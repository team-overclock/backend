"""추천(recommendations) 라우터 엔드포인트 테스트."""

from unittest.mock import MagicMock, patch
from app.models import User, Recommendation, SearchLog, Property, Infrastructure
from app.core.enums import InfrastructureTypeEnum, SchoolDistrictTypeEnum
from app.services.recommendation import _generate_recommendation_task_id

from datetime import datetime

def make_mock_user(id=1, email="test@example.com", name="Test User", cuid="cuid123"):
    """테스트용 가짜 User 모델 인스턴스 생성"""
    user = User(
        id=id,
        email=email,
        name=name,
        cuid=cuid,
    )
    user.password = "password123"
    user.created_at = datetime.utcnow()
    user.updated_at = datetime.utcnow()
    return user


@patch("app.dependencies.get_user_by_cuid")
@patch("app.routers.auth.get_user_by_email")
@patch("app.core.validate.get_region_by_id")
@patch("app.core.validate.verify_high_schools")
def test_request_generate_recommendation_success(
    mock_verify_high_schools, mock_get_region_by_id, mock_get_user_by_email, mock_get_user_by_cuid, client, mock_db
) -> None:
    """추천 생성 요청 성공 테스트."""
    # 1. 모킹 설정
    mock_user = make_mock_user()
    mock_get_user_by_email.return_value = mock_user
    mock_get_user_by_cuid.return_value = mock_user
    
    # 유효한 지역 반환 설정
    mock_get_region_by_id.return_value = {"id": 1, "name": "서울특별시 용산구 도원동"}
    mock_verify_high_schools.return_value = [{"id": 1, "name": "고등학교1"}, {"id": 2, "name": "고등학교2"}]

    mock_db.query.return_value.filter.return_value.first.return_value = None

    # 2. 로그인
    client.post("/auth/login", json={"email": "test@example.com", "password": "password123"})

    # 3. 추천 생성 요청
    response = client.post(
        "/recommendations",
        json={
            "name": "내 맞춤 추천",
            "region_id": 1,
            "infrastructure_types": ["SUBWAY_STATION", "PARK", "HIGH_SCHOOL"],
            "high_school_ids": [1, 2],
            "school_district_types": ["INTENSIVE", "BALANCED"],
            "sale_price": {"min": 0, "max": 1000000000},
            "jeonse_price": {"min": 0, "max": 500000000}
        }
    )

    assert response.status_code == 202
    data = response.json()
    
    expected_task_id = _generate_recommendation_task_id(
        region_id=1,
        infrastructure_types=[InfrastructureTypeEnum.SUBWAY_STATION, InfrastructureTypeEnum.PARK, InfrastructureTypeEnum.HIGH_SCHOOL],
        high_school_ids=[1, 2],
        school_district_types=[SchoolDistrictTypeEnum.INTENSIVE, SchoolDistrictTypeEnum.BALANCED],
        sale_price_min=0,
        sale_price_max=1000000000,
        jeonse_price_min=0,
        jeonse_price_max=500000000
    )
    assert data["task_id"] == expected_task_id



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
    """유효하지 않은 인프라 유형으로 추천 생성 요청 시 422 에러 검증."""
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

    assert response.status_code == 422
    data = response.json()
    assert any(err["loc"] == ["body", "infrastructure_types", 0] for err in data["detail"])


@patch("app.dependencies.get_user_by_cuid")
@patch("app.routers.auth.get_user_by_email")
@patch("app.core.validate.get_region_by_id")
@patch("app.core.validate.verify_high_schools")
def test_request_generate_recommendation_invalid_high_schools(
    mock_verify_high_schools, mock_get_region_by_id, mock_get_user_by_email, mock_get_user_by_cuid, client
) -> None:
    """유효하지 않은 고등학교 ID로 추천 생성 요청 시 400 에러 검증."""
    from app.core.exception import AppException
    from app.core.enums import AppErrorCodeEnum
    from fastapi import status

    mock_user = make_mock_user()
    mock_get_user_by_email.return_value = mock_user
    mock_get_user_by_cuid.return_value = mock_user
    mock_get_region_by_id.return_value = {"id": 1, "name": "서울특별시 용산구 도원동"}

    mock_verify_high_schools.side_effect = AppException(
        status_code=status.HTTP_400_BAD_REQUEST,
        code=AppErrorCodeEnum.HIGH_SCHOOL_ERROR,
        message="유효하지 않은 고등학교 ID가 포함되어 있습니다.",
        detail={"invalid_ids": [999]}
    )

    # 1. 로그인
    client.post("/auth/login", json={"email": "test@example.com", "password": "password123"})

    # 2. 추천 생성 요청
    response = client.post(
        "/recommendations",
        json={
            "region_id": 1,
            "infrastructure_types": ["SUBWAY_STATION", "HIGH_SCHOOL"],
            "high_school_ids": [999]
        }
    )

    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "HIGH_SCHOOL_ERROR"
    assert "유효하지 않은 고등학교 ID" in data["message"]


