#!/usr/bin/with-contenv python3

import re
import os
import sys
import hashlib
from decimal import Decimal
from pathlib import Path
from typing import Any
from sqlalchemy.orm import Session

# backend 디렉터리를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import SessionLocal, engine
from app.models import Base, Version, Region, InfrastructureType, Infrastructure, Property

from scripts.common import parse_price_to_int, parse_decimal, run_with_progress
from scripts.csv_parser import get_csv_files, read_csv_file
from scripts.geo import get_address_from_coords


PROGRESS_PRINT = 100
DB_BATCH_SIZE = 1000

INFRA_TYPES = [
    "고등학교",
    "공원·녹지",
    "대형마트",
    "대형병원",
    "지하철역",
    "초등학교",
]

INFRA_FILE_MAP: dict[str, tuple[str, str]] = {
    "elementary": ("초등학교", "ASGN_POSBL_ELESCH_NM"),
    "highschool": ("고등학교", "NGHB_EDU_FCLTY"),
    "green": ("공원·녹지", "NGHB_PRKGRNLND_SPCE"),
    "market": ("대형마트", "NGHB_LGZ_DISTB_FCLTY"),
    "hospital": ("대형병원", "NGHB_LGZ_MLFLT_NM"),
    "transport": ("지하철역", "NGHB_SUBWAY_STATN"),
}


def usage():
    print("사용법: python insert_data.py")
    print("  - data 폴더 내 *.csv 파일 데이터를 데이터베이스에 삽입합니다.")


def normalize_dong_for_region(dong_name: str) -> str:
    """
    Region 삽입용 동 이름 정규화
    - 숫자 및 suffix 제거 (예: 성수동1가 -> 성수동, 상도1동 -> 상도동)
    """

    return re.sub(r"\d+.*", "동" if re.search(r"\d+동", dong_name) else "", dong_name)


def normalize_lotno(lotno: str) -> str:
    """
    번지 표기를 정규화합니다.
    - '번지' 제거
    - 공백 제거
    - 각 숫자 블록의 앞 0 제거
    """

    raw = (lotno or "").strip().replace("번지", "").replace(" ", "")
    if not raw:
        return ""

    parts = raw.split("-")

    def _clean_num(p: str) -> str:
        if p.isdigit():
            return str(int(p))
        return p

    return "-".join(_clean_num(p) for p in parts)


def normalize_price_range(min_value: int | None, max_value: int | None) -> tuple[int, int] | tuple[None, None]:
    """가격 범위를 정규화합니다.

    규칙:
    - min/max 둘 다 None 이면 유지
    - 둘 중 하나라도 None 이거나 0 이하이면 둘 다 None
    - 둘 다 양수면 (min, max) 순서 보정
    """

    if min_value is None and max_value is None:
        return None, None
    elif min_value is None:
        return max_value, max_value
    elif max_value is None:
        return min_value, min_value

    sort = sorted([min_value, max_value])
    return sort[0], sort[1]


def generate_files_hash(file_names: list[str]) -> str:
    """
    파일명 목록으로 해시를 생성합니다.

    Args:
        file_names (list[str]): 파일명 목록

    Returns:
        str: SHA-256 해시 문자열
    """

    normalized = ",".join(sorted(file_names))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def get_or_create_version(db: Session, hash: str):
    """
    해시로 Version 존재 여부를 확인하고, 없으면 새로 생성합니다.

    Args:
        db: DB 세션
        hash (str): 생성할/조회할 해시 문자열

    Returns:
        tuple[Version, bool]: (Version 인스턴스, 생성되었으면 True, 기존이면 False)
    """

    existing = db.query(Version).filter(Version.hash == hash).first()
    if existing:
        return existing, False

    v = Version(hash=hash)
    db.add(v)
    db.flush()
    return v, True


def insert_infra_types(db: Session) -> None:
    """
    인프라 타입을 데이터베이스에 삽입합니다.
     - 이미 존재하는 타입은 건너뜁니다.
    """

    print(f"인프라 타입 추가 중...")
    infras = {}
    stored_infra_types = [x.name for x in db.query(InfrastructureType).all()]
    for infra in INFRA_TYPES:
        if infra not in stored_infra_types:
            infras[infra] = InfrastructureType(name=infra)
            db.add(infras[infra])
    db.flush()


def build_infra_type_id_map(db: Session) -> dict[str, int]:
    return {x.name: x.id for x in db.query(InfrastructureType).all()}


