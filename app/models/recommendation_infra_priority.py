from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.mysql import INTEGER, TINYINT
from sqlalchemy.orm import relationship

from .base import Base


class RecommendationInfraPriority(Base):
    """
    추천별 인프라 우선순위 모델
    - recommendation_id: 연결된 추천 ID (foreign key)
    - infrastructure_type_id: 인프라 유형 ID (foreign key)
    - priority: 해당 추천에서 지정된 인프라의 우선순위 (unsigned, 값이 낮을수록 우선순위가 높음)

    - recommendation: 추천 정보
    - infrastructure_type: 인프라 유형 정보
    """

    __tablename__ = "recommendation_infra_priority"

    recommendation_id = Column(INTEGER(unsigned=True), ForeignKey("recommendation.id"), primary_key=True)
    infrastructure_type_id = Column(TINYINT(unsigned=True), ForeignKey("infrastructure_type.id"), primary_key=True)
    priority = Column(TINYINT(unsigned=True), nullable=False)

    recommendation = relationship("Recommendation", back_populates="infrastructure_type_priorities")
    infrastructure_type = relationship("InfrastructureType", back_populates="priorities")
