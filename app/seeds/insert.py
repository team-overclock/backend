import random
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from ..core.enums import INFRASTRUCTURE_TYPE_VALUES
from ..redis import redis
from ..database import SessionLocal
from ..demo import create_guest_user
from ..crud.service import get_regions
from ..utils import run_with_progress
from ..models import (
    User,
    SearchLog,
    Recommendation,
    Infrastructure,
    Property,
    PropertyInfrastructure,
)

from ..config import (
    SEED_TASK_ID_PREFIX,
    SEED_USERNAME_PREFIX,
    DEFAULT_INSERT_SEED_RECOMMENDATIONS,
    DEFAULT_INSERT_SEED_USERS,
)


start_ts = int(datetime(2022, 1, 1, 0, 0, 0).timestamp())
end_ts = int(datetime(2026, 12, 31, 23, 59, 59).timestamp())


def random_range(min_value: int, max_value: int):
    results = random.sample(range(min_value, max_value + 1), k=2)
    min, max = sorted(results)
    return min, max


def get_or_create_guest_user(db: Session):
    """게스트 사용자 조회 및 생성"""
    return create_guest_user(db)[0]


def generate_seed_users(
    db: Session,
    suffix: int,
):
    name = f"{SEED_USERNAME_PREFIX}{suffix}"
    user = User(
        name=name,
        email=f"{name}@example.com",
        password="1234",
    )
    db.add(user)
    return user

def generate_seed_recommendations(
    db: Session,
    suffix: int,
    users: list[User],
    regions: list[dict],
    infra_types: list[str],
    infras: list[Infrastructure],
    properties: list[Property],
):
    n = min(5, len(users))
    max_request_users = random.choice([m for m in range(1, n + 1) for _ in range((n ** 2) - (m ** 2) + 1)])
    request_users = random.sample(users, k=max_request_users)

    selected_region = random.choice(regions)
    has_sale_price = random.choice([True, False])
    has_jeonse_price = random.choice([True, False])
    selected_sale_price = random_range(0, 999999999999) if has_sale_price else (None, None)
    selected_jeonse_price = random_range(0, 999999999999) if has_jeonse_price else (None, None)
    created_at, finished_at = random_range(start_ts, end_ts)
    created_at = datetime.fromtimestamp(created_at)
    failed_at = (created_at + timedelta(minutes=random.randint(1, 3))) if random.choice([True] + [False] * 4) else None
    finished_at = datetime.fromtimestamp(finished_at) if not failed_at and random.choice([True, False]) else None
    updated_at = finished_at + timedelta(minutes=random.randint(100, 1000)) if finished_at and random.choice([True, [False] * 4]) else None

    selected_infra_types = random.sample(infra_types, k=random.randint(1, len(infra_types)))
    random.shuffle(selected_infra_types)

    selected_properties = random.sample(properties, k=random.randint(5, 10))
    scores = [random.uniform(0.01, 100.0) for _ in selected_properties]
    selected_properties = sorted(selected_properties, key=lambda x: scores[selected_properties.index(x)], reverse=True)
    top_properties = [
        {
            "id": prop.id,
            "name": prop.name,
            "score": scores[selected_properties.index(prop)],
            "region": prop.region.name,
            "sale_price": sum(random_range(0, 999999999999))/2 if has_sale_price else None,
            "jeonse_price": sum(random_range(0, 999999999999))/2 if has_jeonse_price else None,
        }
        for prop in selected_properties[:5]
    ]

    rec = Recommendation(
        task_id=f"{SEED_TASK_ID_PREFIX}{suffix}",
        infrastructure_priorities=selected_infra_types,
        sale_price_min=selected_sale_price[0],
        sale_price_max=selected_sale_price[1],
        jeonse_price_min=selected_jeonse_price[0],
        jeonse_price_max=selected_jeonse_price[1],
        region=selected_region["name"],
        top_properties=top_properties,
        created_at=created_at,
        finished_at=finished_at,
        updated_at=updated_at,
        failed_at=failed_at,
    )
    db.add(rec)

    is_last_viewed = random.choice([True, False])
    last_viewed_at = rec.created_at + timedelta(minutes=random.randint(1, 1000)) if is_last_viewed else None
    search_logs = [
        SearchLog(
            task_id=rec.task_id,
            user=user,
            recommendation=rec,
            requested_at=rec.created_at,
            last_viewed_at=last_viewed_at,
            name=None if random.choice([True, False]) else f"추천 {'x' * random.randint(1, 10)}",
        )
        for user in request_users
    ]
    db.add_all(search_logs)

    for curr_property in selected_properties:
        for curr_infra in selected_infra_types:
            infra = random.choice(list(filter(lambda x: x.type.value == curr_infra, infras)))
            create_property_infrastructure_score(db, curr_property, infra, random.uniform(0.01, 100.0), random.randint(10, 1000))

    return rec

def create_property_infrastructure_score(
    db: Session,
    property: Property,
    infrastructure: Infrastructure,
    score: float,
    distance: int,
):
    ins = db.query(PropertyInfrastructure).filter(
        PropertyInfrastructure.property_id == property.id,
        PropertyInfrastructure.infrastructure_id == infrastructure.id
    ).first()
    if not ins:
        ins = PropertyInfrastructure(
            property=property,
            property_type=property.type,
            infrastructure=infrastructure,
            infrastructure_type=infrastructure.type.value,
            score=score,
            distance=distance,
        )
        db.add(ins)
    return ins


def _run(
    db: Session,
    num_recommendations: int,
    num_users: int,
    *,
    silent: bool = False,
):
    guest_user = get_or_create_guest_user(db)
    regions = get_regions(redis)
    infra_types = INFRASTRUCTURE_TYPE_VALUES
    infras = db.query(Infrastructure).all()
    properties = db.query(Property).all()

    db_users = db.query(User).filter(User.name.like(f"{SEED_USERNAME_PREFIX}%")).all()
    last_user_suffix = len(db_users)
    last_task_id_suffix = db.query(Recommendation).filter(Recommendation.task_id.like(f"{SEED_TASK_ID_PREFIX}%")).count()

    new_users = run_with_progress(
        range(num_users),
        "시드 사용자 생성 중...",
        lambda idx, _: generate_seed_users(
            db,
            last_user_suffix + idx + 1,
        ),
        silent=silent,
    )

    users = [guest_user] + db_users + new_users
    run_with_progress(
        range(num_recommendations),
        "시드 데이터 삽입 중...",
        lambda idx, _: generate_seed_recommendations(
            db,
            last_task_id_suffix + idx + 1,
            users,
            regions,
            infra_types,
            infras, 
            properties,
        ),
        silent=silent,
    )
    return num_recommendations


def run(
    num_recommendations: int | None = None,
    num_users: int | None = None,
    *,
    silent: bool = False,
):
    num_recs = DEFAULT_INSERT_SEED_RECOMMENDATIONS if num_recommendations is None else num_recommendations
    num_users = DEFAULT_INSERT_SEED_USERS if num_users is None else num_users

    db = SessionLocal()
    try:
        total = _run(db, num_recs, num_users, silent=silent)
    except Exception as e:
        db.rollback()
        raise e
    else:
        db.commit()
    finally:
        db.close()

    return total
