"""문서 엔드포인트 테스트."""

from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def test_builtin_docs() -> None:
    """Swagger 문서 엔드포인트 응답 확인."""
    response = client.get("/docs")

    assert response.status_code == 200
    assert "Swagger UI" in response.text


def test_scalar_docs() -> None:
    """Scalar 문서 엔드포인트 응답 확인."""
    response = client.get("/scalar")

    assert response.status_code == 200
    assert "scalar" in response.text.lower()
