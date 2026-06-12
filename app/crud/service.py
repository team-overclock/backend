import json
from redis import Redis
from sqlalchemy.orm import Session

from ..models import (
    User,
    Region,
    Recommendation,
    SearchLog,
    Infrastructure,
)
from ..core.enums import InfrastructureTypeEnum, SchoolDistrictTypeEnum


REGIONS_ALL_KEY = "regions:all"
REGIONS_DEPTH_PREFIX = "regions:depth_"
REGIONS_MAX_DEPTH_KEY = "regions:max_depth"

HIGH_SCHOOLS_ALL_KEY = "high_schools:all"


def fetch_hgetall(redis: Redis, hkey: str, sort: bool = True, **extra_dict):
    result = redis.hgetall(hkey)
    override_dict = extra_dict.get("override_dict") or {}
    result = [{ **extra_dict, **json.loads(v), **override_dict } for v in result.values()]
    if sort: result.sort(key=lambda x: x["id"])
    return result


def region_depth_hkeys(redis: Redis):
    max_depth = get_region_max_depth(redis)
    return [f"{REGIONS_DEPTH_PREFIX}{d}" for d in range(max_depth + 1)]

def set_region_max_depth(redis: Redis, depth: int):
    redis.set(REGIONS_MAX_DEPTH_KEY, depth)

def get_region_max_depth(redis: Redis):
    return int(redis.get(REGIONS_MAX_DEPTH_KEY) or 0)


def sync_regions_to_redis(db: Session, redis: Redis):
    """
    변하지 않는 값으로, 서버 올릴 때 redis에 자동으로 올림
    - 조회 시 db가 아닌 redis에서 조회
    """
    regions = db.query(Region).filter(Region.deleted_at.is_(None)).all()
    caches = {}
    depths = set([-1])
    for r in regions:
        depths.add(r.depth)
        hkey = f"{REGIONS_DEPTH_PREFIX}{r.depth}"
        value = {"id": r.id, "name": r.name}
        caches.setdefault(hkey, {}).update({r.id: json.dumps(value, ensure_ascii=False)})

    with redis.pipeline(transaction=True) as pipe:
        pipe.delete(REGIONS_ALL_KEY)
        for i in range(5):
            pipe.delete(f"{REGIONS_DEPTH_PREFIX}{i}")

        for hkey in caches:
            value = caches[hkey]
            pipe.hset(REGIONS_ALL_KEY, mapping=value)
            pipe.hset(hkey, mapping=value)

        max_depth = max(depths)
        pipe.set(REGIONS_MAX_DEPTH_KEY, max_depth)

        pipe.execute()

    return len(regions)

def get_regions(redis: Redis, include_depth: bool = True) -> list[dict]:
    """모든 동네 목록을 반환하는 함수"""
    if not include_depth:
        return fetch_hgetall(redis, REGIONS_ALL_KEY)
    else:
        items = []
        hkeys = region_depth_hkeys(redis)
        for hkey in hkeys:
            depth = int(hkey[len(REGIONS_DEPTH_PREFIX):])
            result = fetch_hgetall(redis, hkey, sort=False, depth=depth)
            items.extend(result)
        items.sort(key=lambda x: x["id"])
        return items

def get_region_by_id(redis: Redis, region_id: int) -> dict | None:
    """주어진 id에 해당하는 동네를 반환하는 함수"""
    value = redis.hget(REGIONS_ALL_KEY, region_id)
    if value is None:
        return None
    return json.loads(value)

def get_regions_by_depth(redis: Redis, depth: int):
    """주어진 depth에 해당하는 동네 목록을 반환하는 함수"""
    hkey = f"{REGIONS_DEPTH_PREFIX}{depth}"
    result = fetch_hgetall(redis, hkey)
    return result

def get_region_by_name(redis: Redis, name: str):
    """주어진 이름에 해당하는 동네 목록을 반환하는 함수"""
    regions = get_regions(redis, include_depth=False)
    for region in regions:
        if region["name"] == name:
            return region
    return None

def get_region_by_source_id(db: Session, source_id: int):
    """주어진 source_id와 depth에 해당하는 동네 목록을 반환하는 함수"""
    return db.query(Region).filter(Region.source_id == source_id, Region.deleted_at.is_(None)).first()


