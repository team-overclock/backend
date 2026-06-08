import json
import hashlib
from enum import Enum
from datetime import datetime
from collections import defaultdict
from fastapi import BackgroundTasks
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import User, Recommendation, Property, Infrastructure, PropertyInfrastructure, Region
from ..core.enums import SchoolDistrictTypeEnum, InfrastructureTypeEnum
from ..crud.service import get_recommendation_by_task_id, create_recommendation


def generate_recommendation_task_id(
    region_id: int | None,
    infrastructure_types: list[InfrastructureTypeEnum],
    high_school_ids: list[int] | None,
    school_district_types: list[SchoolDistrictTypeEnum],
    sale_price_min: int | None,
    sale_price_max: int | None,
    jeonse_price_min: int | None,
    jeonse_price_max: int | None,
    **kwargs,
):
    """
    사용자에게 입력받은 동네, 인프라 유형 및 우선순위, 매매/전세 가격 범위를 기반으로 고유한 hash(task_id) 생성
    """
    def _serialize_val(val):
        if isinstance(val, Enum):
            return val.value
        if isinstance(val, list):
            return [_serialize_val(item) for item in val]
        return val

    # None이 아닌 값들만 순서대로 수집
    params = {
        "region_id": region_id,
        "infrastructure_types": infrastructure_types,
        "high_school_ids": high_school_ids,
        "school_district_types": school_district_types,
        "sale_price_min": sale_price_min,
        "sale_price_max": sale_price_max,
        "jeonse_price_min": jeonse_price_min,
        "jeonse_price_max": jeonse_price_max,
    }

    values = {name: _serialize_val(val) for name, val in params.items() if val is not None}

    # 입력된 순서를 유지하면서 JSON 직렬화 후 SHA256 hash 생성
    hash_input = json.dumps(values, ensure_ascii=False, sort_keys=False)
    task_id = hashlib.sha256(hash_input.encode()).hexdigest()
    return task_id


