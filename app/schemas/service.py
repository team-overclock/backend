""" 서비스 응답 스키마 모듈."""

from pydantic import BaseModel, Field

from ..core.enums import (
    InfrastructureTypeEnum,
    SchoolDistrictTypeEnum,
)
from .common import (
    PK_AI,
    RegionName,
    TaskID,
    PropertyName,
    Score,
    PriceUnit,
    Status,
    Datetime,
)


# # public

class RegionItem(BaseModel):
    id: PK_AI = Field(description="동네 id")
    name: RegionName

class RegionsResponse(BaseModel):
    total: int = Field(description="regions 개수")
    items: list[RegionItem] = Field(description="유효한 regions 목록")


class SchoolDistrictTypeItem(BaseModel):
    type: SchoolDistrictTypeEnum = Field(description="학군 유형 고유 타입", examples=[x.meta.type for x in SchoolDistrictTypeEnum])
    label: str = Field(description="학군 유형 한글명", examples=[x.meta.label for x in SchoolDistrictTypeEnum])
    description: str = Field(description="학군 유형 상세 설명", examples=[x.meta.description for x in SchoolDistrictTypeEnum])

class SchoolDistrictsResponse(BaseModel):
    total: int = Field(description="학군 유형 개수")
    items: list[SchoolDistrictTypeItem] = Field(description="유효한 학군 유형 목록")

class InfrastructureTypeItem(BaseModel):
    type: InfrastructureTypeEnum = Field(description="인프라 유형 고유 타입", examples=[x.meta.type for x in InfrastructureTypeEnum])
    emoji: str = Field(description="아이콘 이모지", examples=[x.meta.emoji for x in InfrastructureTypeEnum])
    label: str = Field(description="인프라 유형 한글명", examples=[x.meta.label for x in InfrastructureTypeEnum])
    description: str = Field(description="인프라 유형 상세 설명", examples=[x.meta.description for x in InfrastructureTypeEnum])

class InfrastructureTypesResponse(BaseModel):
    total: int = Field(description="인프라 유형 개수")
    items: list[InfrastructureTypeItem] = Field(description="유효한 인프라 유형 목록")

class HighSchoolItem(BaseModel):
    id: PK_AI = Field(description="고등학교 ID")
    name: str = Field(description="고등학교 이름")
    latitude: float = Field(description="위도")
    longitude: float = Field(description="경도")

class HighSchoolsResponse(BaseModel):
    total: int = Field(description="고등학교 수")
    items: list[HighSchoolItem] = Field(description="고등학교 목록")


# # recommendation

class PriceRange(BaseModel):
    """가격 범위"""

    min: PriceUnit | None
    max: PriceUnit | None

class AddressDetails(BaseModel):
    """주소 정보"""

    land_lot: str | None = Field(description="지번 주소")
    road_name: str | None = Field(description="도로명 주소")
    latitude: float = Field(description="위도")
    longitude: float = Field(description="경도")


class RecommendationCreateRequest(BaseModel):
    """추천 생성 요청"""

    name: str | None = Field(None, description="화면에 표시할 사용자 지정 추천 이름")
    region_id: PK_AI | None = Field(None, description="관심 있는 동네 ID")
    infrastructure_types: list[InfrastructureTypeEnum] = Field(description="관심 있는 인프라 유형 목록 (나열된 순서대로 높은 가중치 부여)", min_length=1)
    high_school_ids: list[PK_AI] | None = Field(None, description="관심 있는 고등학교 ID 목록 (우선순위 없음)")
    school_district_types: list[SchoolDistrictTypeEnum] | None = Field(None, description="관심 있는 학군 유형 목록 (우선순위 없음)")
    sale_price: PriceRange | None = Field(None, description="희망 매매 가격 범위")
    jeonse_price: PriceRange | None = Field(None, description="희망 전세 가격 범위")

