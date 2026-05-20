from typing import TYPE_CHECKING
from sqlalchemy import Column, ForeignKey, DateTime, String
from sqlalchemy.dialects.mysql import INTEGER, DECIMAL
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from .base import Base


if TYPE_CHECKING:
    from . import Infrastructure, Property

class PropertyInfrastructure(Base):
    """
    인프라-건물 점수 모델
    - infrastructure_id: 인프라 ID (foreign key)
    - property_id: 건물 ID (foreign key)
    - infrastructure_type: infrastructure_id에 해당하는 인프라 유형
    - property_type: property_id에 해당하는 건물 유형
    - score: 해당 인프라-건물 조합에 대한 점수 (0~100 사이의 소수점 2자리)
    - distance: 해당 인프라와 건물 간의 거리 (미터 단위)
    - updated_at: 마지막 업데이트 시각

    - infrastructure: 인프라 정보
    - property: 건물 정보
    """

    __tablename__ = "property_infrastructure"

    infrastructure_id = Column(INTEGER(unsigned=True), ForeignKey("infrastructure.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    property_id = Column(INTEGER(unsigned=True), ForeignKey("property.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    infrastructure_type = Column(String(100), nullable=False)
    property_type = Column(String(100))
    score = Column(DECIMAL(5, 2, unsigned=True), nullable=False)
    distance = Column(INTEGER(unsigned=True), nullable=False)
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    infrastructure: Mapped["Infrastructure"] = relationship("Infrastructure", back_populates="property_scores")
    property: Mapped["Property"] = relationship("Property", back_populates="infrastructure_scores")
