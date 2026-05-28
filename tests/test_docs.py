"""문서 엔드포인트 테스트."""


def test_builtin_docs(client) -> None:
    """Swagger 문서 엔드포인트 응답 확인."""
    response = client.get("/docs")

    assert response.status_code == 200
    assert "Swagger UI" in response.text


def test_scalar_docs(client) -> None:
    """Scalar 문서 엔드포인트 응답 확인."""
    response = client.get("/scalar")

    assert response.status_code == 200
    assert "scalar" in response.text.lower()
