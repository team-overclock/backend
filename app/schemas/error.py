"""에러 응답 스키마 모듈."""

from typing import Literal
from pydantic import BaseModel, Field

from ..core.enums import APP_ERROR_CODES
from .service import RegionsResponse, InfrastructureTypesResponse


class AppError(BaseModel):
    """기본 에러"""

    code: str = Field(description="에러 코드", examples=APP_ERROR_CODES)
    message: str = Field(description="에러 메시지")
    detail: None = Field(None, description="에러 상세 정보")


class RegionError(AppError):
    """동네 에러"""

    code: Literal["REGION_ERROR"]
    detail: RegionsResponse


class InfrastructureTypeError(AppError):
    """인프라 유형 에러"""

    code: Literal["INFRASTRUCTURE_TYPE_ERROR"]
    detail: InfrastructureTypesResponse
