"""샘플 라우트 엔드포인트 테스트."""

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_sample_route() -> None:
    """샘플 라우트가 200과 기대 JSON을 반환하는지 확인."""
    response = client.get("/prefix/path")

    assert response.status_code == 200
    assert response.json() == {"Hello": "Router"}
