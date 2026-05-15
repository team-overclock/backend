from typing import TYPE_CHECKING
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.mysql import INTEGER, BIGINT
from sqlalchemy.orm import Mapped, relationship
from geoalchemy2 import Geometry

from .base import Base
from .mixin import CoordinatesMixin


if TYPE_CHECKING:
    from . import Region, RecommendationPropertyScore, PropertyInfrastructureScore, RecommendationPropertyInfrastructureScore, Version

class Property(Base, CoordinatesMixin):
    """
    부동산 모델
    - id: 부동산 ID (unsigned, 자동 증가)
    - region_id: 동네 ID (foreign key)
    - name: 부동산 이름 (예: `"래미안 아파트"` 등)
    - land_lot_address: 지번 주소 (예: `"서울특별시 강남구 역삼동 761-10"` 등)
    - road_name_address: 도로명 주소 (예: `"서울특별시 도봉구 도봉로136길 28"` 등)
    - sale_price_min: 매매가 최저 가격
    - sale_price_max: 매매가 최고 가격
    - deposit_price_min: 전세가 최저 가격
    - deposit_price_max: 전세가 최고 가격
    - point: 부동산 point 바이너리 데이터
    - version_id: 해당 부동산 데이터의 버전 ID (foreign key)

    - region: 동네 정보
    - recommendations: 해당 부동산을 추천 결과로 포함하는 추천 목록
    - infrastructure_scores: 해당 부동산과 인프라 간의 점수 및 거리 정보 목록
    - recommendation_infrastructure_scores: 추천 결과에서 가중치가 적용되어 계산된 인프라와의 점수 목록
    - version: 버전 정보
    """

    __tablename__ = "property"

    id = Column(INTEGER(unsigned=True), primary_key=True, index=True)
    region_id = Column(INTEGER(unsigned=True), ForeignKey("region.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    land_lot_address = Column(String(255), nullable=False)
    road_name_address = Column(String(255), nullable=True)
    sale_price_min = Column(BIGINT(unsigned=True))
    sale_price_max = Column(BIGINT(unsigned=True))
    deposit_price_min = Column(BIGINT(unsigned=True))
    deposit_price_max = Column(BIGINT(unsigned=True))
    point = Column(Geometry("POINT"), nullable=False, index=True)
    version_id = Column(INTEGER(unsigned=True), ForeignKey("version.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False)

    region: Mapped["Region"] = relationship("Region", back_populates="properties")
    recommendations: Mapped[list["RecommendationPropertyScore"]] = relationship("RecommendationPropertyScore", back_populates="property", cascade="all, delete-orphan")
    infrastructure_scores: Mapped[list["PropertyInfrastructureScore"]] = relationship("PropertyInfrastructureScore", back_populates="property", cascade="all, delete-orphan")
    recommendation_infrastructure_scores: Mapped[list["RecommendationPropertyInfrastructureScore"]] = relationship("RecommendationPropertyInfrastructureScore", back_populates="property", cascade="all, delete-orphan")
    version: Mapped["Version"] = relationship("Version", back_populates="properties")
