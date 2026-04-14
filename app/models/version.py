from sqlalchemy import Column, DateTime, Boolean
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class Version(Base):
    """
    데이터 버전 정보을 저장하는 모델

    추후 최신화 된 데이터를 적용할 때 사라지거나 변경된 데이터들을 삭제하지 않고 관리하기 위해 사용됨

    - id: 버전 ID (unsigned, 자동 증가)
    - registered_at: insert 시간, (기본값: 삽입 시간)
    - is_active: 현재 활성화된 버전인지 여부 (기본값 `True`)

    - regions: 해당 버전에 해당하는 지역 목록
    - properties: 해당 버전에 해당하는 부동산 목록
    - infrastructures: 해당 버전에 해당하는 인프라 목록
    - recommendations: 해당 버전의 데이터들로 생성된 추천 목록
    """

    __tablename__ = "version"

    id = Column(INTEGER(unsigned=True), primary_key=True, index=True)
    registered_at = Column(DateTime, nullable=False, default=func.now())
    is_active = Column(Boolean, nullable=False, default=True)

    regions = relationship("Region", back_populates="latest_version")
    properties = relationship("Property", back_populates="latest_version")
    infrastructures = relationship("Infrastructure", back_populates="latest_version")
    recommendations = relationship("Recommendation", back_populates="version")
