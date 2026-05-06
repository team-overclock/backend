from typing import TYPE_CHECKING
from sqlalchemy import Column, ForeignKey, DateTime, String
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from .base import Base


if TYPE_CHECKING:
    from . import User, Recommendation

class UserRecommendation(Base):
    """
    사용자-추천 매핑 모델
    - user_id: 사용자 ID (foreign key)
    - recommendation_id: 추천 ID (foreign key)
    - name: 사용자가 해당 추천 조합에 대해 지정한 이름 (예: "내 첫 번째 추천")
    - requested_at: 사용자가 해당 추천을 요청한 시간

    - user: 사용자 정보
    - recommendation: 추천 정보
    """

    __tablename__ = "user_recommendation"

    user_id = Column(String(36), ForeignKey("user.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    recommendation_id = Column(INTEGER(unsigned=True), ForeignKey("recommendation.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    name = Column(String(100))
    requested_at = Column(DateTime, nullable=False, default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="recommendations")
    recommendation: Mapped["Recommendation"] = relationship("Recommendation", back_populates="request_users")
