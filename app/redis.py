import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
from redis import Redis

load_dotenv()


redis_host = os.getenv("REDIS_HOST") or "127.0.0.1"
redis_port = os.getenv("REDIS_PORT") or "6379"
redis_user = os.getenv("REDIS_USER")
redis_pass = os.getenv("REDIS_PASS")
redis_db = os.getenv("REDIS_DB") or "0"

redis = Redis(
    host=redis_host,
    port=redis_port,
    username=quote_plus(redis_user) if redis_user else None,
    password=quote_plus(redis_pass) if redis_pass else None,
    db=redis_db,
    encoding="utf-8",
    decode_responses=True,
)

def get_redis():
    yield redis