def sync_high_schools_to_redis(db: Session, redis: Redis):
    """
    고등학교 목록을 DB에서 가져와 Redis에 싱크합니다.
    """
    schools = db.query(Infrastructure).filter(
        Infrastructure.type == InfrastructureTypeEnum.HIGH_SCHOOL,
        Infrastructure.deleted_at.is_(None)
    ).all()

    mapping = {}
    for s in schools:
        value = {
            "id": s.id,
            "name": s.name,
            "latitude": float(s.latitude) if s.latitude is not None else 0.0,
            "longitude": float(s.longitude) if s.longitude is not None else 0.0,
        }
        mapping[s.id] = json.dumps(value, ensure_ascii=False)

    redis.delete(HIGH_SCHOOLS_ALL_KEY)
    redis.hset(HIGH_SCHOOLS_ALL_KEY, mapping=mapping)
    return len(mapping)

def get_high_schools(redis: Redis, sort: bool = True):
    """고등학교 인프라 목록을 Redis에서 조회하여 반환하는 함수"""
    return fetch_hgetall(redis, HIGH_SCHOOLS_ALL_KEY, sort=sort)

def get_high_school_map(redis: Redis, sort: bool = True):
    """고등학교 인프라 목록을 Redis에서 조회하여 반환하는 함수"""
    result = get_high_schools(redis, sort=sort)
    school_map = {s["id"]: s for s in result}
    return school_map


def create_recommendation(
    db: Session,
    task_id: str,
    region_name: str,
    infrastructure_types: list[str] | None,
    school_district_types: list[SchoolDistrictTypeEnum] | None,
    high_school_ids: list[int] | None,
    sale_price_min: int | None,
    sale_price_max: int | None,
    jeonse_price_min: int | None,
    jeonse_price_max: int | None,
    *,
    request_user: User | None = None,
    name: str | None = None,
    **kwargs,
):
    """
    추천 생성 함수. 커밋은 하지 않음.
    """

    rec = Recommendation(
        task_id=task_id,
        region=region_name,
        school_district_types=school_district_types,
        high_school_ids=high_school_ids,
        sale_price_min=sale_price_min,
        sale_price_max=sale_price_max,
        jeonse_price_min=jeonse_price_min,
        jeonse_price_max=jeonse_price_max,
    )

    if request_user: rec.add_user(request_user, name)
    if infrastructure_types: rec.set_infrastructure_priorities(infrastructure_types)
    db.add(rec)
    return rec

def get_recommendation_by_task_id(db: Session, recommendation_task_id: str):
    """주어진 task_id에 해당하는 추천을 반환하는 함수"""
    return db.query(Recommendation).filter(Recommendation.task_id == recommendation_task_id).first()

def get_recommendations_by_user_id_and_task_id(db: Session, user_id: int, task_id: str, size: int = 2) -> list[Recommendation]:
    """해당 유저가 요청한 추천 중 주어진 task_id로 시작하는 추천 목록을 반환하는 함수. 최대 `size` 개수만큼 반환"""
    return db.query(Recommendation).join(
        SearchLog,
        SearchLog.recommendation_id == Recommendation.id,
    ).filter(
        SearchLog.user_id == user_id,
        Recommendation.task_id.startswith(task_id),
    ).limit(size).all()

def get_search_log_by_user_id_and_task_id(db: Session, user_id: int, task_id: str, size: int = 2) -> list[SearchLog]:
    """주어진 task_id로 시작하는 검색 로그 목록을 반환하는 함수. 최대 `size` 개수만큼 반환"""
    return db.query(SearchLog).filter(
        SearchLog.user_id == user_id,
        SearchLog.task_id.startswith(task_id),
    ).limit(size).all()

def get_search_log_by_user_id(db: Session, user_id: int) -> list[SearchLog]:
    """주어진 user_id가 요청한 추천 목록을 반환하는 함수"""
    return db.query(SearchLog).join(
        Recommendation,
        SearchLog.recommendation_id == Recommendation.id,
    ).filter(
        SearchLog.user_id == user_id,
    ).order_by(
        SearchLog.requested_at.desc()
    ).all()
