""" 서비스 응답 스키마 모듈."""

from pydantic import BaseModel, Field

from .common import RegionName, InfrastructureType


# public

class RegionItem(BaseModel):
    id: int = Field(description="동네 id")
    name: RegionName

class RegionsResponse(BaseModel):
    total: int = Field(description="regions 개수")
    items: list[RegionItem] = Field(description="유효한 regions 목록")


class InfrastructureTypeItem(BaseModel):
    id: int = Field(description="인프라 유형 id")
    name: InfrastructureType

class InfrastructureTypesResponse(BaseModel):
    total: int = Field(description="인프라 유형 개수")
    items: list[InfrastructureTypeItem] = Field(description="유효한 인프라 유형 목록")
