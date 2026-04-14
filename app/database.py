from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수를 읽어옵니다.
load_dotenv()

# DB 연결 정보 (보안을 위해 .env에서 가져오는 게 정석입니다)
# .env에 정보가 없다면 일단 아래처럼 직접 적어서 테스트해 볼 수 있습니다.
DB_URL = os.getenv("DATABASE_URL", "mysql+pymysql://ID:PASSWORD@HOST:PORT/DB_NAME")

# 1. DB 엔진 생성
engine = create_engine(DB_URL)

# 2. 세션 생성 도구 (실제 DB 작업을 할 때 사용)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. 모델들이 상속받을 기본 클래스 (models/user.py에서 가져다 쓰는 그 Base입니다!)
Base = declarative_base()

# DB 세션을 가져오는 함수 (회원가입/로그인 로직에서 사용)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()