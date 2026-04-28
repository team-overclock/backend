from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.mysql import INTEGER, TINYINT
from sqlalchemy.orm import relationship

from .base import Base


class Region(Base):
    """
    지역 모델 (예: 서울특별시 강남구 역삼동)
    - id: 지역 ID (unsigned, 자동 증가)
    - parent_id: 상위 지역 ID (예: 서울특별시: `null`, 강남구: 서울특별시 ID, 역삼동: 강남구 ID)
    - depth: 깊이 (예: 서울특별시: `0`, 강남구: `1`, 역삼동: `2`)
    - name: 지역 이름 (예: `"서울특별시"`, `"강남구"`, `"역삼동"`)
    - full_name: 전체 지역 이름 (예: `"서울특별시 강남구 역삼동"`)
    - latest_version_id: 해당 지역 데이터의 버전 ID (foreign key)

    - parent: 상위 지역
    - children: 하위 지역 목록
    - latest_version: 버전 정보
    - properties: 해당 지역 내 부동산 목록
    - infrastructures: 해당 지역 내 인프라 목록
    - users: 해당 지역을 기본값으로 선택한 사용자 목록
    - recommendations: 해당 지역을 선택하여 진행한 추천 목록
    """

    __tablename__ = "region"

    id = Column(INTEGER(unsigned=True), primary_key=True, index=True)
    parent_id = Column(INTEGER(unsigned=True), ForeignKey("region.id"), nullable=True)
    depth = Column(TINYINT(unsigned=True), nullable=False)
    name = Column(String(80), nullable=False)
    full_name = Column(String(255), nullable=False)
    latest_version_id = Column(INTEGER(unsigned=True), ForeignKey("version.id"), nullable=False)

    parent = relationship("Region", remote_side=[id], back_populates="children")
    children = relationship("Region", back_populates="parent")
    latest_version = relationship("Version", back_populates="regions")
    properties = relationship("Property", back_populates="region")
    infrastructures = relationship("Infrastructure", back_populates="region")
    users = relationship("User", back_populates="region")
    recommendations = relationship("Recommendation", back_populates="region")
