from typing import TYPE_CHECKING
from sqlalchemy import UniqueConstraint, Column, DateTime, Enum, String, JSON
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry

from .base import Base
from .mixin import CoordinatesMixin
from ..core.enums import InfrastructureTypeEnum


if TYPE_CHECKING:
    from . import PropertyInfrastructure

class Infrastructure(Base, CoordinatesMixin):
    """
    인프라 모델
    - id: 인프라 ID (unsigned, 자동 증가)
    - type: 인프라 유형 Enum (예: ELEMENTARY_SCHOOL, SUBWAY, PARK 등)
    - source_id: 원본 데이터에서의 인프라 고유 ID (예: 학교ID, 역사_ID 등)
    - name: 인프라 이름 (예: `"서울역"`, `"삼성역"`, `"여의도공원"` 등)
    - point: 인프라 point 바이너리 데이터
    - details: 인프라 상세 정보 JSON
    - updated_at: 마지막 업데이트 시각
    - deleted_at: 삭제 시각 (soft delete)

    - property_scores: 건물과의 점수 및 거리 정보 목록
    """

    __tablename__ = "infrastructure"

    id = Column(INTEGER(unsigned=True), primary_key=True, index=True)
    type: InfrastructureTypeEnum = Column(Enum(InfrastructureTypeEnum, native_enum=False, length=100), nullable=False)
    source_id = Column(String(100), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    point = Column(Geometry("POINT"), nullable=False, index=True)
    details: dict = Column(JSON(none_as_null=True), nullable=True, default={})
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime)

    property_scores: Mapped[list["PropertyInfrastructure"]] = relationship("PropertyInfrastructure", back_populates="infrastructure", cascade="all, delete-orphan")

    # 복합 unique, 인프라 유형간 source_id 충돌 방지
    __table_args__ = (
        UniqueConstraint("type", "source_id", name="uq_infrastructure_type_source_id"),
    )
