from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

# .env 파일에서 환경 변수를 읽어옵니다.
load_dotenv()

# DB 연결 정보
# 환경변수 우선순위:
# 1) DATABASE_URL
# 2) DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASS 조합
# 3) 기본값
DB_URL = os.getenv("DATABASE_URL")

if not DB_URL:
    db_host = os.getenv("DB_HOST", "127.0.0.1")
    db_port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_NAME", "overclock")
    db_user = quote_plus(os.getenv("DB_USER", "root"))
    db_pass = quote_plus(os.getenv("DB_PASS", ""))
    DB_URL = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"


# 0. 연결 시 추가 옵션
conn_args = {
    # 별도의 인증서 없이 ssl 연결
    "ssl": {
        "check_hostname": False,
        "verify_mode": False,
    },
}

# 1. DB 엔진 생성
engine = create_engine(DB_URL, pool_pre_ping=True, connect_args=conn_args)

# 2. 세션 생성 도구 (실제 DB 작업을 할 때 사용)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# DB 세션을 가져오는 함수 (회원가입/로그인 로직에서 사용)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
