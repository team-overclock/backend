from redis import Redis
from sqlalchemy.orm import Session

from ...redis import redis
from ...database import SessionLocal
from ...crud.service import sync_regions_to_redis, sync_high_schools_to_redis


def _run(db: Session, redis: Redis):
    sync_regions_to_redis(db, redis)
    sync_high_schools_to_redis(db, redis)


def run(*, silent: bool = False):
    """
    데이터베이스의 지역 및 고등학교 데이터를 Redis에 동기화합니다.
    """
    
    P = not silent

    db = SessionLocal()
    try:
        _run(db, redis)
    except Exception as e:
        if P:
            print()
            print(f"데이터를 Redis에 동기화하는 중 오류가 발생했습니다. ({e})")
        raise e
    else:
        if P: print("데이터를 Redis에 성공적으로 동기화했습니다. 커밋을 진행합니다.")
    finally:
        db.close()
