"""테스트 공통 설정 모듈.

프로젝트 루트를 `sys.path`에 추가해 `app` 패키지 import를 안정적으로 보장.
"""

from pathlib import Path
import sys
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ==============================================================================
# 외부 인프라 (Redis, Database) 완벽 모킹 설정
# app 모듈들이 import되기 전에 가짜 모듈/클래스를 준비하여 실제 연결 시도를 완벽 차단합니다.
# ==============================================================================

# 1. 전역 Mock 인스턴스 준비
mock_redis_instance = MagicMock()
mock_redis_instance.hgetall.return_value = {}
mock_redis_instance.hget.return_value = None

mock_engine_instance = MagicMock()
mock_session_instance = MagicMock()

# 2. 패처(Patcher) 실행
redis_patcher = patch("redis.Redis", return_value=mock_redis_instance)
redis_patcher.start()

engine_patcher = patch("sqlalchemy.create_engine", return_value=mock_engine_instance)
engine_patcher.start()

sessionmaker_patcher = patch(
    "sqlalchemy.orm.sessionmaker", 
    return_value=MagicMock(return_value=mock_session_instance)
)
sessionmaker_patcher.start()


import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def mock_db():
    """데이터베이스 세션을 시뮬레이션하기 위한 mock 세션 fixture"""
    db = MagicMock()
    return db

@pytest.fixture
def mock_redis():
    """Redis 클라이언트를 시뮬레이션하기 위한 mock redis fixture"""
    r = MagicMock()
    r.hgetall.return_value = {}
    r.hget.return_value = None
    return r

@pytest.fixture
def client(mock_db, mock_redis):
    """get_db와 get_redis 의존성이 모킹된 FastAPI TestClient fixture"""
    from app.main import app
    from app.database import get_db
    from app.redis import get_redis

    # 의존성 오버라이딩 적용
    def override_get_db():
        try:
            yield mock_db
        finally:
            pass

    def override_get_redis():
        try:
            yield mock_redis
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    with TestClient(app) as test_client:
        yield test_client

    # 테스트가 끝나면 오버라이딩 원복
    app.dependency_overrides.clear()