def get_or_create_region_depth0(
    db: Session, version_id: int, sido_name: str
) -> Region:
    """
    depth 0 지역 (시도) 생성/조회 후 버전 업데이트
    """
    existing = (
        db.query(Region)
        .filter(Region.depth == 0, Region.parent_id == None, Region.name == sido_name)
        .first()
    )
    if existing is None:
        r = Region(
            parent_id=None,
            depth=0,
            name=sido_name,
            full_name=sido_name,
            version_id=version_id,
        )
        db.add(r)
        return r
    else:
        existing.version_id = version_id
        return existing


def get_or_create_region_depth1(
    db: Session, version_id: int, parent_id: int, sigungu_name: str, sido_name: str
) -> Region:
    """
    depth 1 지역 (시군구) 생성/조회 후 버전 업데이트
    """
    existing = (
        db.query(Region)
        .filter(Region.depth == 1, Region.parent_id == parent_id, Region.name == sigungu_name)
        .first()
    )
    if existing is None:
        full_name = f"{sido_name} {sigungu_name}"
        r = Region(
            parent_id=parent_id,
            depth=1,
            name=sigungu_name,
            full_name=full_name,
            version_id=version_id,
        )
        db.add(r)
        return r
    else:
        existing.version_id = version_id
        return existing


def get_or_create_region_depth2(
    db: Session,
    version_id: int,
    parent_id: int,
    emd_normalized: str,
    sido_name: str,
    sigungu_name: str,
) -> Region:
    """
    depth 2 지역 (읍면동) 생성/조회 후 버전 업데이트
    """
    existing = (
        db.query(Region)
        .filter(Region.depth == 2, Region.parent_id == parent_id, Region.name == emd_normalized)
        .first()
    )
    if existing is None:
        full_name = f"{sido_name} {sigungu_name} {emd_normalized}"
        r = Region(
            parent_id=parent_id,
            depth=2,
            name=emd_normalized,
            full_name=full_name,
            version_id=version_id,
        )
        db.add(r)
        return r
    else:
        existing.version_id = version_id
        return existing


def get_or_create_region(
    db: Session,
    version_id: int,
    sido_name: str,
    sigungu_name: str,
    emd_name: str,
) -> Region | None:
    """
    서울 데이터 기준으로 3단계 Region을 보장합니다.
    - depth 0: 시도
    - depth 1: 시군구
    - depth 2: 읍면동 (N가 등 제거)
    
    기존 데이터가 있으면 버전만 업데이트합니다.
    """

    if sido_name != "서울특별시":
        return None

    dong_for_region = normalize_dong_for_region(emd_name)
    r0 = get_or_create_region_depth0(db, version_id, sido_name)
    r1 = get_or_create_region_depth1(db, version_id, r0.id, sigungu_name, sido_name)
    r2 = get_or_create_region_depth2(
        db, version_id, r1.id, dong_for_region, sido_name, sigungu_name
    )
    return r2


def parse_sgg_field(value: str) -> tuple[str, str, str] | None:
    """'서울특별시 강남구 도곡동' -> (시도, 시군구, 동)"""

    parts = (value or "").strip().split()
    if len(parts) < 3:
        return None
    sido = parts[0]
    sigungu = parts[1]
    emd = " ".join(parts[2:]).strip()
    return sido, sigungu, emd


def parse_lnno_adres(value: str) -> tuple[str, str, str, str] | None:
    """
    '서울특별시 종로구 당주동 100' 같은 `LNNO_ADRES`에서
    (sido, sigungu, emd_raw, lotno) 를 반환합니다.
    """
    if not value:
        return None
    parsed = parse_sgg_field(value)
    if parsed is None:
        return None
    sido, sigungu, emd_raw = parsed
    # emd_raw may contain the lotno at the end, e.g. '당주동 100' or '숭인동 204-11'
    parts = emd_raw.split()
    if len(parts) >= 2 and re.search(r"\d", parts[-1]):
        lotno = normalize_lotno(parts[-1])
        emd = " ".join(parts[:-1])
    else:
        lotno = ""
        emd = emd_raw
    return sido, sigungu, emd, lotno


