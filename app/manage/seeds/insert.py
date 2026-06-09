import random
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from ...core.enums import InfrastructureTypeEnum, SchoolDistrictTypeEnum
from ...redis import redis
from ...database import SessionLocal
from ...demo import create_guest_user
from ...crud.service import get_regions, get_high_schools
from ...utils import run_with_progress
from ...models import (
    User,
    Recommendation,
    SearchLog,
)

from ...config import (
    SEED_TASK_ID_PREFIX,
    SEED_USERNAME_PREFIX,
    DEFAULT_INSERT_SEED_RECOMMENDATIONS,
    DEFAULT_INSERT_SEED_USERS,
)
from ...services.recommendation import generate_recommendation


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
    school_district_types: list[str],
    high_school_ids: list[int],
):
    n = min(5, len(users))
    max_request_users = random.choice([m for m in range(1, n + 1) for _ in range((n ** 2) - (m ** 2) + 1)])
    request_users = random.sample(users, k=max_request_users)

    task_id = f"{SEED_TASK_ID_PREFIX}{suffix}"
    has_sale_price = random.choice([True, False])
    has_jeonse_price = random.choice([True, False])
    selected_region = random.choice(regions)
    selected_infra_types = random.sample(infra_types, k=random.randint(1, len(infra_types)))
    selected_sale_price = random_range(0, 999999999999) if has_sale_price else (None, None)
    selected_jeonse_price = random_range(0, 999999999999) if has_jeonse_price else (None, None)
    selected_school_district_types = random.sample(school_district_types, k=random.randint(0, len(school_district_types)))
    selected_high_school_ids = random.sample(high_school_ids, k=random.randint(0, min(10, len(high_school_ids))))

    random.shuffle(selected_infra_types)

    rec = None
    created_at, finished_at = map(datetime.fromtimestamp, random_range(start_ts, end_ts))
    updated_at = finished_at + timedelta(minutes=random.randint(100, 1000)) if random.choice([True, [False] * 4]) else None

    for user in request_users:
        rec = generate_recommendation(
            db,
            background_tasks=None,
            task_id=task_id,
            request_user=user,
            rec_name=None if random.choice([True, False]) else f"추천 {'x' * random.randint(1, 10)}",
            region=selected_region,
            infrastructure_types=selected_infra_types,
            school_district_types=selected_school_district_types,
            high_school_ids=selected_high_school_ids,
            sale_price_min=selected_sale_price[0],
            sale_price_max=selected_sale_price[1],
            jeonse_price_min=selected_jeonse_price[0],
            jeonse_price_max=selected_jeonse_price[1],
        )
        is_last_viewed = random.choice([True, False])
        last_viewed_at = created_at + timedelta(minutes=random.randint(1, 1000)) if is_last_viewed else None
        search_log = db.query(SearchLog).filter(
            SearchLog.recommendation == rec,
            SearchLog.user == user,
        ).first()
        search_log.last_viewed_at = last_viewed_at

    rec.created_at = created_at
    rec.finished_at = finished_at
    rec.updated_at = updated_at

    db.commit()

    return rec


def _run(
    db: Session,
    num_recommendations: int,
    num_users: int,
    *,
    silent: bool = False,
):
    guest_user = get_or_create_guest_user(db)
    regions = get_regions(redis)
    infra_types = [x.value for x in InfrastructureTypeEnum]
    school_district_types = [x.value for x in SchoolDistrictTypeEnum]

    db_users = db.query(User).filter(User.name.like(f"{SEED_USERNAME_PREFIX}%")).all()
    last_user_suffix = len(db_users)
    last_task_id_suffix = db.query(Recommendation).filter(Recommendation.task_id.like(f"{SEED_TASK_ID_PREFIX}%")).count()
    high_school_ids = [x["id"] for x in get_high_schools(redis)]

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
            school_district_types,
            high_school_ids,
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
