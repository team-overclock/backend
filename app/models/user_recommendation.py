from typing import TYPE_CHECKING
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import Mapped, relationship

from .base import Base


if TYPE_CHECKING:
    from . import User, Recommendation

class UserRecommendation(Base):
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

    user: Mapped["User"] = relationship("User", back_populates="recommendations")
    recommendation: Mapped["Recommendation"] = relationship("Recommendation", back_populates="request_users")