@patch("app.dependencies.get_user_by_cuid")
@patch("app.routers.auth.get_user_by_email")
@patch("app.core.validate.get_region_by_id")
def test_request_generate_recommendation_invalid_school_districts(
    mock_get_region_by_id, mock_get_user_by_email, mock_get_user_by_cuid, client
) -> None:
    """유효하지 않은 학군 등급값으로 추천 생성 요청 시 422 에러 검증."""
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
            "infrastructure_types": ["SUBWAY_STATION"],
            "school_district_types": ["TOP"]  # 유효하지 않은 등급
        }
    )

    assert response.status_code == 422
    data = response.json()
    assert any(err["loc"] == ["body", "school_district_types", 0] for err in data["detail"])


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
@patch("app.dependencies.get_search_log_by_user_id_and_task_id")
def test_get_recommendation_summary_success(
    mock_get_search_log, mock_get_user_by_email, mock_get_user_by_cuid, client, mock_db, mock_redis
) -> None:
    """추천 결과 요약 조회(GET /recommendations/{task_id}) 성공 테스트."""
    mock_user = make_mock_user()
    mock_get_user_by_email.return_value = mock_user
    mock_get_user_by_cuid.return_value = mock_user

    # 1개의 search_log 및 recommendation 리턴하도록 설정
    mock_rec = MagicMock(spec=Recommendation)
    mock_rec.task_id = "unique_task_id"
    mock_rec.region = "서울특별시 용산구 도원동"
    mock_rec.infrastructure_priorities = ["SUBWAY_STATION"]
    mock_rec.school_district_types = ["INTENSIVE"]
    mock_rec.high_school_ids = [1]
    mock_rec.sale_price_min = 0
    mock_rec.sale_price_max = 1000000000
    mock_rec.jeonse_price_min = 0
    mock_rec.jeonse_price_max = 500000000
    mock_rec.in_progress = False

    mock_rec.top_properties = [
        {
            "id": 1,
            "name": "삼성래미안",
            "score": 87,
            "region": "서울특별시 용산구 도원동",
            "sale_price_min": 1200000000,
            "sale_price_max": 1200000000,
            "jeonse_price_min": 440000000,
            "jeonse_price_max": 440000000,
            "infrastructure_scores": [
                {"type": "SUBWAY_STATION", "distance": 0.6, "walking_duration": 13}
            ]
        }
    ]
    
    mock_search_log = MagicMock(spec=SearchLog)
    mock_search_log.task_id = "unique_task_id"
    mock_search_log.name = "내 맞춤 추천"
    mock_search_log.recommendation = mock_rec
    mock_get_search_log.return_value = [mock_search_log]

    # Redis 모킹
    import json as py_json
    def mock_hgetall(key):
        if key == "regions:all":
            return {
                "1": py_json.dumps({"id": 1, "name": "서울특별시 용산구 도원동"}, ensure_ascii=False),
            }
        elif key == "high_schools:all":
            return {
                "1": py_json.dumps({"id": 1, "name": "고등학교1", "latitude": 37.5383, "longitude": 126.9553}, ensure_ascii=False),
            }
        return {}
    mock_redis.hgetall.side_effect = mock_hgetall
    mock_redis.get.return_value = "0"  # max_depth

    # DB 모킹
    mock_property = MagicMock(spec=Property)
    mock_property.id = 1
    mock_property.land_lot_address = "서울특별시 용산구 도원동 23"
    mock_property.road_name_address = "서울특별시 용산구 새창로 70"
    mock_property.latitude = 37.53830000
    mock_property.longitude = 126.95532000
    mock_db.query().filter().all.return_value = [mock_property]

    # 1. 로그인
    client.post("/auth/login", json={"email": "test@example.com", "password": "password123"})

    # 2. 요약 조회 요청
    response = client.get("/recommendations/unique_task_id")
    assert response.status_code == 200
    data = response.json()
    
    assert data["task_id"] == "unique_task_id"
    assert data["status"] == "completed"
    assert len(data["properties"]) == 1
    assert data["properties"][0]["name"] == "삼성래미안"


