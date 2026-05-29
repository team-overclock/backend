"""환경 모드 테스트."""

from unittest.mock import patch
from fastapi.testclient import TestClient


def test_dev_only_routes_blocked_in_production(client) -> None:
    """운영 환경(PROD=True)에서 개발 전용 엔드포인트 접근이 올바르지 허용 및 차단되는지 검증."""
    with patch("app.main.PROD", True):
        from app.main import create_app
        test_app = create_app()
        client = TestClient(test_app)


        # 1. 접근 허용 (200 OK)

        response_redoc = client.get("/redoc")
        assert response_redoc.status_code == 200


        # 2. 접근 차단 (404 Not Found)

        response_docs = client.get("/docs")
        assert response_docs.status_code == 404

        response_scalar = client.get("/scalar")
        assert response_scalar.status_code == 404

        response_manage = client.get("/manage/seeds")
        assert response_manage.status_code == 404

        response_guest = client.get("/auth/guest")
        assert response_guest.status_code == 404


def test_dev_only_routes_allowed_in_development() -> None:
    """개발 환경(PROD=False)에서 개발 전용 엔드포인트 접근이 허용되는지 검증."""
    with patch("app.main.PROD", False):
        from app.main import create_app
        test_app = create_app()
        client = TestClient(test_app)


        # 1. 접근 허용 (200 OK)

        response_docs = client.get("/docs")
        assert response_docs.status_code == 200

        response_scalar = client.get("/scalar")
        assert response_scalar.status_code == 200


        # 2. 접근 허용

        # 존재하지 않는 메소드 요청으로 405 Method Not Allowed 반환하여 라우터 마운트 상태 확인
        response_manage = client.get("/manage/seeds")
        assert response_manage.status_code == 405
