from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import relationship

from .base import Base


class UserHasRecommendation(Base):
    """
    사용자-추천 매핑 모델
    - user_id: 사용자 ID (foreign key)
    - recommendation_id: 추천 ID (foreign key)

    - user: 사용자 정보
    - recommendation: 추천 정보
    """

    __tablename__ = "user_has_recommendation"

    user_id = Column(String(36), ForeignKey("user.id"), primary_key=True)
    recommendation_id = Column(INTEGER(unsigned=True), ForeignKey("recommendation.id"), primary_key=True)

    user = relationship("User", back_populates="recommendations")
    recommendation = relationship("Recommendation", back_populates="users")
