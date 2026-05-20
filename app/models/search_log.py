from typing import TYPE_CHECKING
from sqlalchemy import Column, ForeignKey, DateTime, String
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from .base import Base


if TYPE_CHECKING:
    from . import User, Recommendation

class SearchLog(Base):
    """
    검색 로그 모델
    - user_id: 사용자 ID (foreign key)
    - recommendation_id: 추천 ID (foreign key)
    - task_id: 추천 요청을 식별하는 고유한 문자열 (예: UUID 또는 hash)
    - name: 해당 추천 요청 조합에 대해 사용자가 지정한 이름 (예: "내 첫 번째 추천")
    - requested_at: 추천 요청 시간
    - last_viewed_at: 추천 결과 마지막 조회 시간

    - user: 사용자 정보
    """

    __tablename__ = "search_log"

    user_id = Column(INTEGER(unsigned=True), ForeignKey("user.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    recommendation_id = Column(INTEGER(unsigned=True), ForeignKey("recommendation.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    task_id = Column(String(64), nullable=False)
    name = Column(String(100))
    requested_at = Column(DateTime, nullable=False, default=func.now())
    last_viewed_at = Column(DateTime)

    user: Mapped["User"] = relationship("User", back_populates="search_logs")
    recommendation: Mapped["Recommendation"] = relationship("Recommendation", back_populates="users")
