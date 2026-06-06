import enum
from typing import NamedTuple


class AppErrorCodeEnum(enum.Enum):
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    DUPLICATE_EMAIL = "DUPLICATE_EMAIL"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    FORBIDDEN = "FORBIDDEN"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    INCORRECT_CURRENT_PASSWORD = "INCORRECT_CURRENT_PASSWORD"
    REGION_ERROR = "REGION_ERROR"
    TASK_NOT_FOUND = "TASK_NOT_FOUND"
    HIGH_SCHOOL_ERROR = "HIGH_SCHOOL_ERROR"


class SchoolDistrictTypeMeta(NamedTuple):
    label: str
    description: str

class SchoolDistrictTypeEnum(str, enum.Enum):
    INTENSIVE = "INTENSIVE"
    BALANCED = "BALANCED"
    RELAXED = "RELAXED"

    @property
    def meta(self) -> SchoolDistrictTypeMeta:
        return _SCHOOL_DISTRICT_TYPE_META_MAP[self]


class InfrastructureTypeMeta(NamedTuple):
    emoji: str
    label: str
    description: str

class InfrastructureTypeEnum(str, enum.Enum):
    ELEMENTARY_SCHOOL = "ELEMENTARY_SCHOOL"
    MIDDLE_SCHOOL = "MIDDLE_SCHOOL"
    HIGH_SCHOOL = "HIGH_SCHOOL"
    SUBWAY_STATION = "SUBWAY_STATION"
    LARGE_HOSPITAL = "LARGE_HOSPITAL"
    LARGE_SUPERMARKET = "LARGE_SUPERMARKET"
    PARK = "PARK"

    @property
    def meta(self) -> InfrastructureTypeMeta:
        return _INFRASTRUCTURE_TYPE_META_MAP[self]


_SCHOOL_DISTRICT_TYPE_META_MAP = {
    SchoolDistrictTypeEnum.INTENSIVE: SchoolDistrictTypeMeta("학원가 밀집형", "풍부한 교육 인프라를 갖춘 동네"),
    SchoolDistrictTypeEnum.BALANCED: SchoolDistrictTypeMeta("균형 잡힌 학업형", "적당한 학업 분위기를 갖춘 균형 잡힌 동네"),
    SchoolDistrictTypeEnum.RELAXED: SchoolDistrictTypeMeta("여유로운 주거형", "학업 부담이 적고 여유롭게 생활하는 동네"),
}

_INFRASTRUCTURE_TYPE_META_MAP = {
    InfrastructureTypeEnum.ELEMENTARY_SCHOOL: InfrastructureTypeMeta("🎒", "초등학교", "초등학교 도보 거리"),
    InfrastructureTypeEnum.MIDDLE_SCHOOL: InfrastructureTypeMeta("📘", "중학교", "인근 중학교 도보 거리"),
    InfrastructureTypeEnum.HIGH_SCHOOL: InfrastructureTypeMeta("📚", "고등학교", "인근 고등학교 도보 거리"),
    InfrastructureTypeEnum.SUBWAY_STATION: InfrastructureTypeMeta("🚇", "지하철역", "가장 가까운 역까지 거리"),
    InfrastructureTypeEnum.LARGE_HOSPITAL: InfrastructureTypeMeta("🏥", "대형 병원", "종합병원·대학병원 거리"),
    InfrastructureTypeEnum.LARGE_SUPERMARKET: InfrastructureTypeMeta("🛒", "대형 마트", "마트·백화점 거리"),
    InfrastructureTypeEnum.PARK: InfrastructureTypeMeta("🌳", "공원·녹지", "근린공원·산책로 거리"),
}


APP_ERROR_CODES: list[str] = [x.value for x in AppErrorCodeEnum]

SCHOOL_DISTRICT_TYPE_MAP = { x.value: { "type": x.value, **x.meta._asdict() } for x in SchoolDistrictTypeEnum }
SCHOOL_DISTRICT_TYPES = list(SCHOOL_DISTRICT_TYPE_MAP.values())
SCHOOL_DISTRICT_TYPE_VALUES: list[str] = list(SCHOOL_DISTRICT_TYPE_MAP.keys())

INFRASTRUCTURE_TYPE_MAP = { x.value: { "type": x.value, **x.meta._asdict() } for x in InfrastructureTypeEnum }
INFRASTRUCTURE_TYPES = list(INFRASTRUCTURE_TYPE_MAP.values())
INFRASTRUCTURE_TYPE_VALUES: list[str] = list(INFRASTRUCTURE_TYPE_MAP.keys())
