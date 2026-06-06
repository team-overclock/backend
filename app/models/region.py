from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Column, DateTime, String
from sqlalchemy.dialects.mysql import INTEGER, TINYINT
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from .base import Base


if TYPE_CHECKING:
    from . import Property


class Region(Base):
    """
    동네 모델 (예: 서울특별시 강남구 역삼동)
    - id: 동네 ID (unsigned, 자동 증가)
    - source_id: 원본 데이터에서의 동네 고유 ID (법정동코드)
    - parent_id: 상위 동네 ID (예: 역삼동의 parent_id는 강남구의 id)
    - depth: 깊이 (예: 서울특별시: `0`, 강남구: `1`, 역삼동: `2`)
    - name: 동네 이름 (예: `"서울특별시 강남구 역삼동"`)
    - academy_count: 해당 동네에 위치한 학원 수
    - updated_at: 마지막 업데이트 시각
    - deleted_at: 삭제 시각 (soft delete)

    - parent: 상위 동네 정보
    - children: 하위 동네 정보 목록
    - properties: 해당 동네에 위치한 건물 정보 목록
    """

    __tablename__ = "region"

    id = Column(INTEGER(unsigned=True), primary_key=True, index=True)
    source_id = Column(String(100), nullable=False, unique=True)
    parent_id = Column(INTEGER(unsigned=True), ForeignKey("region.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=True)
    depth = Column(TINYINT(unsigned=True), nullable=False)
    name = Column(String(255), unique=True, nullable=False)
    academy_count = Column(INTEGER(unsigned=True), nullable=False, default=0)
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime)

    parent: Mapped["Region"] = relationship("Region", remote_side=[id], back_populates="children")
    children: Mapped[list["Region"]] = relationship("Region", back_populates="parent", cascade="all, delete-orphan")
    properties: Mapped[list["Property"]] = relationship("Property", back_populates="region", cascade="all, delete-orphan")
