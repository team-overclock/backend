"""에러 응답 스키마 모듈."""

from typing import Union
from pydantic import BaseModel

from .service import RegionsResponse, InfrastructureTypesResponse


class AppError(BaseModel):
    """기본 에러"""

    message: str
    detail: None = None


class RegionError(AppError):
    """동네 에러"""

    detail: RegionsResponse

class InfrastructureTypeError(AppError):
    """인프라 유형 에러"""

    detail: InfrastructureTypesResponse


class RegionOrInfrastructureTypeError(BaseModel):
    """동네 또는 인프라 유형 에러"""
    detail: Union[RegionsResponse, InfrastructureTypesResponse]
