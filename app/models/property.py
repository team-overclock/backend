from typing import TYPE_CHECKING
from sqlalchemy import Column, ForeignKey, Numeric, String
from sqlalchemy.dialects.mysql import INTEGER, BIGINT
from sqlalchemy.orm import Mapped, relationship

from .base import Base


if TYPE_CHECKING:
    from . import Region, PropertyScore, PropertyInfrastructureDistance, Version

class Property(Base):
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
    - latitude: 부동산 위도
    - longitude: 부동산 경도
    - version_id: 해당 부동산 데이터의 버전 ID (foreign key)

    - region: 동네 정보
    - recommendation_entries: 해당 부동산이 포함된 추천 항목 목록
    - infrastructure_distances: 해당 부동산과 인프라 간의 거리 정보 목록
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
    latitude = Column(Numeric(10, 8), nullable=False)
    longitude = Column(Numeric(11, 8), nullable=False)
    version_id = Column(INTEGER(unsigned=True), ForeignKey("version.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False)

    region: Mapped["Region"] = relationship("Region", back_populates="properties")
    recommendation_entries: Mapped[list["PropertyScore"]] = relationship("PropertyScore", back_populates="property", cascade="all, delete-orphan")
    infrastructure_distances: Mapped[list["PropertyInfrastructureDistance"]] = relationship("PropertyInfrastructureDistance", back_populates="property", cascade="all, delete-orphan")
    version: Mapped["Version"] = relationship("Version", back_populates="properties")
