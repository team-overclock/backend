from typing import Literal
from pydantic import BaseModel, Field


class BackgroundSuccessResponse(BaseModel):
    """백그라운드 실행 성공 응답"""

    requested: Literal[True]


class GenerateSeedsRequest(BaseModel):
    """시드 데이터 생성 요청"""

    users: int = Field(0, description="생성할 사용자 수")
    recommendations: int = Field(0, description="생성할 추천 수")

class SeedsStatusResponse(BaseModel):
    """시드 데이터 개수 조회 응답"""

    total_users: int
    total_recommendations: int
