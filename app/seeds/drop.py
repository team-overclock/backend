from ..database import SessionLocal
from ..models import User, Recommendation
from ..config import SEED_TASK_ID_PREFIX, SEED_USERNAME_PREFIX


def run():
    db = SessionLocal()
    try:
        db.query(User).filter(User.name.like(f"{SEED_USERNAME_PREFIX}%")).delete()
        db.query(Recommendation).filter(Recommendation.task_id.like(f"{SEED_TASK_ID_PREFIX}%")).delete()
    except Exception as e:
        db.rollback()
        raise e
    else:
        db.commit()
    finally:
        db.close()
