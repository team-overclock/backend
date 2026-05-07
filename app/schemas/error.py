"""에러 응답 스키마 모듈."""

from pydantic import BaseModel

from .service import RegionsResponse, InfrastructureTypeItem


class AppError(BaseModel):
    """기본 에러 응답 모델."""

    message: str
    detail: None = None


class RegionError(AppError):
    """동네 에러 응답 모델."""

    detail: RegionsResponse

class InfrastructureTypeError(AppError):
    """인프라 유형 에러 응답 모델."""

    detail: InfrastructureTypeItem
