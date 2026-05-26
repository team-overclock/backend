"""추천(recommendations) 라우터 엔드포인트 테스트."""

import pytest
from unittest.mock import MagicMock, patch
from app.models import User, Recommendation, SearchLog

def make_mock_user(id=1, email="test@example.com", name="Test User", cuid="cuid123"):
    """테스트용 가짜 User 모델 인스턴스 생성"""
    user = MagicMock(spec=User)
    user.id = id
    user.email = email
    user.name = name
    user.cuid = cuid
    user.verify_password.return_value = True
    return user


@patch("app.dependencies.get_user_by_cuid")
@patch("app.routers.auth.get_user_by_email")
@patch("app.core.validate.get_region_by_id")
def test_request_generate_recommendation_success(
    mock_get_region_by_id, mock_get_user_by_email, mock_get_user_by_cuid, client
) -> None:
    """추천 생성 요청 성공 테스트."""
    # 1. 모킹 설정
    mock_user = make_mock_user()
    mock_get_user_by_email.return_value = mock_user
    mock_get_user_by_cuid.return_value = mock_user
    
    # 유효한 지역 반환 설정
    mock_get_region_by_id.return_value = {"id": 1, "name": "서울특별시 용산구 도원동"}

    # 2. 로그인
    client.post("/auth/login", json={"email": "test@example.com", "password": "password123"})

    # 3. 추천 생성 요청
    response = client.post(
        "/recommendations",
        json={
            "name": "내 맞춤 추천",
            "region_id": 1,
            "infrastructure_types": ["SUBWAY_STATION", "PARK"],
            "sale_price": {"min": 0, "max": 1000000000},
            "jeonse_price": {"min": 0, "max": 500000000}
        }
    )

    assert response.status_code == 202
    data = response.json()
    assert data["task_id"] == "unique_task_id"
    assert data["status"] == "in_progress"


@patch("app.dependencies.get_user_by_cuid")
@patch("app.routers.auth.get_user_by_email")
@patch("app.core.validate.get_region_by_id")
def test_request_generate_recommendation_invalid_region(
    mock_get_region_by_id, mock_get_user_by_email, mock_get_user_by_cuid, client
) -> None:
    """유효하지 않은 지역 ID로 추천 생성 요청 시 400 에러 검증."""
    mock_user = make_mock_user()
    mock_get_user_by_email.return_value = mock_user
    mock_get_user_by_cuid.return_value = mock_user
    
    # 지역 조회 실패 설정 (유효하지 않은 지역)
    mock_get_region_by_id.return_value = None

    # 1. 로그인
    client.post("/auth/login", json={"email": "test@example.com", "password": "password123"})

    # 2. 추천 생성 요청
    response = client.post(
        "/recommendations",
        json={
            "region_id": 999,
            "infrastructure_types": ["SUBWAY_STATION"]
        }
    )

    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "REGION_ERROR"
    assert "유효하지 않은 동네" in data["message"]


@patch("app.dependencies.get_user_by_cuid")
@patch("app.routers.auth.get_user_by_email")
@patch("app.core.validate.get_region_by_id")
def test_request_generate_recommendation_invalid_infra(
    mock_get_region_by_id, mock_get_user_by_email, mock_get_user_by_cuid, client
) -> None:
    """유효하지 않은 인프라 유형으로 추천 생성 요청 시 400 에러 검증."""
    mock_user = make_mock_user()
    mock_get_user_by_email.return_value = mock_user
    mock_get_user_by_cuid.return_value = mock_user
    mock_get_region_by_id.return_value = {"id": 1, "name": "서울특별시 용산구 도원동"}

    # 1. 로그인
    client.post("/auth/login", json={"email": "test@example.com", "password": "password123"})

    # 2. 추천 생성 요청
    response = client.post(
        "/recommendations",
        json={
            "region_id": 1,
            "infrastructure_types": ["INVALID_INFRA_TYPE"]
        }
    )

    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "INFRASTRUCTURE_TYPE_ERROR"
    assert "유효하지 않은 인프라 유형이 포함" in data["message"]


