from app.database import engine
from app.models import Base


def run():
    try:
        Base.metadata.drop_all(bind=engine)
    except Exception as e:
        raise e
