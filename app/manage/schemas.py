from typing import Literal
from pydantic import BaseModel, Field


class ImmediateResponse(BaseModel):
    """즉시 실행 응답"""

    success: bool

class BackgroundSuccessResponse(BaseModel):
    """백그라운드 실행 성공 응답"""

    requested: Literal[True]


class DataDownloadStatusResponse(BaseModel):
    """데이터 상태 조회 응답"""

    curr_version: str | None
    downloading_version: str | None

class DataInsertStatusResponse(BaseModel):
    """데이터 상태 조회 응답"""

    has_region: bool
    has_property: bool
    has_infrastructure: bool


class ScoresStatusResponse(BaseModel):
    """점수 데이터 상태 조회 응답"""

    total: int


class GenerateSeedsRequest(BaseModel):
    """시드 데이터 생성 요청"""

    users: int = Field(0, description="생성할 사용자 수")
    recommendations: int = Field(0, description="생성할 추천 수")

class SeedsStatusResponse(BaseModel):
    """시드 데이터 개수 조회 응답"""

    total_users: int
    total_recommendations: int
