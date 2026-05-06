from typing import TYPE_CHECKING
from sqlalchemy import Column, ForeignKey, Numeric, String
from sqlalchemy.dialects.mysql import INTEGER, TINYINT
from sqlalchemy.orm import Mapped, relationship

from .base import Base


if TYPE_CHECKING:
    from . import InfrastructureType, Region, PropertyInfrastructureDistance, InfrastructureScore, Version

class Infrastructure(Base):
    """
    인프라 모델
    - id: 인프라 ID (unsigned, 자동 증가)
    - type_id: 인프라 유형 ID (foreign key)
    - region_id: 동네 ID (foreign key)
    - name: 인프라 이름 (예: `"서울역"`, `"삼성역"`, `"여의도공원"` 등)
    - latitude: 인프라 위도
    - longitude: 인프라 경도
    - version_id: 해당 인프라 데이터의 버전 ID (foreign key)

    - type: 인프라 유형 정보
    - region: 동네 정보
    - property_distances: 해당 인프라와 부동산 간의 거리 정보 목록
    - infrastructure_scores: 추천 시 계산된 인프라의 점수 목록
    - version: 버전 정보
    """

    __tablename__ = "infrastructure"

    id = Column(INTEGER(unsigned=True), primary_key=True, index=True)
    type_id = Column(TINYINT(unsigned=True), ForeignKey("infrastructure_type.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    region_id = Column(INTEGER(unsigned=True), ForeignKey("region.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    latitude = Column(Numeric(10, 8), nullable=False)
    longitude = Column(Numeric(11, 8), nullable=False)
    version_id = Column(INTEGER(unsigned=True), ForeignKey("version.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False)

    type: Mapped["InfrastructureType"] = relationship("InfrastructureType", back_populates="infrastructures")
    region: Mapped["Region"] = relationship("Region", back_populates="infrastructures")
    property_distances: Mapped[list["PropertyInfrastructureDistance"]] = relationship("PropertyInfrastructureDistance", back_populates="infrastructure", cascade="all, delete-orphan")
    infrastructure_scores: Mapped[list["InfrastructureScore"]] = relationship("InfrastructureScore", back_populates="infrastructure", cascade="all, delete-orphan")
    version: Mapped["Version"] = relationship("Version", back_populates="infrastructures")

    def to_dict(self):
        """응답용 데이터로 변환 및 반환"""
        return {
            "id": self.id,
            "name": self.name,
        }