def _main(
    db: Session,
    *,
    recommendation: Recommendation,
) -> None:
    # 사용자가 선택한 인프라 유형 순서, 순서대로 가중치 적용 (1개 이상 7개 이하)
    infra_types: list[str] = recommendation.infrastructure_priorities

    # infra_types 내 학교 유형이 있을 때만 school_district_types가 의미 있음
    # depth=1 region의 academy_count 기준: 상위 15% → INTENSIVE, 15~50% → BALANCED, 나머지 → RELAXED
    school_district_types: list[str] = recommendation.school_district_types or []

    # infra_types 내 HIGH_SCHOOL 유형이 있을 때만 high_school_ids가 의미 있음
    high_school_ids: list[int] = recommendation.high_school_ids or []

    school_infra_type_values = {
        InfrastructureTypeEnum.ELEMENTARY_SCHOOL.value,
        InfrastructureTypeEnum.MIDDLE_SCHOOL.value,
        InfrastructureTypeEnum.HIGH_SCHOOL.value,
    }
    has_school_infra = any(t in school_infra_type_values for t in infra_types)

    # Step 1: 학군 조건에 맞는 depth=1 region ID 계산
    # select() 명시적 컬럼 지정으로 Region에 POINT 컬럼이 없더라도 불필요한 컬럼 로딩 방지
    qualifying_school_region_ids = None
    if school_district_types and has_school_infra:
        region_rows = db.execute(
            select(Region.id, Region.academy_count)
            .where(Region.depth == 1, Region.deleted_at.is_(None))
            .order_by(Region.academy_count.desc())
        ).fetchall()
        total = len(region_rows)
        qualifying_school_region_ids = set()
        if total > 0:
            intensive_end = max(1, round(total * 0.15))
            balanced_end = max(intensive_end, round(total * 0.50))
            for i, row in enumerate(region_rows):
                if i < intensive_end:
                    region_type = SchoolDistrictTypeEnum.INTENSIVE.value
                elif i < balanced_end:
                    region_type = SchoolDistrictTypeEnum.BALANCED.value
                else:
                    region_type = SchoolDistrictTypeEnum.RELAXED.value
                if region_type in school_district_types:
                    qualifying_school_region_ids.add(row.id)

    # Step 2: 학군 조건에 맞는 property ID 조회 (Property.point 컬럼 제외)
    qualifying_property_ids = None
    if qualifying_school_region_ids is not None:
        if not qualifying_school_region_ids:
            recommendation.top_properties = []
            return
        qualifying_property_ids = {
            row.id for row in db.execute(
                select(Property.id)
                .join(Region, Property.region_id == Region.id)
                .where(
                    Region.parent_id.in_(qualifying_school_region_ids),
                    Property.deleted_at.is_(None),
                    # Region.deleted_at.is_(None),
                )
            ).fetchall()
        }
        if not qualifying_property_ids:
            recommendation.top_properties = []
            return

    # Step 3: (property, infra_type)별 최고 점수 행 1개씩 추출
    # ROW_NUMBER()로 각 파티션 내 score DESC, infrastructure_id ASC(동점 결정) 순으로 1위 선택
    # select() 명시적 지정으로 Property.point, Infrastructure.point 바이너리 로딩 방지
    rn_col = func.row_number().over(
        partition_by=[PropertyInfrastructure.property_id, PropertyInfrastructure.infrastructure_type],
        order_by=[PropertyInfrastructure.score.desc(), PropertyInfrastructure.infrastructure_id.asc()],
    ).label("rn")

    inner_stmt = (
        select(
            PropertyInfrastructure.property_id,
            PropertyInfrastructure.infrastructure_type,
            PropertyInfrastructure.score,
            Infrastructure.name.label("infra_name"),
            rn_col,
        )
        .join(Infrastructure, PropertyInfrastructure.infrastructure_id == Infrastructure.id)
        .join(Property, PropertyInfrastructure.property_id == Property.id)
        .where(
            Infrastructure.deleted_at.is_(None),
            Property.deleted_at.is_(None),
        )
    )

    # high_school_ids 필터는 사용자가 HIGH_SCHOOL을 직접 선택한 경우에만 적용
    if high_school_ids and InfrastructureTypeEnum.HIGH_SCHOOL.value in infra_types:
        inner_stmt = inner_stmt.where(
            or_(
                PropertyInfrastructure.infrastructure_type != InfrastructureTypeEnum.HIGH_SCHOOL.value,
                PropertyInfrastructure.infrastructure_id.in_(high_school_ids),
            )
        )

    if qualifying_property_ids is not None:
        inner_stmt = inner_stmt.where(
            PropertyInfrastructure.property_id.in_(qualifying_property_ids)
        )

    ranked_subq = inner_stmt.subquery("ranked_infra")

    best_rows = db.execute(
        select(
            ranked_subq.c.property_id,
            ranked_subq.c.infrastructure_type,
            ranked_subq.c.score,
            ranked_subq.c.infra_name,
        )
        .where(ranked_subq.c.rn == 1)
    ).fetchall()

    # Step 4: 인프라 유형별 가중치 적용 (지수 기반: 1위=100, 2위=50, 3위=25, ...)
    # 선택하지 않은 인프라는 N+1번째 가중치(= 100 * 0.5^N)로 동일하게 적용
    n = len(infra_types)
    weight_map: dict[str, float] = {
        infra_type: 100.0 * (0.5 ** i)
        for i, infra_type in enumerate(infra_types)
    }
    unselected_weight = 100.0 * (0.5 ** n)
    for t in InfrastructureTypeEnum:
        if t.value not in weight_map:
            weight_map[t.value] = unselected_weight

    property_infra_scores: dict[int, list[dict]] = defaultdict(list)
    property_total_scores: dict[int, float] = defaultdict(float)
    for row in best_rows:
        infra_type_str = getattr(row.infrastructure_type, "value", row.infrastructure_type)
        raw_score = float(row.score)
        property_infra_scores[row.property_id].append({
            "type": infra_type_str,
            "name": row.infra_name,
            "score": raw_score,
        })
        property_total_scores[row.property_id] += raw_score * weight_map.get(infra_type_str, 0)

    # Step 5: 후보 property 목록 결정 (전체, 점수 내림차순)
    # 가격 필터가 있으면 최대 _MAX_CANDIDATES개 순회, 없으면 상위 10개만 처리
    _MAX_CANDIDATES = 50
    has_sale_filter = recommendation.sale_price_min is not None or recommendation.sale_price_max is not None
    has_jeonse_filter = recommendation.jeonse_price_min is not None or recommendation.jeonse_price_max is not None
    has_price_filter = has_sale_filter or has_jeonse_filter

    all_candidate_pids = sorted(
        property_total_scores, key=property_total_scores.__getitem__, reverse=True
    )
    candidates = all_candidate_pids[:_MAX_CANDIDATES if has_price_filter else 10]

    if not candidates:
        recommendation.top_properties = []
        return

    # Step 6: 후보 property 상세 정보 일괄 조회
    # ST_X/ST_Y로 좌표 추출 → Naver 검색 정확도 향상 (POINT 바이너리 전체 로딩 방지)
    property_detail_map = {
        row.id: row for row in db.execute(
            select(
                Property.id,
                Property.source_id,
                Property.name,
                func.ST_Y(Property.point).label("latitude"),
                func.ST_X(Property.point).label("longitude"),
                Region.name.label("region_name"),
            )
            .join(Region, Property.region_id == Region.id)
            .where(Property.id.in_(candidates), Property.deleted_at.is_(None))
        ).fetchall()
    }

    # Step 7: 후보를 점수 순으로 순회 → 가격 크롤링(Redis→Naver) → 조건 확인 → 최대 10개 선정
    final_properties = []
    for pid in candidates:
        if len(final_properties) >= 10:
            break
        detail = property_detail_map.get(pid)
        if not detail or not detail.name:
            continue

        # 추후 크롤링으로 가격 데이터 및 네이버 URL 가져오기
        # 그 후 가격 조건에 안 맞으면 final_properties에 추가하지 않고 continue
        # continue 하더라도 데이터는 db or redis에 저장
        p = {}
        final_properties.append({
            "id": pid,
            "name": detail.name,
            "score": property_total_scores[pid],
            "region": detail.region_name,
            "sale_price_min": p.get("sale_price_min"),
            "sale_price_max": p.get("sale_price_max"),
            "jeonse_price_min": p.get("jeonse_price_min"),
            "jeonse_price_max": p.get("jeonse_price_max"),
            "naver_url": p.get("naver_url"),
            "infrastructure_scores": sorted(
                property_infra_scores[pid],
                key=lambda x: x["score"],
                reverse=True,
            ),
        })

    recommendation.top_properties = final_properties