class RecommendationCreateRequestResolved(BaseModel):
    """추천 생성 요청 (human-readable)"""

    name: str | None = Field(description="사용자 지정 추천에 대한 별칭")
    region: RegionItem | None = Field(description="관심 있는 동네 이름")
    infrastructure_types: list[InfrastructureTypeItem] = Field(description="인프라 유형 목록 (높은 가중치 순서)", min_length=1)
    high_schools: list[HighSchoolItem] = Field(description="관심 있는 고등학교 이름 목록")
    school_districts: list[SchoolDistrictTypeItem] | None = Field(None, description="관심 있는 학군 유형 목록")
    sale_price: PriceRange = Field(description="매매 가격 범위")
    jeonse_price: PriceRange = Field(description="전세 가격 범위")

class RecommendationMetadataUpdateRequest(BaseModel):
    """추천 메타데이터 업데이트 요청"""

    name: str | None = Field(None, description="화면에 표시할 사용자 지정 추천 이름, None으로 설정 시 기본 이름으로 변경")

class RecommendationCreateResponse(BaseModel):
    """추천 생성 요청에 대한 응답"""

    task_id: TaskID


class RecommendationReportItemInfrastructureSummary(InfrastructureTypeItem):
    """매물 주변 인프라 요약"""

    distance: float = Field(description="매물과의 거리(단위: m)")
    walking_duration: int = Field(description="매물에서 인프라까지의 도보 시간(분)")

class RecommendationReportItemInfrastructureDetail(InfrastructureTypeItem):
    """매물 주변 인프라 상세 정보"""

    name: str = Field(description="인프라 이름")
    score: Score = Field(description="추천 점수 계산에 사용된 인프라 점수")
    distance: float = Field(description="매물과의 거리(단위: m)")
    walking_duration: int = Field(description="매물에서 인프라까지의 도보 시간(분)")
    latitude: float = Field(description="위도")
    longitude: float = Field(description="경도")


class RecommendationReportItemSummary(BaseModel):
    """추천 매물 및 주변 인프라 요약"""

    id: PK_AI = Field(description="매물 고유 ID")
    name: PropertyName
    score: Score
    region: RegionItem = Field(description="동네 이름")
    address: AddressDetails = Field(description="매물 주소 정보")
    sale_price: PriceRange = Field(description="매물의 매매 가격 범위")
    jeonse_price: PriceRange = Field(description="매물의 전세 가격 범위")
    infrastructure: list[RecommendationReportItemInfrastructureSummary] = Field(description="매물 주변 인프라 요약 정보 (요청 시 선택한 인프라 유형만 포함, 거리순)")

class RecommendationReport(RecommendationCreateResponse):
    """추천 결과"""

    status: Status
    total: int | None = Field(description="추천 매물 개수 (`status`가 `in_progress`인 경우에만 `null`)")
    request_data: RecommendationCreateRequestResolved = Field(description="추천 요청 데이터")
    properties: list[RecommendationReportItemSummary] | None = Field(description="추천 매물 목록 (`status`가 `in_progress`인 경우에만 `null`)")


class RecommendationReportItemDetail(RecommendationReportItemSummary):
    """추천 매물 및 주변 인프라 상세 정보"""
    infrastructure: list[RecommendationReportItemInfrastructureDetail] = Field(description="매물 주변 모든 인프라 상세 정보")


class UserRecommendationsItem(RecommendationCreateResponse):
    """추천 요청에 대한 요약 정보"""

    status: Status
    requested_at: Datetime | None = Field(description="추천 요청 시각")
    last_viewed_at: Datetime | None = Field(description="마지막으로 추천 결과를 조회한 시각")
    request_data: RecommendationCreateRequestResolved = Field(description="추천 요청 데이터")
    # TODO: 추천 요청 목록 페이지에서 보여줄 결과 요약 데이터 제공

class UserRecommendations(BaseModel):
    """추천 요청 목록"""

    total: int = Field(description="추천 요청 수")
    items: list[UserRecommendationsItem] = Field(description="추천 요청 목록, 최신순")
