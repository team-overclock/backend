"""에러 응답 스키마 모듈."""

from pydantic import BaseModel


class AppError(BaseModel):
    """기본 에러 응답 모델."""

    message: str
    detail: None = None
