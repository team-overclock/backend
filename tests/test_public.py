"""public 라우터 엔드포인트 테스트."""

import json


def test_get_regions(client, mock_redis) -> None:
    """동네 목록 조회(/regions) API 테스트."""
    # 1. Mock Redis 반환 데이터 설정
    # get_regions 함수 내부에서 redis.hgetall을 호출하므로
    # hgetall의 반환 데이터를 모킹해 둡니다.
    mock_regions_data = {
        "1": json.dumps({"id": 1, "name": "서울특별시 용산구 도원동"}, ensure_ascii=False),
        "3": json.dumps({"id": 3, "name": "서울특별시 강남구 대치동"}, ensure_ascii=False),
        "2": json.dumps({"id": 2, "name": "서울특별시 마포구 합정동"}, ensure_ascii=False),
    }
    
    mock_redis.hgetall.return_value = mock_regions_data

    # 2. API 호출
    response = client.get("/regions")

    # 3. 검증
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3
    assert data["items"][0]["id"] == 1
    assert data["items"][1]["id"] == 2
    assert data["items"][2]["id"] == 3
    assert data["items"][0]["name"] == "서울특별시 용산구 도원동"
    # Pydantic 스키마인 RegionItem 에는 depth가 정의되어 있지 않으므로 depth 키 검증은 생략합니다.


def test_get_infrastructure_types(client) -> None:
    """인프라 유형 목록 조회(/infrastructure-types) API 테스트."""
    # 1. API 호출
    response = client.get("/infrastructure-types")

    # 2. 검증
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data
    assert len(data["items"]) == data["total"]
    
    # 각 인프라 아이템의 구조 검증
    labels = [x["label"] for x in data["items"]]
    assert "지하철역" in labels
    assert "공원·녹지" in labels
    
    types = [x["type"] for x in data["items"]]
    assert "SUBWAY_STATION" in types
    assert "PARK" in types


def test_get_school_districts(client) -> None:
    """학군 등급 목록 조회(/school-districts-types) API 테스트."""
    # 1. API 호출
    response = client.get("/school-districts-types")

    # 2. 검증
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data
    assert len(data["items"]) == data["total"]
    
    # 각 학군 등급 아이템의 구조 검증
    labels = [x["label"] for x in data["items"]]
    assert "학원가 밀집형" in labels
    assert "균형 잡힌 학업형" in labels
    assert "여유로운 주거형" in labels
    
    types = [x["type"] for x in data["items"]]
    assert "INTENSIVE" in types
    assert "BALANCED" in types
    assert "RELAXED" in types