def collect_address_area_range_from_transact(csv_files: list[str]) -> dict[tuple[str, str, str, str], tuple[Decimal, Decimal]]:
    """
    단지별직거래가격*.csv에서 주소별(시도,시군구,동,번지) 평수(min,max)를 수집합니다.
    SMOEU 컬럼(㎡)를 평으로 변환합니다.
    반환: {(sido,sigungu,emd,lotno): (min_pyeong, max_pyeong)} (Decimal)
    """
    result: dict[tuple[str, str, str, str], tuple[Decimal, Decimal]] = {}
    print("단지별 직거래 평수 집계 중...")
    for csv_file in csv_files:
        name = Path(csv_file).name
        if "단지별직거래가격" not in name:
            continue
        rows = read_csv_file(csv_file)
        total = len(rows)
        def run(idx: int):
            row = rows[idx]
            sido = row.get("SIDO_NM")
            sigungu = row.get("SIGNGU_NM")
            emd = row.get("EMD_NM")
            lotno = row.get("LTNO_NM")
            if not (sido and sigungu and emd and lotno):
                return
            lotno = normalize_lotno(lotno)
            if sido != "서울특별시" or not lotno:
                return
            area_m2 = parse_decimal(row.get("SMOEU"))
            if area_m2 is None or area_m2 <= 0:
                return
            pyeong = area_m2 / Decimal("3.305785")
            key = (sido, sigungu, emd, lotno)
            if key not in result:
                result[key] = (pyeong, pyeong)
            else:
                cur_min, cur_max = result[key]
                if pyeong < cur_min:
                    cur_min = pyeong
                if pyeong > cur_max:
                    cur_max = pyeong
                result[key] = (cur_min, cur_max)
        run_with_progress(f"[{name}]", total, run, interval=PROGRESS_PRINT)

    return result


def collect_address_price_per_pyeong_from_complex(csv_files: list[str]) -> dict[tuple[str, str, str, str], tuple[Decimal, Decimal]]:
    """
    단지별전세가격*.csv에서 주소별(시도,시군구,동,번지) 평당 전세가격(PCPP) min/max를 수집합니다.
    PCPP은 파일에 제공된 수치를 그대로 Decimal로 읽습니다.
    반환: {(sido,sigungu,emd,lotno): (min_pcpp, max_pcpp)} (Decimal)
    """
    result: dict[tuple[str, str, str, str], tuple[Decimal, Decimal]] = {}
    print("단지별 전세 평단가 집계 중...")
    for csv_file in csv_files:
        name = Path(csv_file).name
        if "단지별전세가격" not in name:
            continue
        rows = read_csv_file(csv_file)
        total = len(rows)
        def run(idx: int):
            row = rows[idx]
            addr = (row.get("LNNO_ADRES") or "").strip()
            parsed = parse_lnno_adres(addr)
            if parsed is None:
                return
            sido, sigungu, emd, lotno = parsed
            if sido != "서울특별시" or not lotno:
                return
            pcpp = parse_decimal(row.get("PCPP"))
            if pcpp is None or pcpp <= 0:
                return
            key = (sido, sigungu, emd, lotno)
            if key not in result:
                result[key] = (pcpp, pcpp)
            else:
                cur_min, cur_max = result[key]
                if pcpp < cur_min:
                    cur_min = pcpp
                if pcpp > cur_max:
                    cur_max = pcpp
                result[key] = (cur_min, cur_max)
        run_with_progress(f"[{name}]", total, run, interval=PROGRESS_PRINT)

    return result


def merge_address_estimates_to_properties(
    property_data: dict[tuple[str, str, str, str, str], dict[str, Any]],
    area_map: dict[tuple[str, str, str, str], tuple[Decimal, Decimal]],
    price_map: dict[tuple[str, str, str, str], tuple[Decimal, Decimal]],
) -> int:
    """
    주소별 평수(min,max)과 평단가(min,max)를 이용해 전세금(min,max, 원)을 계산하여
    `property_data`의 deposit_min/deposit_max(원 단위)에 병합합니다.
    계산 방식: deposit_min = pcpp_min * pyeong_min, deposit_max = pcpp_max * pyeong_max
    반환: 병합된 갯수
    """
    count = {
        "updated": 0,
    }
    items = list(property_data.items())
    total = len(property_data)
    def run(idx: int):
        (sido, sigungu, emd_raw, lotno, _), item = items[idx]
        key = (sido, sigungu, emd_raw, lotno)
        area = area_map.get(key)
        price = price_map.get(key)
        if not area or not price:
            return

        area_min, area_max = area
        pcpp_min, pcpp_max = price

        # pcpp는 (파일 기준) 평당 가격(원/평)로 간주
        total_min_won = (pcpp_min * area_min).quantize(0) if isinstance(pcpp_min, Decimal) else Decimal(0)
        total_max_won = (pcpp_max * area_max).quantize(0) if isinstance(pcpp_max, Decimal) else Decimal(0)

        if total_min_won <= 0 or total_max_won <= 0:
            return

        # property_data의 deposit는 원 단위(현재 코드에서 원 단위로 저장)
        comp_min = int(total_min_won)
        comp_max = int(total_max_won)

        if item.get("deposit_min") is None:
            item["deposit_min"] = comp_min
        else:
            item["deposit_min"] = min(item["deposit_min"], comp_min)

        if item.get("deposit_max") is None:
            item["deposit_max"] = comp_max
        else:
            item["deposit_max"] = max(item["deposit_max"], comp_max)

        count["updated"] += 1
    run_with_progress("주소병합", total, run, interval=PROGRESS_PRINT)

    return count["updated"]


