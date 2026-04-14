from sqlalchemy import Column, ForeignKey, DateTime, String
from sqlalchemy.dialects.mysql import INTEGER, BIGINT
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class Recommendation(Base):
    """
    추천 모델, 다른 사용자가 같은 조합으로 추천을 요청할 경우 기존 추천 결과를 재사용하기 위해 지역 + 인프라 + 가격 조합에 대한 고유 해시값을 생성하여 관리
    - id: 추천 ID (unsigned, 자동 증가)
    - hash: 추천 고유 해시값, 지역 + 인프라 + 가격 기반으로 생성 (unique)
    - region_id: 추천 요청 시 선택한 지역 ID (foreign key)
    - sale_price_min: 추천 매매가 최솟값
    - sale_price_max: 추천 매매가 최댓값
    - deposit_price_min: 추천 전세가 최솟값
    - deposit_price_max: 추천 전세가 최댓값
    - created_at: 추천 생성 시간
    - finished_at: 추천 완료 시간 (추천 미완료 시 null)
    - version_id: 해당 추천에 사용된 데이터들의 버전 ID (foreign key), 최신 버전이 아니라면 업데이트 필요 (최신 데이터 기준으로 점수 다시 계산)

    - region: 지역 정보
    - version: 버전 정보
    - infrastructure_type_priorities: 추천 요청 시 선택한 인프라 및 우선순위 목록
    - scores: 해당 추천의 부동산에 대한 점수 목록
    - users: 해당 조합으로 추천을 요청한 사용한 사용자 목록
    """

    __tablename__ = "recommendation"

    id = Column(INTEGER(unsigned=True), primary_key=True, index=True)
    hash = Column(String(64), nullable=False, unique=True)
    region_id = Column(INTEGER(unsigned=True), ForeignKey("region.id"), nullable=False)
    sale_price_min = Column(BIGINT(unsigned=True))
    sale_price_max = Column(BIGINT(unsigned=True))
    deposit_price_min = Column(BIGINT(unsigned=True))
    deposit_price_max = Column(BIGINT(unsigned=True))
    created_at = Column(DateTime, nullable=False, default=func.now())
    finished_at = Column(DateTime)
    version_id = Column(INTEGER(unsigned=True), ForeignKey("version.id"), nullable=False)

    region = relationship("Region", back_populates="recommendations")
    version = relationship("Version", back_populates="recommendations")
    infrastructure_type_priorities = relationship("RecommendationInfraPriority", back_populates="recommendation")
    scores = relationship("Score", back_populates="recommendation")
    users = relationship("UserHasRecommendation", back_populates="recommendation")
