from typing import TYPE_CHECKING
from sqlalchemy import Column, DateTime, Boolean, String
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from .base import Base


if TYPE_CHECKING:
    from . import Region, Property, Infrastructure, Recommendation

class Version(Base):
    """
    데이터 버전 정보을 저장하는 모델

    추후 최신화 된 데이터를 적용할 때 사라지거나 변경된 데이터들을 삭제하지 않고 관리하기 위해 사용됨

    - id: 버전 ID (unsigned, 자동 증가)
    - hash: 데이터 해시값 (데이터 변경 여부 판단용)
    - registered_at: insert 시간, (기본값: 삽입 시간)
    - is_active: 현재 활성화된 버전인지 여부 (기본값 `True`)

    - regions: 해당 버전에 해당하는 동네 목록
    - properties: 해당 버전에 해당하는 부동산 목록
    - infrastructures: 해당 버전에 해당하는 인프라 목록
    - recommendations: 해당 버전의 데이터들로 생성된 추천 목록
    """

    __tablename__ = "version"

    id = Column(INTEGER(unsigned=True), primary_key=True, index=True)
    hash = Column(String(64), nullable=True, unique=True)
    registered_at = Column(DateTime, nullable=False, default=func.now())
    is_active = Column(Boolean, nullable=False, default=True)

    regions: Mapped[list["Region"]] = relationship("Region", back_populates="version", cascade="save-update, merge")
    properties: Mapped[list["Property"]] = relationship("Property", back_populates="version", cascade="save-update, merge")
    infrastructures: Mapped[list["Infrastructure"]] = relationship("Infrastructure", back_populates="version", cascade="save-update, merge")
    recommendations: Mapped[list["Recommendation"]] = relationship("Recommendation", back_populates="version", cascade="save-update, merge")
