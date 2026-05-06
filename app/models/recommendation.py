from typing import TYPE_CHECKING
from sqlalchemy import Column, ForeignKey, DateTime, String
from sqlalchemy.dialects.mysql import INTEGER, BIGINT
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from .base import Base


if TYPE_CHECKING:
    from . import Region, RecommendationInfraPriority, PropertyScore, UserRecommendation, Version

class Recommendation(Base):
    """
    추천 모델, 다른 사용자가 같은 조합으로 추천을 요청할 경우 기존 추천 결과를 재사용하기 위해 동네 + 인프라 + 가격 조합에 대한 고유 해시값을 생성하여 관리
    - id: 추천 ID (unsigned, 자동 증가)
    - hash: 추천 고유 해시값, 동네 + 인프라 + 가격 기반으로 생성 (unique)
    - region_id: 추천 요청 시 선택한 동네 ID (foreign key)
    - sale_price_min: 추천 매매가 최솟값
    - sale_price_max: 추천 매매가 최댓값
    - deposit_price_min: 추천 전세가 최솟값
    - deposit_price_max: 추천 전세가 최댓값
    - created_at: 추천 생성 시간
    - finished_at: 추천 완료 시간 (추천 미완료 시 null)
    - version_id: 해당 추천에 사용된 데이터들의 버전 ID (foreign key), 최신 버전이 아니라면 업데이트 필요 (최신 데이터 기준으로 점수 다시 계산)

    - region: 동네 정보
    - infra_priorities: 추천 요청 시 선택한 인프라 우선순위 목록
    - property_scores: 해당 추천 결과인 부동산에 대한 점수 목록
    - request_users: 해당 조합으로 추천을 요청한 사용자 목록
    - version: 버전 정보
    """

    __tablename__ = "recommendation"

    id = Column(INTEGER(unsigned=True), primary_key=True, index=True)
    hash = Column(String(64), nullable=False, unique=True)
    region_id = Column(INTEGER(unsigned=True), ForeignKey("region.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    sale_price_min = Column(BIGINT(unsigned=True))
    sale_price_max = Column(BIGINT(unsigned=True))
    deposit_price_min = Column(BIGINT(unsigned=True))
    deposit_price_max = Column(BIGINT(unsigned=True))
    created_at = Column(DateTime, nullable=False, default=func.now())
    finished_at = Column(DateTime)
    version_id = Column(INTEGER(unsigned=True), ForeignKey("version.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False)

    region: Mapped["Region"] = relationship("Region", back_populates="recommendations")
    infra_priorities: Mapped[list["RecommendationInfraPriority"]] = relationship("RecommendationInfraPriority", back_populates="recommendation", cascade="all, delete-orphan")
    property_scores: Mapped[list["PropertyScore"]] = relationship("PropertyScore", back_populates="recommendation", cascade="all, delete-orphan")
    request_users: Mapped[list["UserRecommendation"]] = relationship("UserRecommendation", back_populates="recommendation", cascade="all, delete-orphan")
    version: Mapped["Version"] = relationship("Version", back_populates="recommendations")
