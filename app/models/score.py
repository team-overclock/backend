from typing import TYPE_CHECKING
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.mysql import INTEGER, DECIMAL
from sqlalchemy.orm import Mapped, relationship

from .base import Base


if TYPE_CHECKING:
    from . import Recommendation, Property

class Score(Base):
    """
    추천-부동산 점수 모델
    - recommendation_id: 추천 ID (foreign key)
    - property_id: 부동산 ID (foreign key)
    - score: 해당 추천-부동산 조합에 대한 점수 (0~100 사이의 소수점 2자리)

    - recommendation: 추천 정보
    - property: 부동산 정보
    """

    __tablename__ = "score"

    recommendation_id = Column(INTEGER(unsigned=True), ForeignKey("recommendation.id"), primary_key=True)
    property_id = Column(INTEGER(unsigned=True), ForeignKey("property.id"), primary_key=True)
    score = Column(DECIMAL(5, 2, unsigned=True), nullable=False)

    recommendation: Mapped["Recommendation"] = relationship("Recommendation", back_populates="scores")
    property: Mapped["Property"] = relationship("Property", back_populates="recommendation_entries")
