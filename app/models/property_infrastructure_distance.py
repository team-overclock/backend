from typing import TYPE_CHECKING
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.mysql import INTEGER, DECIMAL
from sqlalchemy.orm import Mapped, relationship

from .base import Base


if TYPE_CHECKING:
    from . import Property, Infrastructure

class PropertyInfrastructureDistance(Base):
    """
    부동산-인프라 간 거리 모델
    - property_id: 부동산 ID (foreign key)
    - infrastructure_id: 인프라 ID (foreign key)
    - distance: 부동산과 인프라 간의 거리 (km 단위)
    - walking_duration: 도보 이동 시간 (분 단위)

    - property: 부동산 정보
    - infrastructure: 인프라 정보
    """

    __tablename__ = "property_infrastructure_distance"

    property_id = Column(INTEGER(unsigned=True), ForeignKey("property.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    infrastructure_id = Column(INTEGER(unsigned=True), ForeignKey("infrastructure.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    distance = Column(DECIMAL(7, 3), nullable=False)
    walking_duration = Column(INTEGER(unsigned=True), nullable=False)

    property: Mapped["Property"] = relationship("Property", back_populates="infrastructure_distances")
    infrastructure: Mapped["Infrastructure"] = relationship("Infrastructure", back_populates="property_distances")
