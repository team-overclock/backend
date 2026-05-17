from datetime import datetime
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import InfrastructureType, Infrastructure, Recommendation
from ..crud.service import get_all_infrastructure_types, get_recommendation_by_hash


def generate_recommendation_task_id(
    region_id: int,
    infrastructure_type_ids: list[int],
    sale_price_min: int | None,
    sale_price_max: int | None,
    deposit_price_min: int | None,
    deposit_price_max: int | None,
):
    """
    사용자에게 입력받은 동네, 인프라 유형 및 우선순위, 매매/전세 가격 범위를 기반으로 고유한 hash(task_id) 생성
    """
    # - 모든 ID는 DB 내 사용되는 PK 값
    # - infra type 순서 정렬하지 말것 -> 배열 내 item 순서대로 높은 가중치를 부여하기 때문
    task_id = "unique_hash_value"
    return task_id


def get_infrastructures_around_property(
    db: Session, property_id: int, infrastructure_type_ids: list[int]
) -> list[tuple[Infrastructure | None, int, int, float]]:
    """
    property 주변의 인프라 정보 조회 및 점수(가중치 미적용) 계산 (각 인프라 유형별 가장 가까운 인프라만)

    구현 가이드:
    1. 각 infrastructure_type_id별로:
        - Infrastructure 테이블에서 해당 타입의 인프라 중
        - 해당 property와 가장 가까운 것 1개만 조회
        - 직접 구현 vs MariaDB 내장 공간 함수 활용(ST_Distance_Sphere/ST_Distance 등)
        - 공간 함수 활용 시 DB 자체 기능을 통해 한 번의 쿼리로 가까운 인프라와 그에 대한 거리, 도보 시간, 점수까지 동시 계산 가능할 것 같음
        - 무조건 1개씩 vs 반경 제한?
    2. len(결과) == len(infrastructure_type_ids) 보장
        - 반경 제한을 둘 경우 None 포함 가능

    반환값:
    - 인프라 또는 None, 거리(m), 도보 시간(분), 점수(0.00~100.00)을 포함하는 튜플의 리스트
    - 예: [(강남역, 150, 2, 5.0), (삼성병원, 500, 6, 3.0), (None, 0, 0, 0.0), ...]

    참고:
    - 기존 계산값이 있다면 다시 계산하지 않고 DB에서 조회하여 반환
    """
    pass


def _generate_recommendation(
    db: Session,
    *,
    recommendation: Recommendation,
    infrastructure_types: list[InfrastructureType],
) -> None:
    """
    추천 데이터 생성 및 DB 저장

    주의사항:
    1. db 메소드 중 commit/flush/refresh/close 금지 (함수 호출부에서 작업이 끝나면 자동으로 rollback/commit 처리함)

    처리 단계:
    1. recommendation.region에 속한 모든 Property 조회 (가격 범위 필터링)
    2. 각 Property마다 주변 인프라 거리/도보시간/점수 계산 및 저장 (PropertyInfrastructureScore 모델)
    3. 인프라 점수에 우선순위 가중치 적용 및 저장 (RecommendationPropertyInfrastructureScore 모델)
    4. 최종 매물 점수 계산 및 저장 (RecommendationPropertyScore 모델)

    참고:
    - infrastructure_types은 사용자 지정 우선순위가 아니라 모든 인프라 유형임
    - db.add/db.add_all은 즉시 커밋되지 않음 (generate_recommendation에서 최종 커밋)
    - 예외 발생 시 generate_recommendation에서 자동 rollback
    - 같은 유형의 가격 min/max 타입은 항상 같음 (min/max 둘 다 숫자거나 둘 다 None이거나)
    - 추가 함수 얼마든지 만들어서 사용 가능
    """
    pass


def generate_recommendation(
    task_id: str,  # generate_recommendation_task_id로 생성한 hash 값
):
    """
    추천 생성 로직
    - 처리 중 에러 발생 시 저장된 값을 쉽게 무효화(rollback)하기 위해 except, else를 통해서만 commit을 진행함
    """

    # 백그라운드 작업을 위한 독립적인 DB 세션 생성
    db = SessionLocal()

    rec = None
    try:
        rec = get_recommendation_by_hash(db, task_id)
        if not rec:
            # 서버 에러, 호출 전 항상 recommendation을 생성하도록 함
            raise ValueError("추천 요청이 존재하지 않습니다.")
        if not rec.infrastructure_type_priorities:
            # 서버 에러, 호출 전 항상 인프라 유형 우선순위를 생성하도록 함
            raise ValueError("추천 요청에 인프라 유형 우선순위가 존재하지 않습니다.")
        
        infra_types = get_all_infrastructure_types(db)
        _generate_recommendation(db, recommendation=rec, infrastructure_types=infra_types)
    except Exception as e:
        # 추천 생성 중 오류가 발생한 경우에는 롤백 및 실패 처리
        db.rollback()
        if rec:
            rec.failed_at = datetime.now()
        db.commit()
        raise e
    else:
        # 추천 생성이 성공적으로 완료된 경우 시간 기록 후 커밋
        now = datetime.now()
        if not rec.finished_at:
            rec.finished_at = now
        rec.updated_at = now
        rec.failed_at = None
        db.commit()
    finally:
        # DB 세션 닫기
        db.close()