def get_or_create_infrastructure(
    db: Session,
    type_id: int,
    region_id: int,
    name: str,
    latitude: Decimal,
    longitude: Decimal,
    version_id: int,
) -> tuple[Infrastructure, bool]:
    """
    (type_id, name, latitude, longitude)으로 기존 인프라 조회.
    - 없으면: 새로 생성 후 반환 (True)
    - 있으면: 버전만 업데이트 후 반환 (False)
    """

    existing = (
        db.query(Infrastructure)
        .filter(
            Infrastructure.type_id == type_id,
            Infrastructure.region_id == region_id,
            Infrastructure.name == name,
        )
        .first()
    )

    if existing is None:
        infra = Infrastructure(
            type_id=type_id,
            region_id=region_id,
            name=name,
            coordinates=(latitude, longitude),
            version_id=version_id,
        )
        db.add(infra)
        return infra, True
    else:
        existing.version_id = version_id
        return existing, False


def get_or_create_property(
    db: Session,
    version_id: int,
    region_id: int,
    name: str,
    land_lot_address: str,
    latitude: Decimal,
    longitude: Decimal,
    road_name_address: str | None = None,
    sale_price_min: int | None = None,
    sale_price_max: int | None = None,
    deposit_price_min: int | None = None,
    deposit_price_max: int | None = None,
) -> tuple[Property, bool]:
    """
    (region_id, land_lot_address, name)으로 기존 부동산 조회.
    - 없으면: 새로 생성 후 반환 (True)
    - 있으면: 가격 정보와 버전 업데이트 후 반환 (False)
    """

    sale_price_min, sale_price_max = normalize_price_range(sale_price_min, sale_price_max)
    deposit_price_min, deposit_price_max = normalize_price_range(deposit_price_min, deposit_price_max)

    existing = (
        db.query(Property)
        .filter(
            Property.region_id == region_id,
            Property.land_lot_address == land_lot_address,
            Property.name == name,
        )
        .first()
    )

    if existing is None:
        prop = Property(
            region_id=region_id,
            name=name,
            land_lot_address=land_lot_address,
            road_name_address=road_name_address,
            sale_price_min=sale_price_min,
            sale_price_max=sale_price_max,
            deposit_price_min=deposit_price_min,
            deposit_price_max=deposit_price_max,
            coordinates=(latitude, longitude),
            version_id=version_id,
        )
        db.add(prop)
        return prop, True
    else:
        # 기존값 정합성 보정 (이전 배치로 들어간 0/편측 값 정리)
        existing.sale_price_min, existing.sale_price_max = normalize_price_range(
            existing.sale_price_min, existing.sale_price_max
        )
        existing.deposit_price_min, existing.deposit_price_max = normalize_price_range(
            existing.deposit_price_min, existing.deposit_price_max
        )

        # 기존 데이터 업데이트 (가격 정보 병합)
        if sale_price_min is not None:
            existing.sale_price_min = (
                sale_price_min
                if existing.sale_price_min is None
                else min(existing.sale_price_min, sale_price_min)
            )
        if sale_price_max is not None:
            existing.sale_price_max = (
                sale_price_max
                if existing.sale_price_max is None
                else max(existing.sale_price_max, sale_price_max)
            )
        if deposit_price_min is not None:
            existing.deposit_price_min = (
                deposit_price_min
                if existing.deposit_price_min is None
                else min(existing.deposit_price_min, deposit_price_min)
            )
        if deposit_price_max is not None:
            existing.deposit_price_max = (
                deposit_price_max
                if existing.deposit_price_max is None
                else max(existing.deposit_price_max, deposit_price_max)
            )

        # 병합 후에도 정합성 보장
        existing.sale_price_min, existing.sale_price_max = normalize_price_range(
            existing.sale_price_min, existing.sale_price_max
        )
        existing.deposit_price_min, existing.deposit_price_max = normalize_price_range(
            existing.deposit_price_min, existing.deposit_price_max
        )

        if road_name_address and not existing.road_name_address:
            existing.road_name_address = road_name_address
        existing.version_id = version_id
        return existing, False


