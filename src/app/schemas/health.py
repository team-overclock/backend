"""헬스 체크 응답 스키마 모듈."""

from typing import Literal
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """기본 헬스 체크 응답 모델."""

    Hello: Literal["World"]
