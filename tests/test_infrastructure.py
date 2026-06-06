from unittest.mock import MagicMock, patch


@patch("app.dependencies.get_user_by_cuid")
@patch("app.routers.auth.get_user_by_email")
def test_get_high_schools(mock_get_user_by_email, mock_get_user_by_cuid, client, mock_db, mock_redis) -> None:
    """고등학교 목록 조회(/infrastructures/high-schools) API 테스트."""
    # 1. Mock DB 반환 데이터 설정
    import json
    from app.models import User

    mock_user = MagicMock(spec=User)
    mock_user.id = 1
    mock_user.email = "test@example.com"
    mock_user.name = "Test User"
    mock_user.cuid = "cuid123"
    mock_user.verify_password.return_value = True
    mock_get_user_by_email.return_value = mock_user
    mock_get_user_by_cuid.return_value = mock_user

    mock_redis.hgetall.return_value = {
        "1": json.dumps({
            "id": 1,
            "name": "서울고등학교",
            "latitude": 37.5,
            "longitude": 127.0
        }),
        "2": json.dumps({
            "id": 2,
            "name": "대치고등학교",
            "latitude": 37.6,
            "longitude": 127.1
        })
    }

    # 1.5 로그인
    client.post("/auth/login", json={"email": "test@example.com", "password": "password123"})

    # 2. API 호출
    response = client.get("/infrastructures/high-schools")

    # 3. 검증
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    
    assert data["items"][0]["id"] == 1
    assert data["items"][0]["name"] == "서울고등학교"
    assert data["items"][0]["latitude"] == 37.5
    assert data["items"][0]["longitude"] == 127.0

    assert data["items"][1]["id"] == 2
    assert data["items"][1]["name"] == "대치고등학교"
    assert data["items"][1]["latitude"] == 37.6
    assert data["items"][1]["longitude"] == 127.1
