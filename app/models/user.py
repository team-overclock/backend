from typing import TYPE_CHECKING
from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func
from cuid2 import cuid_wrapper

from ..core.security import hash_password, verify_password
from .base import Base


if TYPE_CHECKING:
    from . import SearchLog

create_cuid = cuid_wrapper()

class User(Base):
    """
    사용자 모델, 패스워드 자동 암호화 및 검증 기능 포함
    - id: 사용자 ID (내부용, unsigned, 자동 증가)
    - cuid: 사용자 CUID (외부용, 다른 사용자 unique ID를 유추하지 못하도록 id 대신 cuid를 외부용으로 사용함)
    - name: 사용자 이름
    - email: 사용자 이메일 (unique)
    - _password: 대신 자동 암호화를 지원하는 password 프로퍼티로 접근 권장
    - created_at: 계정 생성 시간
    - updated_at: 계정 정보 마지막 업데이트 시간

    - search_logs: 사용자가 요청한 검색 로그 목록
    """

    __tablename__ = "user"

    id = Column(INTEGER(unsigned=True), primary_key=True, index=True)
    cuid = Column(String(36), nullable=False, unique=True, default=create_cuid)
    name = Column(String(50), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    _password = Column("password", String(100), nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    search_logs: Mapped[list["SearchLog"]] = relationship("SearchLog", back_populates="user", cascade="all, delete-orphan")

    @property
    def password(self) -> str:
        """암호화된 사용자 비밀번호"""
        return self._password

    @password.setter
    def password(self, value):
        """사용자 비밀번호를 암호화하여 저장"""
        # 비밀번호 암호화! (보안 전공자의 자존심)
        self._password = hash_password(value)

    def verify_password(self, plain_password: str):
        """입력된 비밀번호와 DB의 해시값 비교"""
        return verify_password(self.password, plain_password)