@patch("app.dependencies.get_user_by_cuid")
@patch("app.routers.auth.get_user_by_email")
@patch("app.dependencies.get_search_log_by_user_id_and_task_id")
def test_get_recommendation_property_detail_success(
    mock_get_search_log, mock_get_user_by_email, mock_get_user_by_cuid, client, mock_db, mock_redis
) -> None:
    """추천 매물 상세 조회(GET /recommendations/{task_id}/properties/{property_id}) 성공 테스트."""
    mock_user = make_mock_user()
    mock_get_user_by_email.return_value = mock_user
    mock_get_user_by_cuid.return_value = mock_user

    # 1개의 search_log 및 recommendation 리턴하도록 설정
    mock_rec = MagicMock(spec=Recommendation)
    mock_rec.task_id = "unique_task_id"
    mock_rec.region = "서울특별시 용산구 도원동"
    mock_rec.infrastructure_priorities = ["SUBWAY_STATION"]
    mock_rec.school_district_types = ["INTENSIVE"]
    mock_rec.high_school_ids = [1]
    mock_rec.sale_price_min = 0
    mock_rec.sale_price_max = 1000000000
    mock_rec.jeonse_price_min = 0
    mock_rec.jeonse_price_max = 500000000
    mock_rec.in_progress = False

    # top_properties 모킹
    mock_rec.top_properties = [
        {
            "id": 1,
            "name": "삼성래미안",
            "score": 87,
            "region": "서울특별시 용산구 도원동",
            "sale_price_min": 1200000000,
            "sale_price_max": 1200000000,
            "jeonse_price_min": 440000000,
            "jeonse_price_max": 440000000,
            "infrastructure_scores": [
                {"id": 1, "type": "SUBWAY_STATION", "distance": 0.6, "walking_duration": 13, "name": "효창공원앞", "score": 90}
            ]
        }
    ]
    
    mock_search_log = MagicMock(spec=SearchLog)
    mock_search_log.task_id = "unique_task_id"
    mock_search_log.name = "내 맞춤 추천"
    mock_search_log.recommendation = mock_rec
    mock_get_search_log.return_value = [mock_search_log]

    # Redis 모킹
    import json as py_json
    def mock_hgetall(key):
        if key == "regions:all":
            return {
                "1": py_json.dumps({"id": 1, "name": "서울특별시 용산구 도원동"}, ensure_ascii=False),
            }
        elif key == "high_schools:all":
            return {
                "1": py_json.dumps({"id": 1, "name": "고등학교1", "latitude": 37.5383, "longitude": 126.9553}, ensure_ascii=False),
            }
        return {}
    mock_redis.hgetall.side_effect = mock_hgetall
    mock_redis.get.return_value = "0"  # max_depth

    # DB 모킹
    mock_property = MagicMock(spec=Property)
    mock_property.id = 1
    mock_property.land_lot_address = "서울특별시 용산구 도원동 23"
    mock_property.road_name_address = "서울특별시 용산구 새창로 70"
    mock_property.latitude = 37.53830000
    mock_property.longitude = 126.95532000

    mock_infra = MagicMock(spec=Infrastructure)
    mock_infra.id = 1
    mock_infra.name = "효창공원앞"
    mock_infra.latitude = 37.53895534
    mock_infra.longitude = 126.96173072

    def mock_query(model):
        q = MagicMock()
        if model == Property:
            q.filter().first.return_value = mock_property
        elif model == Infrastructure:
            q.filter().all.return_value = [mock_infra]
        return q
    mock_db.query.side_effect = mock_query

    # 1. 로그인
    client.post("/auth/login", json={"email": "test@example.com", "password": "password123"})

    # 2. 상세 조회 요청
    response = client.get("/recommendations/unique_task_id/properties/1")
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == 1
    assert data["name"] == "삼성래미안"
    assert len(data["infrastructure"]) == 1
    assert data["infrastructure"][0]["name"] == "효창공원앞"


@patch("app.dependencies.get_user_by_cuid")
@patch("app.routers.auth.get_user_by_email")
@patch("app.dependencies.get_search_log_by_user_id_and_task_id")
def test_get_recommendation_summary_redirect(
    mock_get_search_log, mock_get_user_by_email, mock_get_user_by_cuid, client
) -> None:
    """추천 결과 요약 조회 시 full id가 아닌 경우 302 리다이렉션 테스트."""
    mock_user = make_mock_user()
    mock_get_user_by_email.return_value = mock_user
    mock_get_user_by_cuid.return_value = mock_user

    # unique_task_id가 실제 task_id이고, 사용자는 unique_ta로 요청
    mock_rec = MagicMock(spec=Recommendation)
    mock_rec.task_id = "unique_task_id"
    
    mock_search_log = MagicMock(spec=SearchLog)
    mock_search_log.task_id = "unique_task_id"
    mock_search_log.recommendation = mock_rec
    mock_get_search_log.return_value = [mock_search_log]

    # 1. 로그인
    client.post("/auth/login", json={"email": "test@example.com", "password": "password123"})

    # 2. 요약 조회 요청 (prefix로 요청)
    response = client.get("/recommendations/unique_ta", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers.get("location") == "/recommendations/unique_task_id"

