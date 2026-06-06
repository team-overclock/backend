"""에러 응답 스키마 모듈."""

from typing import Literal
from pydantic import BaseModel, Field

from ..core.enums import AppErrorCodeEnum, APP_ERROR_CODES
from .service import RegionsResponse


class NotFoundError(BaseModel):
    """FastAPI 404 에러"""

    message: Literal["Not Found"]
    detail: None


class AppError(BaseModel):
    """기본 에러"""

    code: str = Field(description="에러 코드", examples=APP_ERROR_CODES)
    message: str = Field(description="에러 메시지")
    detail: None = Field(None, description="에러 상세 정보")


class AuthenticationRequiredError(AppError):
    """로그인 필요"""

    code: Literal[AppErrorCodeEnum.AUTHENTICATION_REQUIRED]


class DuplicateEmailError(AppError):
    """이메일 중복 에러"""

    code: Literal[AppErrorCodeEnum.DUPLICATE_EMAIL]


class InvalidCredentialsError(AppError):
    """자격 증명 에러"""

    code: Literal[AppErrorCodeEnum.INVALID_CREDENTIALS]


class IncorrectCurrentPasswordError(AppError):
    """올바르지 않은 비밀번호"""

    code: Literal[AppErrorCodeEnum.INCORRECT_CURRENT_PASSWORD]


class RegionError(AppError):
    """동네 에러"""

    code: Literal[AppErrorCodeEnum.REGION_ERROR]
    detail: RegionsResponse