def build_coordinate_map_from_infra(csv_files: list[str]) -> dict[tuple[str, str, str, str], tuple[Decimal, Decimal]]:
    """
    인프라 CSV들에서 좌표 맵 생성.
    정규화된 동명 + 번지로 키 생성 (매칭 선제 정규화).
    key: (시도, 시군구, 정규화된_동명, 정규화된_번지)
    """

    coord_map: dict[tuple[str, str, str, str], tuple[Decimal, Decimal]] = {}

    print("인프라 좌표 맵 생성 중...")
    for csv_file in csv_files:
        lower_name = Path(csv_file).name.lower()
        if not any(key in lower_name for key in INFRA_FILE_MAP.keys()):
            continue

        rows = read_csv_file(csv_file)
        total = len(rows)
        def run(idx: int):
            row = rows[idx]
            sido = (row.get("SIDO_NM") or "").strip()
            if sido != "서울특별시":
                return

            sigungu = (row.get("SIGNGU_NM") or "").strip()
            emd_raw = (row.get("EMD_NM") or "").strip()
            emd_normalized = normalize_dong_for_region(emd_raw)  # 동명 정규화
            lotno = normalize_lotno(row.get("LTNO_NM") or "")  # 번지 정규화
            lat = parse_decimal(row.get("LTNO_LA"))
            lon = parse_decimal(row.get("LTNO_LO"))
            if not (sigungu and emd_normalized and lotno and lat is not None and lon is not None):
                return

            # 정규화된 키로 맵 생성 (중복 시 덮어쓰기)
            key = (sido, sigungu, emd_normalized, lotno)
            coord_map[key] = (lat, lon)
        run_with_progress(f"[{Path(csv_file).name}]", total, run, interval=PROGRESS_PRINT)

    return coord_map


def batch_geocode_coordinates(coords_set: set[tuple[Decimal, Decimal]]) -> dict[tuple[Decimal, Decimal], tuple[str, str, str] | None]:
    """
    좌표 세트를 배치로 역지오코딩합니다.
    중복 제거된 좌표들을 한 번에 처리하여 성능을 개선합니다.
    
    Returns:
        (lat, lon) -> (sido, sigungu, emd) 또는 None
    """
    geo_cache: dict[tuple[Decimal, Decimal], tuple[str, str, str] | None] = {}
    print(f"배치 역지오코딩 중...")

    items = list(coords_set)
    total = len(coords_set)
    def run(idx: int):
        (lat, lon) = items[idx]
        result = get_address_from_coords(lat, lon)
        geo_cache[(lat, lon)] = result
    run_with_progress("역지오코딩", total, run, interval=PROGRESS_PRINT)
    
    return geo_cache


def collect_region_seed_keys(
    csv_files: list[str],
) -> tuple[
    set[str],
    set[tuple[str, str]],
    set[tuple[str, str, str]],
]:
    """
    CSV들에서 Region 삽입용 유니크 키를 수집합니다.
    - depth0: sido
    - depth1: (sido, sigungu)
    - depth2: (sido, sigungu, normalized_emd)
    """

    depth0_keys: set[str] = set()
    depth1_keys: set[tuple[str, str]] = set()
    depth2_keys: set[tuple[str, str, str]] = set()

    print("지역 키 집계 중...")

    for csv_file in csv_files:
        file_name = Path(csv_file).name
        is_property_file = "아파트(매매)_실거래가" in file_name or "아파트(전월세)_실거래가" in file_name

        rows = read_csv_file(csv_file)
        total = len(rows)
        def run(idx: int):
            row = rows[idx]
            if row.get("전월세구분") == "월세":
                return
            if is_property_file:
                parsed = parse_sgg_field(row.get("시군구") or "")
                if parsed is None:
                    return
                sido, sigungu, emd_raw = parsed
            else:
                sido = (row.get("SIDO_NM") or "").strip()
                sigungu = (row.get("SIGNGU_NM") or "").strip()
                emd_raw = (row.get("EMD_NM") or "").strip()

            if sido != "서울특별시" or not sigungu:
                return

            emd_normalized = normalize_dong_for_region(emd_raw)
            if not emd_normalized:
                return

            depth0_keys.add(sido)
            depth1_keys.add((sido, sigungu))
            depth2_keys.add((sido, sigungu, emd_normalized))
        run_with_progress(f"[{Path(file_name).name}]", total, run, interval=PROGRESS_PRINT)

    return depth0_keys, depth1_keys, depth2_keys


