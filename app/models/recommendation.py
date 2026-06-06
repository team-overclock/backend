from typing import TYPE_CHECKING
from sqlalchemy import Column, DateTime, JSON, String
from sqlalchemy.dialects.mysql import INTEGER, BIGINT
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from .base import Base


if TYPE_CHECKING:
    from ..core.enums import InfrastructureTypeEnum
    from . import User, SearchLog

class Recommendation(Base):
    """
    추천 모델
    - id: 추천의 고유 ID (primary key)
    - task_id: 추천 요청을 식별하는 고유한 문자열 (예: UUID 또는 hash)
    - region: 동네명
    - infrastructure_priorities: 인프라 우선순위 (예: ["초등학교", "공원·녹지", "대형마트"])
    - sale_price_min: 희망 매매 최소 가격
    - sale_price_max: 희망 매매 최대 가격
    - jeonse_price_min: 희망 전세 최소 가격
    - jeonse_price_max: 희망 전세 최대 가격
    - top_properties: 시스템이 해당 추천 조합에 대해 생성한 상위 N개 추천 결과
    - created_at: 추천 최초 생성 시간
    - finished_at: 추천 최초 완료 시간
    - updated_at: 추천 정보 마지막 업데이트 시간
    - failed_at: 추천 로직 실행 중 에러 발생 시간

    - users: 해당 조합으로 추천을 요청한 사용자 목록
    """

    __tablename__ = "recommendation"

    id = Column(INTEGER(unsigned=True), primary_key=True, index=True)
    task_id = Column(String(64), unique=True, nullable=False)
    region = Column(String(255))
    infrastructure_priorities = Column(JSON, nullable=False)
    sale_price_min = Column(BIGINT(unsigned=True))
    sale_price_max = Column(BIGINT(unsigned=True))
    jeonse_price_min = Column(BIGINT(unsigned=True))
    jeonse_price_max = Column(BIGINT(unsigned=True))
    top_properties = Column(JSON)
    school_district_types = Column(JSON)
    high_school_ids = Column(JSON)
    created_at = Column(DateTime, nullable=False, default=func.now())
    finished_at = Column(DateTime)
    updated_at = Column(DateTime)
    failed_at = Column(DateTime)

    users: Mapped[list["SearchLog"]] = relationship("SearchLog", back_populates="recommendation", cascade="all, delete-orphan")

    def add_user(
        self,
        user: "User",
        name: str | None = None,
    ):
        """
        해당 추천을 요청한 사용자 추가. 커밋은 하지 않음.
        - name: 사용자 지정 추천 별칭 (선택 사항)
        """
        isn = SearchLog(name=name, user=user)
        self.users.append(isn)
        return isn

    def set_infrastructure_priorities(
        self,
        infrastructure_types: list["InfrastructureTypeEnum | str"],
    ) -> list[str]:
        """
        해당 추천의 인프라 유형 우선순위 설정. 커밋은 하지 않음.
        """
        self.infrastructure_priorities = [x.value if hasattr(x, "value") else x for x in infrastructure_types]
        return self.infrastructure_priorities
