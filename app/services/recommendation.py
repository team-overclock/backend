import json
import hashlib
from enum import Enum

from ..core.enums import SchoolDistrictTypeEnum, InfrastructureTypeEnum


def generate_recommendation_task_id(
    region_id: int | None,
    infrastructure_types: list[InfrastructureTypeEnum],
    high_school_ids: list[int] | None,
    school_district_types: list[SchoolDistrictTypeEnum],
    sale_price_min: int | None,
    sale_price_max: int | None,
    jeonse_price_min: int | None,
    jeonse_price_max: int | None,
):
    """
    사용자에게 입력받은 동네, 인프라 유형 및 우선순위, 매매/전세 가격 범위를 기반으로 고유한 hash(task_id) 생성
    """
    def _serialize_val(val):
        if isinstance(val, Enum):
            return val.value
        if isinstance(val, list):
            return [_serialize_val(item) for item in val]
        return val

    # None이 아닌 값들만 순서대로 수집
    params = {
        "region_id": region_id,
        "infrastructure_types": infrastructure_types,
        "high_school_ids": high_school_ids,
        "school_district_types": school_district_types,
        "sale_price_min": sale_price_min,
        "sale_price_max": sale_price_max,
        "jeonse_price_min": jeonse_price_min,
        "jeonse_price_max": jeonse_price_max,
    }

    values = {name: _serialize_val(val) for name, val in params.items() if val is not None}

    # 입력된 순서를 유지하면서 JSON 직렬화 후 SHA256 hash 생성
    hash_input = json.dumps(values, ensure_ascii=False, sort_keys=False)
    task_id = hashlib.sha256(hash_input.encode()).hexdigest()
    return task_id