def insert_regions(
    db: Session,
    version: Version,
    csv_files: list[str],
) -> dict[tuple[str, str, str], Region]:
    """
    Region을 depth 순서대로 먼저 삽입/갱신합니다.
    반환값은 (sido, sigungu, normalized_emd) -> Region 맵입니다.
    """

    depth0_keys, depth1_keys, depth2_keys = collect_region_seed_keys(csv_files)

    depth0_map: dict[str, Region] = {}
    depth1_map: dict[tuple[str, str], Region] = {}
    depth2_map: dict[tuple[str, str, str], Region] = {}

    print("지역 데이터 삽입 중...")

    items0 = sorted(depth0_keys)
    total0 = len(items0)
    def run0(idx: int):
        sido = items0[idx]
        depth0_map[sido] = get_or_create_region_depth0(db, version.id, sido)
        if idx % DB_BATCH_SIZE == 0:
            db.flush()
    run_with_progress("depth0", total0, run0, interval=PROGRESS_PRINT)
    if depth0_keys: db.flush()

    items1 = sorted(depth1_keys)
    total1 = len(items1)
    def run1(idx: int):
        sido, sigungu = items1[idx]
        parent = depth0_map.get(sido)
        if parent is None:
            return
        depth1_map[(sido, sigungu)] = get_or_create_region_depth1(db, version.id, parent.id, sigungu, sido)
        if idx % DB_BATCH_SIZE == 0:
            db.flush()
    run_with_progress("depth1", total1, run1, interval=PROGRESS_PRINT)
    if depth1_keys: db.flush()

    items2 = sorted(depth2_keys)
    total2 = len(items2)
    def run2(idx: int):
        sido, sigungu, emd_normalized = items2[idx]
        parent = depth1_map.get((sido, sigungu))
        if parent is None:
            return
        depth2_map[(sido, sigungu, emd_normalized)] = get_or_create_region_depth2(db, version.id, parent.id, emd_normalized, sido, sigungu)
        if idx % DB_BATCH_SIZE == 0:
            db.flush()
    run_with_progress("depth2", total2, run2, interval=PROGRESS_PRINT)
    if depth2_keys: db.flush()

    return depth2_map


def insert_infrastructures(
    db: Session,
    version: Version,
    csv_files: list[str],
    infra_type_id_map: dict[str, int],
    region_map: dict[tuple[str, str, str], Region],
) -> int:
    count = {
        "inserted": 0,
        "processed": 0,
    }

    # 1) 인프라별(type + name) 모든 좌표 수집
    # key: (infra_type_name, infra_name) -> list of (lat, lon)
    infra_coords: dict[tuple[str, str], list[tuple[Decimal, Decimal]]] = {}

    print("인프라 좌표 수집 중...")
    for csv_file in csv_files:
        lower_name = Path(csv_file).name.lower()

        matched = None
        for key, value in INFRA_FILE_MAP.items():
            if key in lower_name:
                matched = value
                break
        if matched is None:
            continue

        infra_type_name, infra_name_col = matched

        rows = read_csv_file(csv_file)
        total_rows = len(rows)
        def run_rows(idx: int):
            row = rows[idx]
            if row.get("SIDO_NM", "").strip() != "서울특별시":
                return

            infra_name = (row.get(infra_name_col) or "").strip()
            lat = parse_decimal(row.get(f"{infra_name_col}_LA") or row.get("NGHB_SUBWAY_STATN_LA"))
            lon = parse_decimal(row.get(f"{infra_name_col}_LO") or row.get("NGHB_SUBWAY_STATN_LO"))

            # 각 파일별 위경도 컬럼명이 다르므로 suffix 기반으로 보강
            if lat is None or lon is None:
                lat = parse_decimal(
                    row.get("ELESCH_LA")
                    or row.get("NGHB_EDU_FCLTY_LA")
                    or row.get("NGHB_PRKGRNLND_SPCE_LA")
                    or row.get("NGHB_LGZ_DISTB_FCLTY_LA")
                    or row.get("NGHB_LGZ_MLFLT_LA")
                    or row.get("NGHB_SUBWAY_STATN_LA")
                )
                lon = parse_decimal(
                    row.get("ELESCH_LO")
                    or row.get("NGHB_EDU_FCLTY_LO")
                    or row.get("NGHB_PRKGRNLND_SPCE_LO")
                    or row.get("NGHB_LGZ_DISTB_FCLTY_LO")
                    or row.get("NGHB_LGZ_MLFLT_LO")
                    or row.get("NGHB_SUBWAY_STATN_LO")
                )

            if not (infra_name and lat is not None and lon is not None):
                return

            infra_key = (infra_type_name, infra_name)
            if infra_key not in infra_coords:
                infra_coords[infra_key] = []
            infra_coords[infra_key].append((lat, lon))
        run_with_progress(f"[{Path(csv_file).name}]", total_rows, run_rows, interval=PROGRESS_PRINT)

    # 2) 각 인프라별로 좌표 평균을 구하고 역지오코딩
    print("좌표 평균 계산 및 역지오코딩 중...")
    avg_coords_to_geocode: dict[tuple[str, str], tuple[Decimal, Decimal]] = {}  # (type, name) -> avg (lat, lon)
    coords = sorted(infra_coords.items())
    total_coords = len(coords)
    def run_coords(idx: int):
        (infra_type_name, infra_name), coords_list = coords[idx]

        # 모든 좌표의 평균 계산
        avg_lat = sum(Decimal(c[0]) for c in coords_list) / len(coords_list)
        avg_lon = sum(Decimal(c[1]) for c in coords_list) / len(coords_list)
        avg_coords_to_geocode[(infra_type_name, infra_name)] = (avg_lat, avg_lon)
    run_with_progress("좌표 평균", total_coords, run_coords, interval=PROGRESS_PRINT)

    # 3) 평균 좌표들을 배치 역지오코딩
    avg_coords_set = set(avg_coords_to_geocode.values())
    geo_cache = batch_geocode_coordinates(avg_coords_set)

    # 4) 역지오코딩 결과로 인프라 데이터 처리
    print("인프라 데이터 삽입 중...")
    deduped_infra: dict[tuple[str, str, str, str, str], tuple[Decimal, Decimal]] = {}
    avgs = list(avg_coords_to_geocode.items())
    total_avrs = len(avgs)
    def run_avgs(idx: int):
        (infra_type_name, infra_name), (avg_lat, avg_lon) = avgs[idx]
        address = geo_cache.get((avg_lat, avg_lon))
        if address is None:
            return

        sido, sigungu, emd = address
        if not (sido and sigungu and emd):
            return

        dedupe_key = (infra_type_name, sido, sigungu, emd, infra_name)
        deduped_infra[dedupe_key] = (avg_lat, avg_lon)
    run_with_progress("인프라 처리", total_avrs, run_avgs, interval=PROGRESS_PRINT)

    # 5) 중복 제거된 결과를 DB에 삽입
    infras = list(deduped_infra.items())
    total_infras = len(infras)
    def run_infras(idx: int):
        (infra_type_name, sido, sigungu, emd, infra_name), (lat, lon) = infras[idx]
        type_id = infra_type_id_map.get(infra_type_name)
        if type_id is None:
            return

        region_key = (sido, sigungu, normalize_dong_for_region(emd))
        region = region_map.get(region_key)
        if region is None:
            return

        _, is_new = get_or_create_infrastructure(
            db,
            type_id,
            region.id,
            infra_name,
            lat,
            lon,
            version.id,
        )
        if is_new:
            count["inserted"] += 1

        count["processed"] += 1
        if count["processed"] % DB_BATCH_SIZE == 0:
            db.flush()
    run_with_progress("DB 삽입", total_infras, run_infras, interval=PROGRESS_PRINT)

    if count["processed"] % DB_BATCH_SIZE != 0:
        db.flush()

    return count["inserted"]

