from typing import TYPE_CHECKING
from sqlalchemy import Column, String
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import Mapped, relationship

from .base import Base


if TYPE_CHECKING:
    from . import Infrastructure, RecommendationInfrastructureTypePriority

class InfrastructureType(Base):
    """
    인프라 유형 모델
    - id: 인프라 유형 ID (unsigned, 자동 증가)
    - name: 인프라 유형 이름 (예: `"지하철역"`, `"대형병원"` 등)

    - infrastructures: 해당 인프라 유형에 속하는 인프라 목록
    - usage_in_recommendations: 해당 인프라 유형이 우선순위로 선택된 추천 목록
    """

    __tablename__ = "infrastructure_type"

    id = Column(TINYINT(unsigned=True), primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)

    infrastructures: Mapped[list["Infrastructure"]] = relationship("Infrastructure", back_populates="type", cascade="all, delete-orphan")
    usage_in_recommendations: Mapped[list["RecommendationInfrastructureTypePriority"]] = relationship("RecommendationInfrastructureTypePriority", back_populates="infrastructure_type", cascade="all, delete-orphan")

    def to_dict(self):
        """응답용 데이터로 변환 및 반환"""
        return {
            "id": self.id,
            "name": self.name,
        }