@patch("app.dependencies.get_user_by_cuid")
@patch("app.routers.auth.get_user_by_email")
@patch("app.dependencies.get_search_log_by_user_id_and_task_id")
def test_change_recommendation_name_success(
    mock_get_search_log, mock_get_user_by_email, mock_get_user_by_cuid, client, mock_db
) -> None:
    """추천 이름 변경(PATCH /recommendations/{task_id}) 성공 테스트."""
    mock_user = make_mock_user()
    mock_get_user_by_email.return_value = mock_user
    mock_get_user_by_cuid.return_value = mock_user
    
    # 1개의 search_log 리턴하도록 설정
    mock_search_log = MagicMock(spec=SearchLog)
    mock_search_log.task_id = "unique_task_id"
    mock_search_log.name = "Old Name"
    mock_get_search_log.return_value = [mock_search_log]

    # 1. 로그인
    client.post("/auth/login", json={"email": "test@example.com", "password": "password123"})

    # 2. 이름 변경 요청
    response = client.patch(
        "/recommendations/unique_task_id",
        json={"name": "New Recommendation Name"}
    )

    assert response.status_code == 204
    assert mock_search_log.name == "New Recommendation Name"
    mock_db.commit.assert_called_once()


@patch("app.dependencies.get_user_by_cuid")
@patch("app.routers.auth.get_user_by_email")
@patch("app.dependencies.get_recommendations_by_user_id_and_task_id")
def test_get_recommendation_summary_success(
    mock_get_recommendations, mock_get_user_by_email, mock_get_user_by_cuid, client
) -> None:
    """추천 결과 요약 조회(GET /recommendations/{task_id}) 성공 테스트."""
    mock_user = make_mock_user()
    mock_get_user_by_email.return_value = mock_user
    mock_get_user_by_cuid.return_value = mock_user

    # 1개의 추천 결과 리턴하도록 설정
    mock_rec = MagicMock(spec=Recommendation)
    mock_rec.task_id = "unique_task_id"
    mock_get_recommendations.return_value = [mock_rec]

    # 1. 로그인
    client.post("/auth/login", json={"email": "test@example.com", "password": "password123"})

    # 2. 요약 조회 요청
    response = client.get("/recommendations/unique_task_id")
    assert response.status_code == 200
    data = response.json()
    
    # 하드코딩 리턴 구조 검증
    assert data["task_id"] == "full_task_id"
    assert data["status"] == "completed"
    assert len(data["properties"]) == 2
    assert data["properties"][0]["name"] == "삼성래미안"


@patch("app.dependencies.get_user_by_cuid")
@patch("app.routers.auth.get_user_by_email")
@patch("app.dependencies.get_recommendations_by_user_id_and_task_id")
def test_get_recommendation_property_detail_success(
    mock_get_recommendations, mock_get_user_by_email, mock_get_user_by_cuid, client
) -> None:
    """추천 매물 상세 조회(GET /recommendations/{task_id}/properties/{property_id}) 성공 테스트."""
    mock_user = make_mock_user()
    mock_get_user_by_email.return_value = mock_user
    mock_get_user_by_cuid.return_value = mock_user

    # 1개의 추천 결과 리턴하도록 설정
    mock_rec = MagicMock(spec=Recommendation)
    mock_rec.task_id = "unique_task_id"
    # top_properties 모킹
    mock_rec.top_properties = [MagicMock()]
    mock_get_recommendations.return_value = [mock_rec]

    # 1. 로그인
    client.post("/auth/login", json={"email": "test@example.com", "password": "password123"})

    # 2. 상세 조회 요청
    response = client.get("/recommendations/unique_task_id/properties/1")
    assert response.status_code == 200
    data = response.json()
    
    # 하드코딩 리턴 구조 검증
    assert data["id"] == 1
    assert data["name"] == "삼성래미안"
    assert len(data["infrastructure"]) == 2
    assert data["infrastructure"][0]["name"] == "효창공원앞"
