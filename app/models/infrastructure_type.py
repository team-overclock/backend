from sqlalchemy import Column, String
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import relationship

from .base import Base


class InfrastructureType(Base):
    """
    인프라 유형 모델
    - id: 인프라 유형 ID (unsigned, 자동 증가)
    - name: 인프라 유형 이름 (예: `"지하철역"`, `"대형병원"` 등)

    - infrastructures: 해당 인프라 유형에 속하는 인프라 목록
    - priorities: 해당 인프라 유형이 추천에 사용된 우선순위 목록, 추천 데이터로 연결됨
    """

    __tablename__ = "infrastructure_type"

    id = Column(TINYINT(unsigned=True), primary_key=True, index=True)
    name = Column(String(100), nullable=False)

    infrastructures = relationship("Infrastructure", back_populates="type")
    priorities = relationship("RecommendationInfraPriority", back_populates="infrastructure_type")
