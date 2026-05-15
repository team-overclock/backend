from typing import TYPE_CHECKING
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.mysql import INTEGER, TINYINT
from sqlalchemy.orm import Mapped, relationship
from geoalchemy2 import Geometry

from .base import Base
from .mixin import CoordinatesMixin


if TYPE_CHECKING:
    from . import InfrastructureType, Region, PropertyInfrastructureScore, RecommendationPropertyInfrastructureScore, Version

class Infrastructure(Base, CoordinatesMixin):
    """
    인프라 모델
    - id: 인프라 ID (unsigned, 자동 증가)
    - type_id: 인프라 유형 ID (foreign key)
    - region_id: 동네 ID (foreign key)
    - name: 인프라 이름 (예: `"서울역"`, `"삼성역"`, `"여의도공원"` 등)
    - point: 인프라 point 바이너리 데이터
    - version_id: 해당 인프라 데이터의 버전 ID (foreign key)

    - type: 인프라 유형 정보
    - region: 동네 정보
    - property_scores: 부동산과의 점수 및 거리 정보 목록
    - recommendation_infrastructure_scores: 추천 결과에서 가중치가 적용되어 계산된 부동산과의 점수 목록
    - version: 버전 정보
    """

    __tablename__ = "infrastructure"

    id = Column(INTEGER(unsigned=True), primary_key=True, index=True)
    type_id = Column(TINYINT(unsigned=True), ForeignKey("infrastructure_type.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    region_id = Column(INTEGER(unsigned=True), ForeignKey("region.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    point = Column(Geometry("POINT"), nullable=False, index=True)
    version_id = Column(INTEGER(unsigned=True), ForeignKey("version.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False)

    type: Mapped["InfrastructureType"] = relationship("InfrastructureType", back_populates="infrastructures")
    region: Mapped["Region"] = relationship("Region", back_populates="infrastructures")
    property_scores: Mapped[list["PropertyInfrastructureScore"]] = relationship("PropertyInfrastructureScore", back_populates="infrastructure", cascade="all, delete-orphan")
    recommendation_infrastructure_scores: Mapped[list["RecommendationPropertyInfrastructureScore"]] = relationship("RecommendationPropertyInfrastructureScore", back_populates="infrastructure", cascade="all, delete-orphan")
    version: Mapped["Version"] = relationship("Version", back_populates="infrastructures")

    def to_dict(self):
        """응답용 데이터로 변환 및 반환"""
        return {
            "id": self.id,
            "name": self.name,
        }
