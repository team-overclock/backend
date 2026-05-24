import enum
from typing import NamedTuple
from pydantic import model_serializer


class AppErrorCodeEnum(enum.Enum):
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    DUPLICATE_EMAIL = "DUPLICATE_EMAIL"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    FORBIDDEN = "FORBIDDEN"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    REGION_ERROR = "REGION_ERROR"
    INFRASTRUCTURE_TYPE_ERROR = "INFRASTRUCTURE_TYPE_ERROR"
    TASK_ID_TOO_SHORT = "TASK_ID_TOO_SHORT"
    

class InfrastructureTypeMeta(NamedTuple):
    emoji: str
    label: str
    description: str

class InfrastructureTypeEnum(enum.Enum):
    ELEMENTARY_SCHOOL = ("ELEMENTARY_SCHOOL", "🎒", "초등학교", "초등학교 도보 거리")
    MIDDLE_SCHOOL = ("MIDDLE_SCHOOL", "📘", "중학교", "인근 중학교 도보 거리")
    HIGH_SCHOOL = ("HIGH_SCHOOL", "📚", "고등학교", "인근 고등학교 도보 거리")
    SUBWAY_STATION = ("SUBWAY_STATION", "🚇", "지하철역", "가장 가까운 역까지 거리")
    LARGE_HOSPITAL = ("LARGE_HOSPITAL", "🏥", "대형 병원", "종합병원·대학병원 거리")
    LARGE_SUPERMARKET = ("LARGE_SUPERMARKET", "🛒", "대형 마트", "마트·백화점 거리")
    PARK = ("PARK", "🌳", "공원·녹지", "근린공원·산책로 거리")

    def __new__(self, value: str, emoji: str, label: str, description: str):
        obj = object.__new__(self)
        obj._value_ = value
        obj._meta_data = InfrastructureTypeMeta(emoji=emoji, label=label, description=description)
        return obj

    @property
    def meta(self) -> InfrastructureTypeMeta:
        return self._meta_data

    @model_serializer
    def serialize_as_value(self) -> str:
        return self.value


APP_ERROR_CODES: list[str] = [x.value for x in AppErrorCodeEnum]

INFRASTRUCTURE_TYPE_MAP = { x.value: { "type": x.value, **x.meta._asdict() } for x in InfrastructureTypeEnum }
INFRASTRUCTURE_TYPES = list(INFRASTRUCTURE_TYPE_MAP.values())
INFRASTRUCTURE_TYPE_VALUES: list[str] = list(INFRASTRUCTURE_TYPE_MAP.keys())
