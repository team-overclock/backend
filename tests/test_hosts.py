"""호스트 및 프록시 허용 검증 테스트."""

from unittest.mock import patch
from fastapi.testclient import TestClient


def test_allowed_hosts_in_production() -> None:
    """운영 환경에서 ALLOWED_HOSTS 정책이 올바르게 적용되는지 검증."""
    # PROD = True 이고 ALLOWED_HOSTS = ["allowed.com"] 일 때를 시뮬레이션
    with patch("app.main.PROD", True), \
         patch("app.main.ALLOWED_HOSTS", ["allowed.com"]):
        
        from app.main import create_app
        test_app = create_app()
        client = TestClient(test_app)

        # 1. 허용된 호스트로 요청
        response = client.get("/", headers={"Host": "allowed.com"})
        assert response.status_code == 200

        # 2. 허용되지 않은 호스트로 요청 (TrustedHostMiddleware에 의해 400 Bad Request)
        response_invalid = client.get("/", headers={"Host": "malicious.com"})
        assert response_invalid.status_code == 400
        assert "Invalid host header" in response_invalid.text
