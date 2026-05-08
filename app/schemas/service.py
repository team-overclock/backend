""" 서비스 응답 스키마 모듈."""

from pydantic import BaseModel, Field

from .common import (
    PK_AI,
    RegionName,
    InfrastructureType,
    TaskID,
    PropertyName,
    Score,
    PriceUnit,
    Status,
    Datetime,
)


# public

class RegionItem(BaseModel):
    id: PK_AI = Field(description="동네 id")
    name: RegionName

class RegionsResponse(BaseModel):
    total: int = Field(description="regions 개수")
    items: list[RegionItem] = Field(description="유효한 regions 목록")


class InfrastructureTypeItem(BaseModel):
    id: PK_AI = Field(description="인프라 유형 id")
    name: InfrastructureType

class InfrastructureTypesResponse(BaseModel):
    total: int = Field(description="인프라 유형 개수")
    items: list[InfrastructureTypeItem] = Field(description="유효한 인프라 유형 목록")


# recommendation

class PriceRange(BaseModel):
    """가격 범위"""

    min: PriceUnit
    max: PriceUnit

class AddressDetails(BaseModel):
    """주소 정보"""

    land_lot: str = Field(description="지번 주소")
    road_name: str | None = Field(description="도로명 주소")
    latitude: float = Field(description="위도")
    longitude: float = Field(description="경도")


class RecommendationCreateRequest(BaseModel):
    """추천 생성 요청"""

    name: str | None = Field(None, description="화면에 표시할 사용자 지정 추천 이름")
    region_id: PK_AI = Field(description="관심 있는 동네 ID")
    infrastructure_type_ids: list[PK_AI] = Field(description="관심 있는 인프라 유형 ID 목록 (나열된 순서대로 높은 가중치 부여)", min_length=1)
    sale_price: PriceRange | None = Field(None, description="희망 매매 가격 범위")
    deposit_price: PriceRange | None = Field(None, description="희망 전세 가격 범위")

class RecommendationCreateRequestResolved(BaseModel):
    """추천 생성 요청 (human-readable)"""

    name: str | None = Field(description="사용자 지정 추천에 대한 별칭")
    region: RegionName = Field(description="관심 있는 동네 이름")
    infrastructure_types: list[InfrastructureType] = Field(description="인프라 유형 목록 (높은 가중치 순서)", min_length=1)
    sale_price: PriceRange | None = Field(description="매매 가격 범위")
    deposit_price: PriceRange | None = Field(description="전세 가격 범위")

class RecommendationCreateResponse(BaseModel):
    """추천 생성 요청에 대한 응답"""

    task_id: TaskID
    status: Status


class RecommendationReportItemInfrastructure(BaseModel):
    """매물 주변 인프라 정보"""

    type: InfrastructureType = Field(description="인프라 유형")
    name: str = Field(description="인프라 이름")
    score: Score = Field(description="추천 점수 계산에 사용된 인프라 점수")
    distance: float = Field(description="매물과의 거리(단위: m)")
    walking_duration: int = Field(description="매물에서 인프라까지의 도보 시간(분)")
    latitude: float = Field(description="위도")
    longitude: float = Field(description="경도")

class RecommendationReportItem(BaseModel):
    """추천 매물 및 주변 인프라"""

    name: PropertyName
    score: Score
    address: AddressDetails = Field(description="매물 주소 정보")
    sale_price: int | None = Field(description="매물의 매매 최소 가격")
    deposit_price: int | None = Field(description="매물의 전세 최소 가격")
    infrastructure: list[RecommendationReportItemInfrastructure] = Field(description="매물 주변 인프라")

class RecommendationReport(RecommendationCreateResponse):
    """추천 결과"""

    total: int | None = Field(description="추천 매물 개수 (`status`가 `in_progress`인 경우에만 `null`)")
    request_data: RecommendationCreateRequestResolved = Field(description="추천 요청 데이터")
    properties: list[RecommendationReportItem] | None = Field(description="추천 매물 목록 (`status`가 `in_progress`인 경우에만 `null`)")


class UserRecommendationsItem(RecommendationCreateResponse):
    """추천 요청에 대한 요약 정보"""

    requested_at: Datetime | None = Field(description="추천 요청 시각")
    last_viewed_at: Datetime | None = Field(description="마지막으로 추천 결과를 조회한 시각")
    request_data: RecommendationCreateRequestResolved = Field(description="추천 요청 데이터")
    # TODO: 추천 요청 목록 페이지에서 보여줄 결과 요약 데이터 제공

class UserRecommendations(BaseModel):
    """추천 요청 목록"""

    total: int = Field(description="추천 요청 수")
    items: list[UserRecommendationsItem] = Field(description="추천 요청 목록")