def _bg_run(
    task_id: str,
    *,
    db: Session | None = None,
):
    # 백그라운드 작업을 위한 독립적인 DB 세션 생성
    # 스크립트로 실행 시 외부에서 전달된 세션 사용
    conn = db or SessionLocal()

    try:
        rec = get_recommendation_by_task_id(conn, task_id)
        _main(conn, recommendation=rec)
    except Exception as e:
        # 추천 생성 중 오류가 발생한 경우에는 롤백 및 실패 처리
        conn.rollback()
        if rec:
            rec.failed_at = datetime.now()
        conn.commit()
        raise e
    else:
        # 추천 생성이 성공적으로 완료된 경우 시간 기록 후 커밋
        now = datetime.now()
        if not rec.finished_at:
            rec.finished_at = now
        rec.updated_at = now
        rec.failed_at = None
        conn.commit()
    finally:
        # DB 세션 닫기
        if not db: conn.close()



def generate_recommendation(
    db: Session,
    background_tasks: BackgroundTasks | None,
    *,
    request_user: User,
    rec_name: str | None = None,
    region: dict | None = None,
    infrastructure_types: list[InfrastructureTypeEnum] = [],
    school_district_types: list[SchoolDistrictTypeEnum] = [],
    high_school_ids: list[int] = [],
    sale_price_min: float | None = None,
    sale_price_max: float | None = None,
    jeonse_price_min: float | None = None,
    jeonse_price_max: float | None = None,
    task_id: str | None = None,
):
    """
    추천 생성 로직
    - 처리 중 에러 발생 시 저장된 값을 쉽게 무효화(rollback)하기 위해 except, else를 통해서만 commit을 진행함
    """

    region_id = region["id"] if region else None
    region_name = region["name"] if region else None

    request_data = {
        "region": region_name,
        "region_id": region_id,
        "infrastructure_types": infrastructure_types,
        "school_district_types": school_district_types,
        "high_school_ids": high_school_ids,
        "sale_price_min": sale_price_min,
        "sale_price_max": sale_price_max,
        "jeonse_price_min": jeonse_price_min,
        "jeonse_price_max": jeonse_price_max,
    }

    # 입력받은 조건들을 기반으로 task_id 생성
    task_id = task_id or generate_recommendation_task_id(
        **request_data,
    )

    failed = False
    recommendation = get_recommendation_by_task_id(db, task_id)
    if recommendation:
        if recommendation.failed_at:
            # 이전에 실패했다면 다시 로직 실행
            failed = True
            recommendation.failed_at = None

    if not recommendation or failed:
        if not recommendation:
            recommendation = create_recommendation(
                db,
                task_id=task_id,
                **request_data,
            )
    recommendation.add_user(request_user, rec_name)
    db.commit()

    # 테스트용, 테스트 끝나면 들여쓰기 1번 추가
    if background_tasks:
        # 백그라운드에서 비동기로 추천 생성 실행
        background_tasks.add_task(
            _bg_run,
            task_id=task_id,
        )
    else:
        # 스크립트로 실행 시 동기적으로 추천 생성 실행
        _bg_run(task_id, db=db)

    return task_id, recommendation
