from sqlalchemy import Column, ForeignKey, Numeric, String
from sqlalchemy.dialects.mysql import INTEGER, BIGINT
from sqlalchemy.orm import relationship

from .base import Base


class Property(Base):
    """
    부동산 모델
    - id: 부동산 ID (unsigned, 자동 증가)
    - region_id: 지역 ID (foreign key)
    - name: 부동산 이름 (예: `"래미안 아파트"` 등)
	- address: 부동산 주소 (예: `"서울특별시 강남구 역삼동 123-45"` 등)
    - sale_price_min: 매매가 최저 가격
    - sale_price_max: 매매가 최고 가격
    - deposit_price_min: 전세가 최저 가격
    - deposit_price_max: 전세가 최고 가격
    - latitude: 부동산 위도
    - longitude: 부동산 경도
    - latest_version_id: 해당 부동산 데이터의 버전 ID (foreign key)

    - region: 지역 정보
    - latest_version: 버전 정보
    - scores: 해당 부동산의 점수 목록, 해당 점수를 계산한 추천 데이터로 연결됨
    """

    __tablename__ = "property"

    id = Column(INTEGER(unsigned=True), primary_key=True, index=True)
    region_id = Column(INTEGER(unsigned=True), ForeignKey("region.id"), nullable=False)
    name = Column(String(255), nullable=False)
    address = Column(String(255), nullable=False)
    sale_price_min = Column(BIGINT(unsigned=True))
    sale_price_max = Column(BIGINT(unsigned=True))
    deposit_price_min = Column(BIGINT(unsigned=True))
    deposit_price_max = Column(BIGINT(unsigned=True))
    latitude = Column(Numeric(10, 8), nullable=False)
    longitude = Column(Numeric(11, 8), nullable=False)
    latest_version_id = Column(INTEGER(unsigned=True), ForeignKey("version.id"), nullable=False)

    region = relationship("Region", back_populates="properties")
    latest_version = relationship("Version", back_populates="properties")
    scores = relationship("Score", back_populates="property")
