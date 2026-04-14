from sqlalchemy import Column, ForeignKey, Numeric, String
from sqlalchemy.dialects.mysql import INTEGER, TINYINT
from sqlalchemy.orm import relationship

from .base import Base


class Infrastructure(Base):
    """
    인프라 모델
    - id: 인프라 ID (unsigned, 자동 증가)
    - type_id: 인프라 유형 ID (foreign key)
    - region_id: 지역 ID (foreign key)
    - name: 인프라 이름 (예: `"서울역"`, `"삼성역"`, `"여의도공원"` 등)
    - latitude: 인프라 위도
    - longitude: 인프라 경도
    - latest_version_id: 해당 인프라 데이터의 버전 ID (foreign key)

    - type: 인프라 유형 정보
    - region: 지역 정보
    - latest_version: 버전 정보
    """

    __tablename__ = "infrastructure"

    id = Column(INTEGER(unsigned=True), primary_key=True, index=True)
    type_id = Column(TINYINT(unsigned=True), ForeignKey("infrastructure_type.id"), nullable=False)
    region_id = Column(INTEGER(unsigned=True), ForeignKey("region.id"), nullable=False)
    name = Column(String(255), nullable=False)
    latitude = Column(Numeric(10, 8), nullable=False)
    longitude = Column(Numeric(11, 8), nullable=False)
    latest_version_id = Column(INTEGER(unsigned=True), ForeignKey("version.id"), nullable=False)

    type = relationship("InfrastructureType", backref="infrastructures")
    region = relationship("Region", back_populates="infrastructures")
    latest_version = relationship("Version", back_populates="infrastructures")