def collect_property_seed_data(csv_files: list[str]) -> dict[tuple[str, str, str, str, str], dict[str, Any]]:
    """
    매매/전월세 CSV에서 Property 후보를 집계합니다.
    key: (시도, 시군구, 원본동명, 번지, 단지명)
    """

    property_data: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}

    print("부동산 집계 데이터 생성 중...")
    for csv_file in csv_files:
        file_name = Path(csv_file).name
        is_sale = "아파트(매매)_실거래가" in file_name
        is_rent = "아파트(전월세)_실거래가" in file_name
        if not (is_sale or is_rent):
            continue

        rows = read_csv_file(csv_file)
        total = len(rows)
        def run(idx: int):
            row = rows[idx]
            parsed = parse_sgg_field(row.get("시군구") or "")
            if parsed is None:
                return
            if row.get("전월세구분") == "월세":
                return
            sido, sigungu, emd_raw = parsed
            if sido != "서울특별시":
                return

            lotno = normalize_lotno(row.get("번지") or "")
            apt_name = (row.get("단지명") or "").strip()
            if not (lotno and apt_name):
                return

            key = (sido, sigungu, emd_raw, lotno, apt_name)
            item = property_data.setdefault(
                key,
                {
                    "road_name": None,
                    "sale_min": None,
                    "sale_max": None,
                    "deposit_min": None,
                    "deposit_max": None,
                },
            )

            road_name = (row.get("도로명") or "").strip()
            if road_name:
                item["road_name"] = f"{sido} {sigungu} {road_name}"

            if is_sale:
                sale_price_raw = parse_price_to_int(row.get("거래금액(만원)"))
                sale_price = None if sale_price_raw is None else sale_price_raw * 10_000
                if sale_price is not None and sale_price > 0:
                    item["sale_min"] = sale_price if item["sale_min"] is None else min(item["sale_min"], sale_price)
                    item["sale_max"] = sale_price if item["sale_max"] is None else max(item["sale_max"], sale_price)

            if is_rent:
                deposit_raw = parse_price_to_int(row.get("보증금(만원)"))
                deposit = None if deposit_raw is None else deposit_raw * 10_000
                if deposit is not None and deposit > 0:
                    item["deposit_min"] = deposit if item["deposit_min"] is None else min(item["deposit_min"], deposit)
                    item["deposit_max"] = deposit if item["deposit_max"] is None else max(item["deposit_max"], deposit)
        run_with_progress(f"[{Path(csv_file).name}]", total, run, interval=PROGRESS_PRINT)

    return property_data


