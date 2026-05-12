""" 서비스 응답 스키마 모듈."""

from typing import Annotated, Literal
from pydantic import BaseModel, Field

from .common import RegionName, InfrastructureType


# public

class RegionItem(BaseModel):
    id: int = Field(description="동네 id")
    name: RegionName

class RegionsResponse(BaseModel):
    total: int = Field(description="regions 개수")
    items: list[RegionItem] = Field(description="유효한 regions 목록")


class InfrastructureTypeItem(BaseModel):
    id: int = Field(description="인프라 유형 id")
    name: InfrastructureType

class InfrastructureTypesResponse(BaseModel):
    total: int = Field(description="인프라 유형 개수")
    items: list[InfrastructureTypeItem] = Field(description="유효한 인프라 유형 목록")


# recommendation

TaskID = Annotated[str, Field(description="추천 요청을 식별하는 고유 ID", min_length=1)]
Status = Annotated[Literal["completed", "in_progress", "failed"], Field(description="요청 처리 상태")]
Score = Annotated[float, Field(description="추천 점수", ge=0, le=100)]
PriceUnit = Annotated[int, Field(description="단위: 원")]

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


class CreateRecommendationRequest(BaseModel):
    """추천 생성 요청"""

    region_id: int = Field(description="관심 있는 동네 ID")
    name: str | None = Field(None, description="화면에 표시할 사용자 지정 추천 이름")
    infrastructure_type_ids: list[int] = Field(description="관심 있는 인프라 유형 ID 목록 (나열된 순서대로 높은 가중치 부여)", min_length=1)
    sale_price: PriceRange | None = Field(None, description="희망 매매 가격 범위")
    deposit_price: PriceRange | None = Field(None, description="희망 전세 가격 범위")

class CreateRecommendationResponse(BaseModel):
    """추천 생성 요청에 대한 응답"""

    task_id: TaskID


class InfrastructureItem(BaseModel):
    """매물 주변 인프라 정보"""

    type_id: int = Field(description="인프라 유형 id")
    type_name: InfrastructureType = Field(description="인프라 유형")
    name: str = Field(description="인프라 이름")
    score: Score = Field(description="추천 점수 계산에 사용된 인프라 점수")
    distance: float = Field(description="매물과의 거리(단위: m)")
    walking_duration: int = Field(description="매물에서 인프라까지의 도보 시간(분)")
    latitude: float = Field(description="위도")
    longitude: float = Field(description="경도")

class RecommendationItem(BaseModel):
    """추천 매물 및 주변 인프라"""

    name: str = Field(description="매물 이름")
    score: Score
    address: AddressDetails = Field(description="매물 주소 정보")
    sale_price: PriceRange | None = Field(description="매물의 매매 가격 범위")
    deposit_price: PriceRange | None = Field(description="매물의 전세 가격 범위")
    infrastructure: list[InfrastructureItem] = Field(description="매물 주변 인프라 목록")

class RecommendationDetailResponse(BaseModel):
    """추천 결과"""

    status: Status
    total: int | None = Field(description="추천 매물 개수 (`status`가 `in_progress`인 경우에만 `null`)")
    items: list[RecommendationItem] | None = Field(description="추천 매물 목록 (`status`가 `in_progress`인 경우에만 `null`)")


class UserRecommendationItem(BaseModel):
    """추천 요청 시 선택한 조건"""

    task_id: TaskID
    status: Status
    region_id: int = Field(description="동네 ID")
    name: str | None = Field(description="사용자 지정 추천 이름")
    infrastructure_type_ids: list[int] = Field(description="인프라 유형 ID 목록", min_length=1)
    sale_price: PriceRange | None = Field(description="매매 가격 범위")
    deposit_price: PriceRange | None = Field(description="전세 가격 범위")

class UserRecommendationsResponse(BaseModel):
    """추천 요청 목록"""

    total: int = Field(description="추천 요청 수")
    items: list[UserRecommendationItem] = Field(description="추천 요청 목록")
