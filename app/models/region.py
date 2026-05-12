from typing import TYPE_CHECKING
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.mysql import INTEGER, TINYINT
from sqlalchemy.orm import Mapped, relationship

from .base import Base


if TYPE_CHECKING:
    from . import Property, Infrastructure, User, Recommendation, Version

class Region(Base):
    """
    동네 모델 (예: 서울특별시 강남구 역삼동)
    - id: 동네 ID (unsigned, 자동 증가)
    - parent_id: 상위 동네 ID (예: 서울특별시: `null`, 강남구: 서울특별시 ID, 역삼동: 강남구 ID)
    - depth: 깊이 (예: 서울특별시: `0`, 강남구: `1`, 역삼동: `2`)
    - name: 동네 이름 (예: `"서울특별시"`, `"강남구"`, `"역삼동"`)
    - full_name: 동네 전체 이름 (예: `"서울특별시 강남구 역삼동"`)
    - version_id: 해당 동네 데이터의 버전 ID (foreign key)

    - parent: 상위 동네
    - children: 하위 동네 목록
    - properties: 해당 동네 내 부동산 목록
    - infrastructures: 해당 동네 내 인프라 목록
    - users: 해당 동네을 기본값으로 선택한 사용자 목록
    - recommendations: 해당 동네을 선택하여 진행한 추천 목록
    - version: 버전 정보
    """

    __tablename__ = "region"

    id = Column(INTEGER(unsigned=True), primary_key=True, index=True)
    parent_id = Column(INTEGER(unsigned=True), ForeignKey("region.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=True)
    depth = Column(TINYINT(unsigned=True), nullable=False)
    name = Column(String(80), nullable=False)
    full_name = Column(String(255), nullable=False)
    version_id = Column(INTEGER(unsigned=True), ForeignKey("version.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False)

    parent: Mapped["Region"] = relationship("Region", remote_side=[id], back_populates="children")
    children: Mapped[list["Region"]] = relationship("Region", back_populates="parent", cascade="all, delete-orphan")
    properties: Mapped[list["Property"]] = relationship("Property", back_populates="region", cascade="all, delete-orphan")
    infrastructures: Mapped[list["Infrastructure"]] = relationship("Infrastructure", back_populates="region", cascade="all, delete-orphan")
    users: Mapped[list["User"]] = relationship("User", back_populates="region", cascade="save-update, merge")
    recommendations: Mapped[list["Recommendation"]] = relationship("Recommendation", back_populates="region", cascade="all, delete-orphan")
    version: Mapped["Version"] = relationship("Version", back_populates="regions")

    def to_dict(self):
        """id 및 name(full_name)만 포함하는 딕셔너리를 반환"""
        return {
            "id": self.id,
            "name": self.full_name,
        }
