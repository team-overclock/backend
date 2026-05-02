from typing import TYPE_CHECKING
from sqlalchemy import Column, ForeignKey, DateTime, String
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func
from cuid2 import cuid_wrapper

from .base import Base


if TYPE_CHECKING:
    from . import Region, UserRecommendation

create_cuid = cuid_wrapper()

class User(Base):
    """
    사용자 모델
    - id: 사용자 ID (CUID/CUID2 문자열, 다른 사용자 pk를 유추하지 못하도록 int/auto-increment 대신 사용함)
    - name: 사용자 이름
    - email: 사용자 이메일 (unique)
    - password: 사용자 비밀번호
    - region_id: 사용자가 선택한 기본 동네 ID (foreign key)
    - created_at: 계정 생성 시간
    - updated_at: 계정 정보 마지막 업데이트 시간

    - region: 사용자가 선택한 기본 동네 정보
    - recommendations: 사용자가 요청한 추천 목록
    """

    __tablename__ = "user"

    id = Column(String(36), primary_key=True, default=create_cuid)
    name = Column(String(50), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    password = Column(String(100), nullable=False)
    region_id = Column(INTEGER(unsigned=True), ForeignKey("region.id"))
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    region: Mapped["Region"] = relationship("Region", back_populates="users")
    recommendations: Mapped[list["UserRecommendation"]] = relationship("UserRecommendation", back_populates="user")
