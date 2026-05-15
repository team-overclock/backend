from typing import TYPE_CHECKING
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.mysql import INTEGER, DECIMAL
from sqlalchemy.orm import Mapped, relationship

from .base import Base


if TYPE_CHECKING:
    from . import Recommendation, Property, Infrastructure

class RecommendationPropertyInfrastructureScore(Base):
    """
    추천-부동산-인프라 점수 모델
    - recommendation_id: 추천 ID (foreign key)
    - property_id: 부동산 ID (foreign key)
    - infrastructure_id: 인프라 ID (foreign key)
    - score: 추천 내 부동산-인프라 조합에 대한 가중치가 적용된 점수

    - recommendation: 추천 정보
    - property: 부동산 정보
    - infrastructure: 인프라 정보
    """

    __tablename__ = "recommendation_property_infrastructure_score"

    recommendation_id = Column(INTEGER(unsigned=True), ForeignKey("recommendation.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    property_id = Column(INTEGER(unsigned=True), ForeignKey("property.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    infrastructure_id = Column(INTEGER(unsigned=True), ForeignKey("infrastructure.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    score = Column(DECIMAL(5, 2, unsigned=True), nullable=False)

    recommendation: Mapped["Recommendation"] = relationship("Recommendation", back_populates="property_infrastructure_scores")
    property: Mapped["Property"] = relationship("Property", back_populates="recommendation_infrastructure_scores")
    infrastructure: Mapped["Infrastructure"] = relationship("Infrastructure", back_populates="recommendation_infrastructure_scores")
