import json
from redis import Redis
from sqlalchemy.orm import Session

from ..models import (
    User,
    Region,
    Recommendation,
    SearchLog,
)


_max_depth = 0
REGIONS_ALL_KEY = "regions:all"
REGIONS_DEPTH_PREFIX = "regions:depth_"

def region_depth_hkeys():
    return [f"{REGIONS_DEPTH_PREFIX}{d}" for d in range(_max_depth + 1)]


def sync_regions_to_redis(db: Session, redis: Redis):
    """
    변하지 않는 값으로, 서버 올릴 때 redis에 자동으로 올림
    - 조회 시 db가 아닌 redis에서 조회
    """
    global _max_depth
    regions = db.query(Region).all()
    caches = {}
    depths = set()
    for r in regions:
        depths.add(r.depth)
        hkey = f"{REGIONS_DEPTH_PREFIX}{r.depth}"
        value = {"id": r.id, "name": r.name}
        caches.setdefault(hkey, {}).update({r.id: json.dumps(value, ensure_ascii=False)})
    _max_depth = max(depths) if len(depths) > 0 else 0

    keys = region_depth_hkeys()
    redis.delete(*keys)
    total = 0
    for hkey in caches:
        value = caches[hkey]
        redis.hset(REGIONS_ALL_KEY, mapping=value)
        total += redis.hset(hkey, mapping=value)
    return total

def fetch_regions(redis: Redis, hkey: str, sort: bool = True, **extra_dict):
    result = redis.hgetall(hkey)
    override_dict = extra_dict.get("override_dict") or {}
    result = [{ **extra_dict, **json.loads(v), **override_dict } for v in result.values()]
    if sort: result.sort(key=lambda x: x["id"])
    return result

def get_regions(redis: Redis, include_depth: bool = True):
    """모든 동네 목록을 반환하는 함수"""
    if not include_depth:
        return fetch_regions(redis, REGIONS_ALL_KEY)
    else:
        items = []
        hkeys = region_depth_hkeys()
        for hkey in hkeys:
            depth = int(hkey[len(REGIONS_DEPTH_PREFIX):])
            result = fetch_regions(redis, hkey, sort=False, depth=depth)
            items.extend(result)
        items.sort(key=lambda x: x["id"])
        return items

def get_region_by_id(redis: Redis, region_id: int):
    """주어진 id에 해당하는 동네를 반환하는 함수"""
    value = redis.hget(REGIONS_ALL_KEY, region_id)
    if value is None:
        return None
    return json.loads(value)

def get_regions_by_depth(redis: Redis, depth: int):
    """주어진 depth에 해당하는 동네 목록을 반환하는 함수"""
    hkey = f"{REGIONS_DEPTH_PREFIX}{depth}"
    result = fetch_regions(redis, hkey)
    return result

def get_region_by_source_id(db: Session, source_id: int):
    """주어진 source_id와 depth에 해당하는 동네 목록을 반환하는 함수"""
    return db.query(Region).filter(Region.source_id == source_id).first()


def create_recommendation(
    db: Session,
    task_id: str,
    region: Region,
    sale_price_min: int | None,
    sale_price_max: int | None,
    jeonse_price_min: int | None,
    jeonse_price_max: int | None,
    *,
    request_user: User | None = None,
    infrastructure_types: list[str] = [],
    name: str | None = None,
):
    """
    추천 생성 함수. 커밋은 하지 않음.
    """

    rec = Recommendation(
        task_id=task_id,
        region=region,
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
    """주어진 task_id로 시작하는 추천 목록을 반환하는 함수. 최대 `size` 개수만큼 반환"""
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
    ).all()
