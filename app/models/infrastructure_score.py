from typing import TYPE_CHECKING
from sqlalchemy import Column, ForeignKey, ForeignKeyConstraint
from sqlalchemy.dialects.mysql import INTEGER, DECIMAL
from sqlalchemy.orm import Mapped, relationship

from .base import Base


if TYPE_CHECKING:
    from . import Infrastructure, PropertyScore

class InfrastructureScore(Base):
    """
    추천-인프라 점수 모델
    - recommendation_id: 추천 ID (foreign key)
    - property_id: 부동산 ID (foreign key)
    - infrastructure_id: 인프라 ID (foreign key)
    - score: 해당 추천-인프라 조합에 대한 점수 (0~100 사이의 소수점 2자리)

    - property_score: 추천-부동산 점수 정보
    - infrastructure: 인프라 정보
    """

    __tablename__ = "infrastructure_score"

    __table_args__ = (
        ForeignKeyConstraint(
            ["recommendation_id", "property_id"],
            ["property_score.recommendation_id", "property_score.property_id"],
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
    )

    recommendation_id = Column(INTEGER(unsigned=True), primary_key=True)
    property_id = Column(INTEGER(unsigned=True), primary_key=True)
    infrastructure_id = Column(INTEGER(unsigned=True), ForeignKey("infrastructure.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    score = Column(DECIMAL(5, 2, unsigned=True), nullable=False)

    property_score: Mapped["PropertyScore"] = relationship("PropertyScore", back_populates="infrastructure_scores")
    infrastructure: Mapped["Infrastructure"] = relationship("Infrastructure", back_populates="infrastructure_scores")
