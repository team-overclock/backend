"""헬스 체크 엔드포인트 테스트."""

from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def test_health_root() -> None:
    """루트 엔드포인트가 200과 기대 JSON을 반환하는지 확인."""
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}