def insert_properties(
    db: Session,
    version: Version,
    property_data: dict[tuple[str, str, str, str, str], dict[str, Any]],
    coord_map: dict[tuple[str, str, str, str], tuple[Decimal, Decimal]],
    region_map: dict[tuple[str, str, str], Region],
) -> tuple[int, int]:
    count = {
        "inserted": 0,
        "processed": 0,
        "skipped_no_coord": 0,
    }

    print("부동산 데이터 삽입 중...")

    items = list(property_data.items())
    total = len(items)
    def run(idx: int):
        (sido, sigungu, emd_raw, lotno, apt_name), item = items[idx]
        region_key = (sido, sigungu, normalize_dong_for_region(emd_raw))
        region = region_map.get(region_key)
        if region is None:
            return

        # 좌표 맵과 동일한 정규화 규칙 적용
        emd_normalized = normalize_dong_for_region(emd_raw)
        coord_key = (sido, sigungu, emd_normalized, lotno)
        coord = coord_map.get(coord_key)

        if coord is None:
            count["skipped_no_coord"] += 1
            return

        lat, lon = coord
        land_lot_address = f"{sido} {sigungu} {emd_raw} {lotno}"

        _, is_new = get_or_create_property(
            db,
            version.id,
            region.id,
            apt_name,
            land_lot_address,
            lat,
            lon,
            road_name_address=item.get("road_name"),
            sale_price_min=item.get("sale_min"),
            sale_price_max=item.get("sale_max"),
            deposit_price_min=item.get("deposit_min"),
            deposit_price_max=item.get("deposit_max"),
        )
        if is_new:
            count["inserted"] += 1

        count["processed"] += 1
        if count["processed"] % DB_BATCH_SIZE == 0:
            db.flush()
    run_with_progress("부동산 처리", total, run, interval=PROGRESS_PRINT)

    if count["processed"] % DB_BATCH_SIZE != 0:
        db.flush()

    return count["inserted"], count["skipped_no_coord"]

def _main(db: Session, version: Version, csv_files: list[str]):
    insert_infra_types(db)

    infra_type_id_map = build_infra_type_id_map(db)
    coord_map = build_coordinate_map_from_infra(csv_files)
    property_data = collect_property_seed_data(csv_files)
    # 주소별 평수와 평단가를 수집해 property_data의 전세(원) 범위에 반영
    area_map = collect_address_area_range_from_transact(csv_files)
    price_map = collect_address_price_per_pyeong_from_complex(csv_files)
    if area_map and price_map:
        merged = merge_address_estimates_to_properties(property_data, area_map, price_map)
        if merged:
            print(f"  * 주소 기반 전세 추정 병합: {merged}건")
    region_map = insert_regions(db, version, csv_files)
    _ = insert_infrastructures(db, version, csv_files, infra_type_id_map, region_map)
    _, skipped_no_coord = insert_properties(db, version, property_data, coord_map, region_map)
    if skipped_no_coord:
        print(f"  * 좌표 매칭 실패로 건너뜀: {skipped_no_coord}")


def main(directory_path: str):
    """
    디렉토리 내의 CSV 파일을 읽어 데이터를 데이터베이스에 삽입하는 메인 함수입니다.

    Args:
        directory_path (str): CSV 파일이 있는 디렉토리 경로
    Retruns:
        None
    """

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        path = Path(directory_path)
        
        if not path.is_dir():
            print(f"폴더가 아닙니다: {directory_path}")
            return
        
        csv_files = get_csv_files(directory_path)
        files_hash = generate_files_hash(csv_files)

        version, created = get_or_create_version(db, files_hash)
        print(f"version id: {version.id}, hash: {version.hash}")
        if not created:
            print(f"같은 파일 해시가 이미 존재합니다. 작업을 종료합니다.")
            return

        _main(db, version, csv_files)
    except Exception as e:
        print(f"데이터 삽입 중 오류가 발생했습니다. 롤백을 진행합니다. ({e})")
        db.rollback()
    else:
        print("데이터 삽입이 성공적으로 완료되었습니다. 커밋을 진행합니다.")
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    if "-h" in sys.argv or "--help" in sys.argv:
        usage()
        sys.exit(0)
    elif len(sys.argv) != 1:
        usage()
        sys.exit(1)
    else:
        data_dir = Path(__file__).resolve().parent.parent / "data"
        main(str(data_dir))
