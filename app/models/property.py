from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Column, DateTime, String
from sqlalchemy.dialects.mysql import INTEGER, DECIMAL, BIGINT
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry

from .base import Base
from .mixin import CoordinatesMixin


if TYPE_CHECKING:
    from . import PropertyInfrastructure, Region

class Property(Base, CoordinatesMixin):
    """
    건물 모델
    - id: 건물 ID (unsigned, 자동 증가)
    - source_id: 원본 데이터에서의 건물 고유 ID (아파트코드)
    - region_id: 건물이 위치한 동네의 ID (foreign key)
    - type: 건물 유형 (예: 공동주택)
    - name: 건물 이름 (예: `"래미안 아파트"`)
    - land_lot_address: 지번 주소
    - road_name_address: 도로명 주소
    - point: 건물 point 바이너리 데이터
    - dong_count: 동 수
    - household_count: 세대 수
    - parking_count: 주차 대수
    - parking_per_household: 세대당 주차 대수
    - sale_price_min: 매매 최소 가격
    - sale_price_max: 매매 최대 가격
    - jeonse_price_min: 전세 최소 가격
    - jeonse_price_max: 전세 최대 가격
    - updated_at: 마지막 업데이트 시각
    - deleted_at: 삭제 시각 (soft delete)

    - infrastructure_scores: 해당 건물과 인프라 간의 점수 및 거리 정보 목록
    - region: 건물이 위치한 동네 정보
    """

    __tablename__ = "property"

    id = Column(INTEGER(unsigned=True), primary_key=True, index=True)
    source_id = Column(String(100), nullable=False, unique=True)
    region_id = Column(INTEGER(unsigned=True), ForeignKey("region.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    type = Column(String(100))
    name = Column(String(255))
    land_lot_address = Column(String(255))
    road_name_address = Column(String(255))
    point = Column(Geometry("POINT"), nullable=False, index=True)
    dong_count = Column(INTEGER(unsigned=True))
    household_count = Column(INTEGER(unsigned=True))
    parking_count = Column(INTEGER(unsigned=True))
    parking_per_household = Column(DECIMAL(4, 2, unsigned=True))
    sale_price_min = Column(BIGINT(unsigned=True))
    sale_price_max = Column(BIGINT(unsigned=True))
    jeonse_price_min = Column(BIGINT(unsigned=True))
    jeonse_price_max = Column(BIGINT(unsigned=True))
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime)

    region: Mapped["Region"] = relationship("Region", back_populates="properties")
    infrastructure_scores: Mapped[list["PropertyInfrastructure"]] = relationship("PropertyInfrastructure", back_populates="property", cascade="all, delete-orphan")
