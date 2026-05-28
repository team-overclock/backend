"""사용자(users) 라우터 엔드포인트 테스트."""

from unittest.mock import MagicMock, patch
from app.models import User


def make_mock_user(id=1, email="test@example.com", name="Test User", cuid="cuid123"):
    """테스트용 가짜 User 모델 인스턴스 생성"""
    user = MagicMock(spec=User)
    user.id = id
    user.email = email
    user.name = name
    user.cuid = cuid
    user.verify_password.return_value = True
    return user


def test_users_me_unauthorized(client) -> None:
    """로그인하지 않고 내 정보 조회(/users/me) 시도 시 401 에러 검증."""
    response = client.get("/users/me")
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == "AUTHENTICATION_REQUIRED"


@patch("app.dependencies.get_user_by_cuid")
@patch("app.routers.auth.get_user_by_email")
def test_get_user_info_success(mock_get_user_by_email, mock_get_user_by_cuid, client) -> None:
    """내 정보 조회(/users/me) 성공 테스트."""
    mock_user = make_mock_user()
    mock_get_user_by_email.return_value = mock_user
    mock_get_user_by_cuid.return_value = mock_user

    # 1. 로그인하여 세션 획득
    client.post("/auth/login", json={"email": "test@example.com", "password": "password123"})

    # 2. 조회 요청
    response = client.get("/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"
    assert data["cuid"] == "cuid123"


@patch("app.dependencies.get_user_by_cuid")
@patch("app.routers.auth.get_user_by_email")
def test_update_user_info_success(mock_get_user_by_email, mock_get_user_by_cuid, client, mock_db) -> None:
    """내 정보 수정(PATCH /users/me) 성공 테스트."""
    mock_user = make_mock_user()
    mock_get_user_by_email.return_value = mock_user
    mock_get_user_by_cuid.return_value = mock_user

    # 1. 로그인
    client.post("/auth/login", json={"email": "test@example.com", "password": "password123"})

    # 2. 수정 요청
    response = client.patch(
        "/users/me",
        json={"name": "New Name", "email": "new@example.com"}
    )

    assert response.status_code == 200
    # DB 세션의 commit 및 refresh가 잘 수행되었는지 확인
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(mock_user)

    # 응답 확인 (mock_user의 필드 수정이 이루어졌는지 검증)
    assert mock_user.name == "New Name"
    assert mock_user.email == "new@example.com"


@patch("app.dependencies.get_user_by_cuid")
@patch("app.routers.auth.get_user_by_email")
def test_change_password_success(mock_get_user_by_email, mock_get_user_by_cuid, client, mock_db) -> None:
    """비밀번호 변경(POST /users/me/password) 성공 테스트."""
    mock_user = make_mock_user()
    mock_get_user_by_email.return_value = mock_user
    mock_get_user_by_cuid.return_value = mock_user

    # 1. 로그인
    client.post("/auth/login", json={"email": "test@example.com", "password": "password123"})

    # 2. 비밀번호 변경 요청
    response = client.post(
        "/users/me/password",
        json={"current_password": "password123", "new_password": "newpassword123"}
    )

    assert response.status_code == 204
    assert mock_user.password == "newpassword123"
    mock_db.commit.assert_called_once()


@patch("app.dependencies.get_user_by_cuid")
@patch("app.routers.auth.get_user_by_email")
def test_change_password_invalid_current(mock_get_user_by_email, mock_get_user_by_cuid, client) -> None:
    """현재 비밀번호가 틀려 비밀번호 변경에 실패하는 케이스 테스트."""
    mock_user = make_mock_user()
    # 로그인 시("password123")는 True를 반환하고, 비밀번호 변경 시("wrongpassword")는 False를 반환하도록 세팅
    mock_user.verify_password.side_effect = lambda password: password == "password123"
    mock_get_user_by_email.return_value = mock_user
    mock_get_user_by_cuid.return_value = mock_user

    # 1. 로그인
    client.post("/auth/login", json={"email": "test@example.com", "password": "password123"})

    # 2. 비밀번호 변경 요청 (비밀번호 검증이 실패하므로 400 에러 기대)
    response = client.post(
        "/users/me/password",
        json={"current_password": "wrongpassword", "new_password": "newpassword123"}
    )

    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "INVALID_CREDENTIALS"
    assert "현재 비밀번호가 일치하지 않습니다" in data["message"]



@patch("app.dependencies.get_user_by_cuid")
@patch("app.routers.auth.get_user_by_email")
def test_get_user_recommendations(mock_get_user_by_email, mock_get_user_by_cuid, client) -> None:
    """추천 요청 목록 조회(GET /users/me/recommendations) 테스트."""
    mock_user = make_mock_user()
    mock_get_user_by_email.return_value = mock_user
    mock_get_user_by_cuid.return_value = mock_user

    # 1. 로그인
    client.post("/auth/login", json={"email": "test@example.com", "password": "password123"})

    # 2. 추천 목록 조회
    response = client.get("/users/me/recommendations")
    assert response.status_code == 200
    data = response.json()
    
    # 더미 데이터 응답 포맷 검증
    assert "total" in data
    assert "items" in data
    assert len(data["items"]) == 2
    assert data["items"][0]["status"] == "completed"
    assert data["items"][1]["status"] == "in_progress"
    assert data["items"][0]["request_data"]["region"] == "서울특별시 용산구 도원동"
