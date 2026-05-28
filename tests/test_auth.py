"""인증(auth) 라우터 엔드포인트 테스트."""

from unittest.mock import MagicMock, patch
from app.models import User


def make_mock_user(id=1, email="test@example.com", name="Test User", cuid="cuid123"):
    """테스트를 위해 User 모델을 모킹한 Mock 인스턴스 생성"""
    user = MagicMock(spec=User)
    user.id = id
    user.email = email
    user.name = name
    user.cuid = cuid
    user.verify_password.return_value = True
    return user


def test_login_check_unauthenticated(client) -> None:
    """로그인하지 않은 상태에서 로그인 상태 조회(/auth/check) 테스트."""
    response = client.get("/auth/check")
    assert response.status_code == 200
    data = response.json()
    assert data["is_logged_in"] is False
    assert data["user"] is None


@patch("app.routers.auth.create_user")
def test_signup_success(mock_create_user, client) -> None:
    """회원가입(/auth/signup) 성공 케이스 테스트."""
    mock_user = make_mock_user()
    mock_create_user.return_value = (mock_user, True)

    response = client.post(
        "/auth/signup",
        json={
            "email": "test@example.com",
            "password": "password123",
            "name": "Test User"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"
    assert data["cuid"] == "cuid123"
    mock_create_user.assert_called_once()


@patch("app.routers.auth.create_user")
def test_signup_duplicate_email(mock_create_user, client) -> None:
    """중복 이메일 회원가입 시도 시 409 에러 검증."""
    mock_create_user.return_value = (None, False)

    response = client.post(
        "/auth/signup",
        json={
            "email": "duplicate@example.com",
            "password": "password123",
            "name": "Duplicate"
        }
    )

    assert response.status_code == 409
    data = response.json()
    assert data["code"] == "DUPLICATE_EMAIL"
    assert "이미 등록된 이메일" in data["message"]


@patch("app.routers.auth.get_user_by_email")
def test_login_success(mock_get_user_by_email, client) -> None:
    """로그인(/auth/login) 성공 케이스 테스트."""
    mock_user = make_mock_user()
    mock_get_user_by_email.return_value = mock_user

    response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["cuid"] == "cuid123"
    # 세션 쿠키가 세팅되었는지 확인 (클라이언트 쿠키 저장소 검증)
    assert "session" in client.cookies


@patch("app.routers.auth.get_user_by_email")
def test_login_invalid_credentials(mock_get_user_by_email, client) -> None:
    """올바르지 않은 비밀번호로 로그인 시도 시 401 에러 검증."""
    mock_user = make_mock_user()
    # 비밀번호 매칭 실패 시뮬레이션
    mock_user.verify_password.return_value = False
    mock_get_user_by_email.return_value = mock_user

    response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401
    data = response.json()
    assert data["code"] == "INVALID_CREDENTIALS"
    assert "이메일 또는 비밀번호가 잘못되었습니다." in data["message"]


@patch("app.routers.auth.get_user_by_cuid")
@patch("app.routers.auth.get_user_by_email")
def test_login_and_check_and_logout_flow(mock_get_user_by_email, mock_get_user_by_cuid, client) -> None:
    """로그인 -> 로그인 상태 확인 -> 로그아웃 전체 플로우 테스트."""
    mock_user = make_mock_user()
    mock_get_user_by_email.return_value = mock_user
    mock_get_user_by_cuid.return_value = mock_user

    # 1. 로그인 요청
    login_response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123"
        }
    )
    assert login_response.status_code == 200
    assert "session" in client.cookies

    # 2. 로그인 상태 조회
    check_response = client.get("/auth/check")
    assert check_response.status_code == 200
    check_data = check_response.json()
    assert check_data["is_logged_in"] is True
    assert check_data["user"]["email"] == "test@example.com"

    # 3. 로그아웃 요청
    logout_response = client.post("/auth/logout")
    assert logout_response.status_code == 204

    # 4. 로그아웃 후 상태 재확인
    check_response_after = client.get("/auth/check")
    check_data_after = check_response_after.json()
    assert check_data_after["is_logged_in"] is False
