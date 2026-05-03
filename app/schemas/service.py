""" 서비스 응답 스키마 모듈."""

from typing import Annotated
from pydantic import BaseModel, Field


# public

Region = Annotated[str, Field(description="동네 이름", examples=["서울특별시 강남구 역삼동"])]
InfrastructureType = Annotated[str, Field(description="인프라 유형", examples=["지하철역"])]

class RegionsResponse(BaseModel):
    total: int = Field(description="regions 개수")
    items: list[Region] = Field(description="유효한 regions 목록")


class InfrastructureTypesResponse(BaseModel):
    total: int = Field(description="인프라 유형 개수")
    items: list[InfrastructureType] = Field(description="유효한 인프라 유형 목록")
