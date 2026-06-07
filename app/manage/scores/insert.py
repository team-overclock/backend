from sqlalchemy import case
from sqlalchemy.orm import Session
from geoalchemy2.functions import ST_Distance_Sphere

from ...database import SessionLocal
from ...models import (
    Property,
    Infrastructure,
    PropertyInfrastructure,
)


RADIUS_METERS = 700.0  # 인프라와의 최대 거리 (m) - 이 범위 내에서 점수 계산, 700m 이상은 0점


def _run(db: Session, *, silent: bool = False):
    P = not silent

    # 1. 원본 공간 거리 연산식 정의 (소수점 유지)
    distance_expr = ST_Distance_Sphere(Property.point, Infrastructure.point)

    # 2. 0m = 100점, 700m = 0점 기준의 소수점 유지 스코어링 수식
    score_expr = case(
        (distance_expr >= RADIUS_METERS, 0.0),
        else_=(100.0 - (distance_expr / RADIUS_METERS * 100.0))
    )

    # 3. 대량의 데이터를 효율적으로 조회하기 위한 크로스 조인(Cros Join) 및 공간 필터링 쿼리
    # 레코드 수가 많을 경우를 대비해 필요한 컬럼 및 연산값만 정확히 스냅샷으로 뜹니다.
    if P: print("DB에서 Property-Infrastructure 매핑 데이터를 조회 및 점수 계산 중...")
    mapping_records = db.query(
        Property.id.label("property_id"),
        Infrastructure.id.label("infrastructure_id"),
        Property.type.label("property_type"),
        Infrastructure.type.label("infrastructure_type"),
        score_expr.label("score"),
        distance_expr.label("distance"),
    ).join(
        Infrastructure,
        distance_expr <= RADIUS_METERS
    ).all()

    # 4. 조회된 매핑 데이터를 PropertyInfrastructure 모델에 맞는 딕셔너리 형태로 가공
    if P: print("DB에 삽입할 매핑 데이터를 가공 중...")
    bulk_insert_data = [
        row._asdict()
        for row in mapping_records
    ]

    # 5. SQLAlchemy Bulk Insert를 이용해 매핑 테이블에 초고속 주입
    if P: print("계산된 매핑 데이터를 DB에 삽입 중...")
    if bulk_insert_data:
        # bulk_insert_mappings를 사용하면 인스턴스를 일일이 생성하지 않아 메모리 및 속도가 수백 배 빠릅니다.
        db.bulk_insert_mappings(PropertyInfrastructure, bulk_insert_data)

    return len(bulk_insert_data)



def run(*, silent: bool = False):
    """
    DB에 삽입된 Property와 Infrastructure 데이터를 기반으로 
    RADIUS_METERS 미터 이내의 모든 연관 관계(거리, 도보시간, 원천점수)를 계산하여 
    다대다 중간 매핑 테이블에 삽입합니다.
    """

    P = not silent
    db = SessionLocal()
    try:
        _run(db, silent=silent)
    except Exception as e:
        if P:
            print()
            print(f"데이터 삽입 중 오류가 발생했습니다. 롤백을 진행합니다. ({e})")
        db.rollback()
        raise e
    else:
        if P: print("데이터 삽입이 성공적으로 완료되었습니다. 커밋을 진행합니다.")
        db.commit()
    finally:
        db.close()
