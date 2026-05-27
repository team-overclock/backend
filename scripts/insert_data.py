import re
import os
import sys
import numpy as np
import pandas as pd
import geopandas as gpd
from typing import Generator
from pathlib import Path
from typing import Any
from geopandas import GeoDataFrame
from collections.abc import Iterable
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from pyproj import Transformer

# backend 디렉터리를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import SessionLocal, engine
from app.models import Base, Region, Property, Infrastructure
from app.utils import parse_int, parse_float, run_with_progress, get_files

from scripts.csv_parser import read_csv_file
from scripts.df_parser import read_pandas, read_shp_file


PROGRESS_PRINT = 100
DB_BATCH_SIZE = 1000


# global variable
DF: dict[str, pd.DataFrame] = {}
GDF: dict[str, GeoDataFrame] = {}
ADDRESS_MAP = {}
BJD_CODE_MAP = {}
REGION_NAME_MAP = {}
REGION_UNIQUE_MAP = {}
PROPERTY_UNIQUE_MAP = {}
INFRA_UNIQUE_MAP = {}


# *_FIELD_NAME_MAP
# - key: filename.startswith(key)

PRELOAD_FIELD_NAME_MAP: dict[str, dict[str, Any]] = {
    "rnaddrkor_": {
        "priority": -10,
        "file_extension": ".txt",
        "parser": None,
        "category": "rnaddrkor",
    },
    "jibun_rnaddrkor_": {
        "priority": -10,
        "file_extension": ".txt",
        "parser": None,
        "category": "jibun",
    },
    "AL_D164_": {
        "priority": -10,
        "file_extension": ".shp",
        "category": "AL_D164",
    },
}

REGION_FIELD_NAME_MAP: dict[str, dict[str, Any]] = {
    "법정동코드 전체": {
        "file_extension": ".txt",
        "delimiter": "\t",
        "category": "동네",
        "type": "main",
        "id": "법정동코드",
        "이름": "법정동명",
        "상태": "폐지여부",
    },
    "서울시 학원 교습소정보": {
        "priority": 10,
        "category": "동네",
        "type": "academy",
        "id": "학원지정번호",
        "이름": "학원명",
        "유형": "학원/교습소",
        "도로명주소": "도로명주소",
        "도로명상세주소": "도로명상세주소",
        "운영상태": "등록상태명",
    },
}

PROPERTY_FIELD_NAME_MAP: dict[str, dict[str, Any]] = {
    "AL_D164_": {
        "file_extension": ".shp",
        "category": "건물",
        "type": "main",
    },
    "서울시 공동주택 아파트 정보": {
        "priority": 10,
        "category": "건물",
        "type": "apartment",
        "id": "k-아파트코드",
        "이름": "k-아파트명",
        "위도": "좌표Y",
        "경도": "좌표X",
        "도로명주소": "kapt도로명주소",
        "시도": "주소(시도)k-apt주소split",
        "시군구": "주소(시군구)",
        "읍면동": "주소(읍면동)",
        "나머지주소": "나머지주소",
        "도로명": "주소(도로명)",
        "도로상세주소": "주소(도로상세주소)",
        "동수": "k-전체동수",
        "세대수": "k-전체세대수",
        "주차대수": "주차대수",
    },
}

INFRA_FIELD_NAME_MAP: dict[str, dict[str, Any]] = {
    "전국초중등학교위치표준데이터": {
        "category": "학교",
        "id": "학교ID",
        "이름": "학교명",
        "위도": "위도",
        "경도": "경도",
        "지번주소": "소재지지번주소",
        "도로명주소": "소재지도로명주소",
        "유형": "학교급구분",
        "운영상태": "운영상태",
    },
    "서울시 역사마스터 정보": {
        "category": "역사",
        "type": "main",
        "id": lambda row: f"01_{row['역사명']}",
        "이름": lambda row: row['역사명'].rstrip('역'),
        "위도": "위도",
        "경도": "경도",
    },
    "국토교통부_도시철도 전체노선": {
        "priority": 10,
        "category": "역사",
        "type": "lines",
        "id": ["권역", "역명"],
        "이름": lambda row: row['역명'].rstrip('역'),
        "노선": "노선명",
    },
    "서울시 응급실 위치 정보": {
        "category": "병원",
        "id": "기관ID",
        "이름": "기관명",
        "위도": "병원위도",
        "경도": "병원경도",
        "응급의료기관코드명": "응급의료기관코드명",
    },
    "생활_대규모점포_서울특별시": {
        "category": "마트",
        "id": "관리번호",
        "이름": "사업장명",
        "tm_x": "좌표정보(X)",
        "tm_y": "좌표정보(Y)",
        "영업상태명": "영업상태명",
        "업태구분명": "업태구분명",
        "점포구분명": "점포구분명",
    },
    "전국도시공원정보표준데이터": {
        "category": "공원",
        "id": "관리번호",
        "이름": "공원명",
        "위도": "위도",
        "경도": "경도",
        "지번주소": "소재지지번주소",
        "도로명주소": "소재지도로명주소",
        "면적": "공원면적",
    },
}


transformer = Transformer.from_crs("epsg:5179", "epsg:4326", always_xy=True)


def usage():
    print("사용법: python insert_data.py")
    print("  - data 폴더 내 *.csv 파일 데이터를 데이터베이스에 삽입합니다.")


def string_rcut_and_rstrip(_value: str, suffix: str) -> tuple[str, bool]:
    value = _value.strip()
    if value.endswith(suffix):
        value = value[:-len(suffix)].strip()
    return value, _value != value

def all_join_or_none(*args, sep=" "):
    if all(args):
        return sep.join(str(arg) for arg in args)
    return None


def get_field_value(row: dict[str, Any], value: Any) -> str | None:
    if isinstance(value, str):
        return row.get(value, "").strip() or None

    if isinstance(value, Iterable) and all(isinstance(v, str) for v in value):
        return "_".join(str(row.get(key, "").strip()) for key in value) or None

    if callable(value):
        return value(row).strip() or None


def get_coords_from_row(row: dict[str, Any], field_mapping: dict[str, Any]) -> tuple[float, float] | None:
    """
    주어진 행에서 위도와 경도를 추출하여 float 형태로 반환합니다.

    Args:
        row (dict[str, Any]): CSV 파일의 한 행을 나타내는 딕셔너리
        field_mapping (dict[str, Any]): 위도와 경도 필드 이름이 매핑된 딕셔너리

    Returns:
        tuple[float, float] | None: (위도, 경도) 튜플 또는 좌표 정보를 찾을 수 없는 경우 None
    """
    lat = None
    lng = None
    try:
        lat = parse_float(row[field_mapping["위도"]])
        lng = parse_float(row[field_mapping["경도"]])
        if lat is None or lng is None: raise
    except:
        try:
            tm_x = parse_float(row[field_mapping["tm_x"]])
            tm_y = parse_float(row[field_mapping["tm_y"]])
            lng, lat = transformer.transform(tm_x, tm_y)
        except:
            pass
    if lat is None or lng is None:
        return None
    return lat, lng


def normalize_sido(sido: str) -> str:
    sido = re.sub(r"^서울(시|특별시)?($|\s+)", "서울특별시 ", sido).strip()
    return sido


def get_next_region_name(region_name: str) -> Generator[str, None, None]:
    maybe_gu = region_name.split()
    maybe_gu = maybe_gu[1] if len(maybe_gu) > 1 else None

    region_name = region_name.strip()
    yield region_name

    check1 = re.sub(r"[\d -]+$", "", region_name)
    yield check1

    check2 = re.sub(r"[\d·]+", "", check1)
    yield check2

    check3 = "상일동" if maybe_gu == "강동구" and check2 == "상동" else None
    if check3: yield check3


def nomalize_apartment_address(name: str, address: str) -> str:
    strip = string_rcut_and_rstrip
    name, _ = strip(name, "아파트")
    address, _ = strip(address, "관리소")
    address, _ = strip(address, "관리사무소")
    address, _ = strip(address, "아파트")
    address, _ = strip(address, "번지")
    address, _ = strip(address, name)
    return address


def clean_series_field(series, fill_val=""):
    return series.fillna(fill_val).astype(str).str.strip()

def empty_series_to_nan(series):
    return series.astype(str).str.strip().replace("", np.nan)


def parse_address_data(_df: pd.DataFrame) -> pd.DataFrame:
    print()
    print(f"  - ✅ 원본 데이터 로드 완료 (총 {len(_df)}개 행)")
    print(f"  - ⏳ 1. 데이터 제거 및 정형화 작업 중...")

    # 필수 데이터 결측치 제거 및 정형화

    df = _df.dropna(subset=["법정동코드"])

    tmp_df = df[[
        "도로명주소관리번호",
        "법정동코드",
        "시도명",
        "시군구명",
        "법정읍면동명",
        "법정리명",
        "산여부",
        "지번본번",
        "지번부번",
        "도로명코드",
        "도로명", 
        "건물본번",
        "건물부번",
    ]].copy().apply(clean_series_field)

    tmp_df["법정읍면동명"] = tmp_df["법정읍면동명"].fillna("")
    tmp_df["법정리명"] = tmp_df["법정리명"].fillna("")
    tmp_df["산여부"] = tmp_df["산여부"].fillna("0")
    tmp_df["지번본번"] = tmp_df["지번본번"].fillna("0")
    tmp_df["지번부번"] = tmp_df["지번부번"].fillna("0")
    tmp_df["지번본번"] = tmp_df["지번본번"].str.zfill(4)
    tmp_df["지번부번"] = tmp_df["지번부번"].str.zfill(4)

    # 산여부 0과 1을 각각 1(일반 대지), 2(산)로 변환
    tmp_df["산여부"] = np.where(tmp_df["산여부"] == "0", "1", "2")

    # 시군구코드, 읍면동코드, 도로명번호 추출
    tmp_df["시군구코드"] = tmp_df["도로명코드"].str[:5]
    tmp_df["읍면동코드"] = tmp_df["도로명주소관리번호"].str[5:8]
    tmp_df["도로명번호"] = tmp_df["도로명코드"].str[5:]

    print(f"  - ⏳ 2. pnu_code 컬럼 결합 연산 및 지번/도로명 주소 매핑 중...")
    tmp_df["pnu_code"] = tmp_df["법정동코드"] + tmp_df["산여부"] + tmp_df["지번본번"] + tmp_df["지번부번"]

    tmp_df["지번주소"] = (
        tmp_df["시도명"] + " " +
        tmp_df["시군구명"] + " " +
        tmp_df["법정읍면동명"] + " " +
        tmp_df["법정리명"] + " " +
        (
            tmp_df["지번본번"].str.lstrip("0") +
            "-" +
            tmp_df["지번부번"].str.lstrip("0")
        ).str.strip(" -")
    ).str.replace(r"\s+", " ", regex=True).str.strip()

    tmp_df["도로명주소"] = (
        tmp_df["시도명"] + " " +
        tmp_df["시군구명"] + " " +
        tmp_df["도로명"] + " " +
        (
            tmp_df["건물본번"].str.lstrip("0") +
            "-" +
            tmp_df["건물부번"].str.lstrip("0")
        ).str.strip(" -")
    )

    print(f"  - ✅ 최종 데이터 개수: {len(tmp_df)}개")
    print(f"  - ✅ 제거된 데이터 개수: {len(df) - len(tmp_df)}")

    res = df.copy()
    res["pnu_code"] = tmp_df["pnu_code"]
    res["시군구코드"] = tmp_df["시군구코드"]
    res["읍면동코드"] = tmp_df["읍면동코드"]
    res["도로명번호"] = tmp_df["도로명번호"]
    res["도로명주소"] = tmp_df["도로명주소"]
    res["지번주소"] = tmp_df["지번주소"]
    return res

def parse_rnaddrkor(filepath: str, *_):
    rdf = read_pandas(
        filepath,
        names=[
            "도로명주소관리번호",
            "법정동코드",
            "시도명",
            "시군구명",
            "법정읍면동명",
            "법정리명",
            "산여부",
            "지번본번",
            "지번부번",
            "도로명코드",
            "도로명",
            "지하여부",
            "건물본번",
            "건물부번",
            "행정동코드",
            "행정동명",
            "기초구역번호",
            "이전도로명주소",
            "효력발생일",
            "공동주택구분",
            "이동사유코드",
            "건축물대장건물명",
            "시군구용건물명",
            "비고",
        ],
    )

    rdf = parse_address_data(rdf)
    print(f"  - ⏳ 주소 변환을 위한 사전 매핑 중...")
    ADDRESS_MAP["rncode_to_rn"] = dict(zip(rdf["도로명코드"], rdf["도로명"]))
    DF["rnaddrkor"] = rdf

def parse_jibun_rnaddrkor(filepath: str, *_):
    jdf = read_pandas(
        filepath,
        names=[
            "도로명주소관리번호",
            "법정동코드",
            "시도명",
            "시군구명",
            "법정읍면동명",
            "법정리명",
            "산여부",
            "지번본번",
            "지번부번",
            "도로명코드",
            "지하여부",
            "건물본번",
            "건물부번",
            "이동사유코드",
        ],
    )

    jdf["도로명"] = jdf["도로명코드"].map(ADDRESS_MAP["rncode_to_rn"])
    jdf = parse_address_data(jdf)
    DF["jibun"] = jdf

def parse_AL_D164_shp(filepath: str, *_):
    gdf = read_shp_file(
        filepath,
        columns=[
            "GIS건물통합식별번호",
            "고유번호",
            "법정동코드",
            "법정동명",
            "특수지구분코드",
            "특수지구분명",
            "지번",
            "건물식별번호",
            "집합건물구분코드",
            "집합건물구분",
            "대장종류코드",
            "대장종류",
            "건물명",
            "상위건물식별번호",
            "도로명주소코드",
            "도로명주소읍면동리코드",
            "도로명주소지하코드",
            "도로명주소본번",
            "도로명주소부번",
            "건물동명",
            "건물주부구분코드",
            "건물주부구분",
            "건물대지면적(㎡)",
            "건물건축면적(㎡)",
            "건물연면적(㎡)",
            "용적율(%)",
            "건폐율(%)",
            "건축물구조코드",
            "건축물구조명",
            "건축물용도코드",
            "건축물용도명",
            "건물높이",
            "지상층수",
            "지하층수",
            "허가일자",
            "사용승인일자",
            "총주차수",
            "총주차장면적(㎡)",
            "데이터기준일자",
            "시군구코드",
            "geometry",
        ],
    )

    jdf = DF["jibun"]
    rdf = DF["rnaddrkor"]
    print()
    print(f"  - ✅ 원본  데이터 로드 완료 (총 {len(gdf)}개 행)")

    # ==========================================
    # 1. 사람이 살 수 있는 주거용 건물 추출
    # ==========================================
    print("  - ⏳ 1. 주거용 건물(단독/공동주택 등) 필터링 중...")

    gdf["건축물용도코드"] = clean_series_field(gdf["건축물용도코드"])
    residential_mask = (
        gdf["건축물용도코드"].str.startswith("01") | 
        gdf["건축물용도코드"].str.startswith("02") |
        gdf["건축물용도명"].str.contains("주택|아파트|빌라|오피스텔", na=False)
    )
    merged_df = gdf[residential_mask].copy()

    # ==========================================================
    # 2. 주소 매핑
    # ==========================================================
    print(f"  - ⏳ 2. 주소 매핑용 룩업 사전 빌드 중...")

    # 0) 주소 매핑용 사전 빌드: 관리번호와 PNU 기준으로 각각 도로명주소/지번주소 매핑할 수 있는 사전 조립
    jdf_by_mgmt = jdf.drop_duplicates(subset=["도로명주소관리번호"])
    rdf_by_mgmt = rdf.drop_duplicates(subset=["도로명주소관리번호"])

    jdf_by_pnu = jdf.drop_duplicates(subset=["pnu_code"])
    rdf_by_pnu = rdf.drop_duplicates(subset=["pnu_code"])

    # 1) rnnum_to_rnaddr : 관리번호 -> 도로명주소 및 역매핑
    ADDRESS_MAP.setdefault("rnnum_to_rnaddr", {})
    ADDRESS_MAP.setdefault("rnaddr_to_rnnum", {})
    for zips in [
        zip(rdf_by_mgmt["도로명주소"], rdf_by_mgmt["도로명주소관리번호"]),
        zip(jdf_by_mgmt["도로명주소"], jdf_by_mgmt["도로명주소관리번호"]),
    ]:
        for addr, num in zips:
            ADDRESS_MAP["rnnum_to_rnaddr"].setdefault(num, addr)
            ADDRESS_MAP["rnaddr_to_rnnum"].setdefault(addr.replace(" ", ""), []).append(num)

    # 2) rnnum_to_jibun : 관리번호 -> 지번주소 및 역매핑
    ADDRESS_MAP.setdefault("rnnum_to_jibun", {})
    ADDRESS_MAP.setdefault("jibun_to_rnnum", {})
    for zips in [
        zip(jdf_by_pnu["지번주소"], jdf_by_pnu["도로명주소관리번호"]),
        zip(rdf_by_pnu["지번주소"], rdf_by_pnu["도로명주소관리번호"]),
    ]:
        for addr, num in zips:
            ADDRESS_MAP["rnnum_to_jibun"].setdefault(num, addr)
            ADDRESS_MAP["jibun_to_rnnum"].setdefault(addr.replace(" ", ""), []).append(num)

    # 3) pnu_to_rnaddr : PNU -> 도로명주소 및 역매핑
    ADDRESS_MAP.setdefault("pnu_to_rnaddr", {})
    ADDRESS_MAP.setdefault("rnaddr_to_pnu", {})
    for zips in [
        zip(rdf_by_mgmt["도로명주소"], rdf_by_mgmt["pnu_code"]),
        zip(jdf_by_mgmt["도로명주소"], jdf_by_mgmt["pnu_code"]),
    ]:
        for addr, pnu in zips:
            ADDRESS_MAP["pnu_to_rnaddr"].setdefault(pnu, addr)
            ADDRESS_MAP["rnaddr_to_pnu"].setdefault(addr.replace(" ", ""), []).append(pnu)

    # 4) pnu_to_jibun : PNU -> 지번주소 및 역매핑
    ADDRESS_MAP.setdefault("pnu_to_jibun", {})
    ADDRESS_MAP.setdefault("jibun_to_pnu", {})
    for zips in [
        zip(jdf_by_pnu["지번주소"], jdf_by_pnu["pnu_code"]),
        zip(rdf_by_pnu["지번주소"], rdf_by_pnu["pnu_code"]),
    ]:
        for addr, pnu in zips:
            ADDRESS_MAP["pnu_to_jibun"].setdefault(pnu, addr)
            ADDRESS_MAP["jibun_to_pnu"].setdefault(addr.replace(" ", ""), []).append(pnu)

    print("✨ [SUCCESS] 데이터 우선순위 역전 사전(ADDRESS_MAP) 빌드 완료!")

    # ==========================================
    # 3. 도로명주소관리번호 추출 및 주소 매핑용 컬럼 조립
    # ==========================================
    print("  - ⏳ 3. 도로명주소관리번호 추출 및 주소 매핑용 컬럼 조립 중...")

    tmp_df = merged_df[["고유번호", "도로명주소코드", "도로명주소읍면동리코드", "도로명주소지하코드", "도로명주소본번", "도로명주소부번"]].copy()
    tmp_df = tmp_df.dropna(subset=["도로명주소코드", "도로명주소읍면동리코드"], how="all")

    tmp_df["도로명주소코드"] = clean_series_field(tmp_df["도로명주소코드"])
    tmp_df["도로명주소읍면동리코드"] = clean_series_field(tmp_df["도로명주소읍면동리코드"])
    tmp_df["도로명주소지하코드"] = clean_series_field(tmp_df["도로명주소지하코드"], "0")
    tmp_df["도로명주소본번"] = clean_series_field(tmp_df["도로명주소본번"], "0")
    tmp_df["도로명주소부번"] = clean_series_field(tmp_df["도로명주소부번"], "0")

    tmp_df["시군구코드"] = tmp_df["도로명주소코드"].str[:5]
    tmp_df["읍면동코드"] = tmp_df["도로명주소읍면동리코드"].str[:3]
    tmp_df["읍면동일련번호"] = tmp_df["도로명주소읍면동리코드"].str[3:]
    tmp_df["도로명번호"] = tmp_df["도로명주소코드"].str[5:]
    tmp_df["도로명주소본번"] = tmp_df["도로명주소본번"].str.zfill(5)
    tmp_df["도로명주소부번"] = tmp_df["도로명주소부번"].str.zfill(5)

    tmp_df["도로명주소관리번호"] = tmp_df["시군구코드"] + tmp_df["읍면동코드"] + tmp_df["도로명번호"] + tmp_df["도로명주소지하코드"] + tmp_df["도로명주소본번"] + tmp_df["도로명주소부번"]

    # Left Join
    tmp_subset = tmp_df[["시군구코드", "읍면동코드", "읍면동일련번호", "도로명번호", "도로명주소관리번호"]]
    merged_df = merged_df.merge(tmp_subset, left_index=True, right_index=True, how="left")

    # ==========================================
    # 4. 국토부 GDF에 대장 주소 1차 수혈 (map 연산)
    # ==========================================
    print("  - ⏳ 4. 국토부 GDF에 대장 주소 매핑 중...")
    merged_df["도로명주소"] = merged_df["도로명주소관리번호"].map(ADDRESS_MAP["rnnum_to_rnaddr"]).fillna(merged_df["고유번호"].map(ADDRESS_MAP["pnu_to_rnaddr"]))
    merged_df["지번주소"] = merged_df["고유번호"].map(ADDRESS_MAP["pnu_to_jibun"]).fillna(merged_df["도로명주소관리번호"].map(ADDRESS_MAP["rnnum_to_jibun"]))

    # ==========================================
    # 5. 대장 미매칭 구역 대상 GDF 내장 정보 결합
    # ==========================================
    print("  - ⏳ 5. 대장 미매칭 유령 필지 대상 국토부 내장 정보 결합 및 예외 처리...")

    # 1) 지번주소 Fallback: 대장 주소가 끝까지 없으면 [법정동명 + 지번] 조합으로 강제 메꿈
    fallback_jibun = (merged_df["법정동명"] + " " + merged_df["지번"]).str.strip()
    merged_df["지번주소"] = np.where(
        merged_df["지번주소"].isna() | (merged_df["지번주소"] == "") | (merged_df["지번주소"] == "nan"),
        fallback_jibun,
        merged_df["지번주소"]
    )

    # 2) 도로명주소 Fallback: 대장 주소가 없으면 차선책으로 내장 건물명이라도 보존 (없으면 None)
    merged_df["도로명주소"] = np.where(
        merged_df["도로명주소"].isna() | (merged_df["도로명주소"] == "") | (merged_df["도로명주소"] == "nan"),
        np.where(merged_df["건물명"] != "", merged_df["건물명"], None),
        merged_df["도로명주소"]
    )

    # ==========================================
    # 6. 주소 분리 조립 및 필수/Nullable 데이터 최종 추출
    # ==========================================
    print("  - ⏳ 6. 주소 분리 조립 및 필수/Nullable 데이터 최종 추출 중...")

    # 추후 region 관계설정 및 좌표를 point로 변환해야 함
    renames = {
        "고유번호": "source_id",
        "건축물용도명": "type",
        "건물명": "name",
        "지번주소": "land_lot_address",
        "도로명주소": "road_name_address",
        "법정동코드": "bjd_code",
    }
    res_df = merged_df[list(renames.keys())].rename(columns=renames)

    centroid_4326 = gpd.GeoSeries(merged_df.geometry.centroid, crs=merged_df.crs).to_crs(epsg=4326)
    res_df["lon"] = centroid_4326.x
    res_df["lat"] = centroid_4326.y

    # ====================================================
    # 7.: 19자리 고유번호(source_id) 기준 단지화 압축 (중복 제거)
    # ====================================================
    print("  - ⏳ 같은 아파트 단지(동별 데이터)를 하나의 대표 단지 데이터로 압축 중...")
    agg_rules = {
        "lon": "mean",
        "lat": "mean",
        "land_lot_address": "first",
        "road_name_address": "first",  # 행안부 마스터 기준으로 완벽히 통일된 주소 채택
        "name": "first",
        "type": "first",
        "bjd_code": "first"
    }

    res_df = res_df.groupby("source_id", as_index=False).agg(agg_rules)
    res_df = res_df.replace({np.nan: None})

    GDF["AL_D164"] = res_df


def parse_region(row: dict[str, Any], field_mapping: dict[str, Any], context: dict[str, Any]):
    name = get_field_value(row, field_mapping["이름"])
    source_id = get_field_value(row, field_mapping["id"])

    if field_mapping["type"] == "main":
        if not name.startswith("서울"):
            return

        status = get_field_value(row, field_mapping["상태"])
        if status != "존재":
            return
        
        data = {
            "source_id": source_id,
            "name": name,
            "depth": name.count(" "),
        }
        REGION_NAME_MAP[name] = data
        BJD_CODE_MAP[source_id] = name
        BJD_CODE_MAP[name] = source_id
        return data
    elif field_mapping["type"] == "academy":
        status = get_field_value(row, field_mapping["운영상태"])
        if status != "개원":
            return

        try:
            academy_type = get_field_value(row, field_mapping["유형"])
            if academy_type == "교습소":
                return

            addr = get_field_value(row, field_mapping["도로명주소"])
            addr = normalize_sido(addr)
            si, gu = addr.split()[:2]

            addr_detail = get_field_value(row, field_mapping["도로명상세주소"])
            start_idx = addr_detail.find("(")
            if start_idx == -1: return

            details = [
                d.rstrip("층").strip()
                for a in addr_detail[start_idx:].split("(")
                for b in a.split(")")
                for c in b.replace(".", ",").split(",")
                for d in c.split(" ")
                if d.strip()
            ]
            context.setdefault("academy", []).append((si, gu, details))
        except:
            pass

def post_parse_region(context: dict[str, Any]):
    academy = context.get("academy", [])

    for si, gu, details in academy:
        dong = None
        for item in details:
            checks = get_next_region_name(item)
            for curr in checks:
                if not curr: continue
                full_name = f"{si} {gu} {curr}"
                if full_name in REGION_NAME_MAP:
                    dong = curr
                    break
        if not dong: continue
        for key in [si, f"{si} {gu}", f"{si} {gu} {dong}"]:
            REGION_NAME_MAP.get(key, {}).setdefault("academy_count", 0)
            REGION_NAME_MAP[key]["academy_count"] += 1


def parse_apartment(row: dict[str, Any], field_mapping: dict[str, Any], context: dict[str, Any]):
    bjd_codes = context.setdefault("bjd_codes", {})
    if field_mapping["type"] == "main":
        gdf = GDF["AL_D164"]
        records = gdf.to_dict(orient="records")
        results = context.setdefault("results", {})
        for record in records:
            bjd_codes[record["source_id"]] = record["bjd_code"]
            results[record["source_id"]] = {
                "source_id": record["source_id"],
                "type": record["type"],
                "name": record["name"],
                "land_lot_address": record["land_lot_address"],
                "road_name_address": record["road_name_address"],
                "coordinates": (record["lat"], record["lon"]),
            }
    elif field_mapping["type"] == "apartment":
        name = get_field_value(row, field_mapping["이름"])
        apt_id = get_field_value(row, field_mapping["id"])
        
        rn_address = get_field_value(row, field_mapping["도로명주소"])
        sido = normalize_sido(get_field_value(row, field_mapping["시도"]) or "")
        sigungu = get_field_value(row, field_mapping["시군구"])
        dong = get_field_value(row, field_mapping["읍면동"])
        jibun_suffix = get_field_value(row, field_mapping["나머지주소"])
        road_name = get_field_value(row, field_mapping["도로명"])
        road_suffix = get_field_value(row, field_mapping["도로상세주소"])
        dong_count = parse_int(get_field_value(row, field_mapping["동수"]))
        household_count = parse_int(get_field_value(row, field_mapping["세대수"]))
        parking_count = parse_float(get_field_value(row, field_mapping["주차대수"]))
        parking_per_household = None if parking_count is None or household_count is None else parking_count / household_count if household_count else 0

        ll_address = nomalize_apartment_address(name, all_join_or_none(sido, sigungu, dong, jibun_suffix) or "") or None
        rn_address = nomalize_apartment_address(name, rn_address or all_join_or_none(sido, sigungu, road_name, road_suffix) or "") or None

        def extract_rnnum_from_kapt():
            rn_key = rn_address.replace(" ", "") if rn_address else None
            if rn_key in ADDRESS_MAP["rnaddr_to_rnnum"]:
                return ADDRESS_MAP["rnaddr_to_rnnum"][rn_key][0]
            ll_key = ll_address.replace(" ", "") if ll_address else None
            if ll_key in ADDRESS_MAP["jibun_to_rnnum"]:
                return ADDRESS_MAP["jibun_to_rnnum"][ll_key][0]
            return None # 양쪽 다 실패 시 안전하게 Null 리턴
        source_id = extract_rnnum_from_kapt()

        data = {
            "source_id": source_id or apt_id,
            "name": name,
            "land_lot_address": ll_address,
            "road_name_address": rn_address,
            "dong_count": dong_count,
            "household_count": household_count,
            "parking_count": parking_count,
            "parking_per_household": parking_per_household,
        }

        if not source_id:
            coords = get_coords_from_row(row, field_mapping)
            if not coords:
                return

            checks = get_next_region_name(dong)
            for curr in checks:
                if not curr: continue
                full_name = f"{sido} {sigungu} {curr}"
                if full_name in BJD_CODE_MAP:
                    dong = curr
                    break

            # BJD_CODE_MAP[full_name]: 항상 존재해야 함
            bjd_codes[apt_id] = BJD_CODE_MAP[full_name]
            return {
                **data,
                "coordinates": coords,
            }
        else:
            if ll_address: context.setdefault("extra_data", {})[ll_address.replace(" ", "")] = data
            if rn_address: context.setdefault("extra_data", {})[rn_address.replace(" ", "")] = data


def parse_school(row: dict[str, Any], field_mapping: dict[str, Any], context: dict[str, Any]):
    name = get_field_value(row, field_mapping["이름"])
    source_id = get_field_value(row, field_mapping["id"])

    coords = get_coords_from_row(row, field_mapping)
    if not coords:
        return

    status = get_field_value(row, field_mapping["운영상태"])
    if status != "운영":
        return

    address = get_field_value(row, field_mapping["도로명주소"]) or get_field_value(row, field_mapping["지번주소"])
    if not address.startswith("서울"):
        return

    school_type = get_field_value(row, field_mapping["유형"])
    infrastructure_type = "ELEMENTARY_SCHOOL" if school_type == "초등학교" else "MIDDLE_SCHOOL" if school_type == "중학교" else "HIGH_SCHOOL" if school_type == "고등학교" else None
    if not infrastructure_type:
        return
    
    # 학군?
    # 횡단보도 수?
    
    return {
        "type": infrastructure_type,
        "source_id": source_id,
        "name": name,
        "coordinates": coords,
        "details": None,
    }


def parse_subway_station(row: dict[str, Any], field_mapping: dict[str, Any], context: dict[str, Any]):
    name = get_field_value(row, field_mapping["이름"])
    source_id = get_field_value(row, field_mapping["id"])

    if field_mapping["type"] == "main":
        coords = get_coords_from_row(row, field_mapping)
        if coords:
            old_coords = context.setdefault("coords", {}).setdefault(source_id, {})
            count = old_coords.get("count")
            if count is None:
                old_coords["count"] = 1
                old_coords["lat"] = coords[0]
                old_coords["lng"] = coords[1]
            else:
                count += 1
                old_coords["count"] += count
                old_coords["lat"] += (coords[0] - old_coords["lat"]) / count
                old_coords["lng"] += (coords[1] - old_coords["lng"]) / count

        return {
            "type": "SUBWAY_STATION",
            "source_id": source_id,
            "name": name,
        }
    elif field_mapping["type"] == "lines":
        result = context.get("results", {}).get(source_id)
        if not result: return
        line = get_field_value(row, field_mapping["노선"])
        result.setdefault("details", {}).setdefault("lines", []).append(line)

def post_parse_subway_station(context: dict[str, Any]):
    all_coords = context.get("coords", {})
    for source_id in all_coords:
        coords = all_coords[source_id]
        if not coords: continue
        context.get("results", {}).get(source_id, {})["coordinates"] = (coords["lat"], coords["lng"])


def parse_large_hospital(row: dict[str, Any], field_mapping: dict[str, Any], context: dict[str, Any]):
    name = get_field_value(row, field_mapping["이름"])
    source_id = get_field_value(row, field_mapping["id"])

    coords = get_coords_from_row(row, field_mapping)
    if not coords:
        return
    
    code = get_field_value(row, field_mapping["응급의료기관코드명"])
    
    details = {
        "응급의료기관코드명": code,
    }
    
    infrastructure_type = "LARGE_HOSPITAL"
    return {
        "type": infrastructure_type,
        "source_id": source_id,
        "name": name,
        "coordinates": coords,
        "details": details,
    }


def parse_large_supermarket(row: dict[str, Any], field_mapping: dict[str, Any], context: dict[str, Any]):
    name = get_field_value(row, field_mapping["이름"])
    source_id = get_field_value(row, field_mapping["id"])
    coords = get_coords_from_row(row, field_mapping)
    if not coords:
        return
    
    status = get_field_value(row, field_mapping["영업상태명"])
    if status != "영업/정상":
        return
    
    store_type = get_field_value(row, field_mapping["점포구분명"])
    if store_type not in ["대규모점포", "준대규모점포"]:
        return
    
    biz_type = get_field_value(row, field_mapping["업태구분명"])
    
    infrastructure_type = "LARGE_SUPERMARKET"
    return {
        "type": infrastructure_type,
        "source_id": source_id,
        "name": name,
        "coordinates": coords,
        "details": {
            "업태구분명": biz_type,
            "점포구분명": store_type,
        },
    }


def parse_park(row: dict[str, Any], field_mapping: dict[str, Any], context: dict[str, Any]):
    name = get_field_value(row, field_mapping["이름"])
    source_id = get_field_value(row, field_mapping["id"])
    
    coords = get_coords_from_row(row, field_mapping)
    if not coords:
        return

    address = get_field_value(row, field_mapping["지번주소"]) or get_field_value(row, field_mapping["도로명주소"])
    if not address.startswith("서울"):
        return
    
    try:
        park_area = get_field_value(row, field_mapping["면적"])
    except:
        park_area = None
    
    infrastructure_type = "PARK"
    return {
        "type": infrastructure_type,
        "source_id": source_id,
        "name": name,
        "coordinates": coords,
        "details": {
            "면적": park_area,
        },
    }


def connect_relationships(contexts: dict[str, Any]):
    # region self relationship
    regions = contexts.get("동네", {}).get("instances", {})
    for source_id in regions:
        ins = regions[source_id]
        name = ins.name
        if " " in name:
            parent_name = " ".join(name.split(" ")[:-1])
            parent_source_id = REGION_NAME_MAP[parent_name]["source_id"]
            parent_ins = regions[parent_source_id]
            ins.parent = parent_ins

    # property - region relationship
    context = contexts.get("건물", {})
    bjd_codes = context.get("bjd_codes", {})
    properties = context.get("instances", {})
    extra_data = context.get("extra_data", {})
    for source_id in properties:
        ins = properties[source_id]

        bjd_code = bjd_codes[source_id]
        ins.region = regions[bjd_code]

        keys = [
            ins.land_lot_address,
            ins.road_name_address,
        ]
        extra = None
        for key in keys:
            key = key.replace(" ", "").strip() if key else None
            if not key: continue
            if key in extra_data:
                extra = extra_data[key]
                break
        if not extra: continue
        if not ins.name: ins.name = extra.get("name")
        if not ins.land_lot_address: ins.land_lot_address = extra.get("land_lot_address")
        if not ins.road_name_address: ins.road_name_address = extra.get("road_name_address")
        ins.dong_count = extra.get("dong_count")
        ins.household_count = extra.get("household_count")
        ins.parking_count = extra.get("parking_count")
        ins.parking_per_household = extra.get("parking_per_household")


def _main(db: Session, target_files: list[str]):
    print(f"데이터베이스에서 기존 데이터 조회 중...")
    REGION_UNIQUE_MAP.update({x.source_id: x for x in db.query(Region).all()})
    PROPERTY_UNIQUE_MAP.update({x.source_id: x for x in db.query(Property).all()})
    INFRA_UNIQUE_MAP.update({(x.type.value, x.source_id): x for x in db.query(Infrastructure).all()})
    MAP_ROUTER = {
        Region: REGION_UNIQUE_MAP,
        Property: PROPERTY_UNIQUE_MAP,
        Infrastructure: INFRA_UNIQUE_MAP
    }
    def get_model_instance(model_cls, result: dict[str, Any]):
        target_map = MAP_ROUTER.get(model_cls, {})
        
        if model_cls is Region or model_cls is Property:
            key = result["source_id"]
        elif model_cls is Infrastructure:
            key = (result.get("type"), result.get("source_id"))

        return target_map.pop(key, None)

    print(f"데이터 처리 중...")
    contexts: dict[str, Any] = {}
    map_items = [
        item
        for field_map in [
            PRELOAD_FIELD_NAME_MAP,
            REGION_FIELD_NAME_MAP,
            PROPERTY_FIELD_NAME_MAP,
            INFRA_FIELD_NAME_MAP,
        ]
        for item in field_map.items()
    ]
    priorities = {}
    for k, v in map_items:
        p = v.get("priority", 0)
        priorities.setdefault(p, []).append((k, v))

    filepath_and_names = [(file, Path(file).stem) for file in target_files]
    for p in sorted(priorities):
        for key, field_mapping in priorities[p]:
            file_extension = field_mapping.get("file_extension", ".csv")
            filtered_files = filter(lambda x: x[1].startswith(key) and x[0].endswith(file_extension), filepath_and_names)
            for filepath, filename in filtered_files:
                is_iterable = False
                if file_extension != ".shp":
                    parser = field_mapping.get("parser", "csv")
                    if parser == "csv":
                        is_iterable = True
                        header = field_mapping.get("header", True)
                        fieldnames = field_mapping.get("fieldnames")
                        delimiter = field_mapping.get("delimiter", ",")
                        rows = read_csv_file(
                            filepath,
                            header=header,
                            fieldnames=fieldnames,
                            delimiter=delimiter,
                        )
                category = field_mapping["category"]
                match category:
                    case "AL_D164":
                        callback = parse_AL_D164_shp
                    case "rnaddrkor":
                        callback = parse_rnaddrkor
                    case "jibun":
                        callback = parse_jibun_rnaddrkor
                    case "동네":
                        callback = parse_region
                    case "건물":
                        callback = parse_apartment
                    case "학교":
                        callback = parse_school
                    case "역사":
                        callback = parse_subway_station
                    case "병원":
                        callback = parse_large_hospital
                    case "마트":
                        callback = parse_large_supermarket
                    case "공원":
                        callback = parse_park
                    case _:
                        continue

                prefix = f"[{file_extension.strip('.')}] [{filename}]"
                context = contexts.setdefault(category, {})
                if is_iterable:
                    def run(idx: int, row: dict[str, Any]):
                        result = callback(row, field_mapping, context)
                        if not result: return

                        source_id = get_field_value(row, field_mapping["id"])
                        context.setdefault("results", {})[source_id] = result
                    run_with_progress(rows, prefix, run, interval=PROGRESS_PRINT)
                else:
                    def run(idx: int, filepath: str):
                        callback(filepath, field_mapping, context)
                    run_with_progress([filepath], prefix, run, interval=PROGRESS_PRINT)

    print(f"데이터 정리 중...")
    for category in contexts:
        print(f"  - {category}")
        context = contexts[category]
        match category:
            case "동네":
                callback = post_parse_region
            case "역사":
                callback = post_parse_subway_station
            case _:
                continue
        callback(context)

    print(f"데이터 삽입 중...")
    for category in contexts:
        match category:
            case "동네":
                Model = Region
            case "건물":
                Model = Property
            case _:
                Model = Infrastructure

        context = contexts[category]
        results = context.get("results") or {}
        items = list(results.values())
        def run(idx: int, result):
            if not result: return
            ins = get_model_instance(Model, result)
            if ins:
                for key, val in result.items():
                    setattr(ins, key, val)
            else:
                ins = Model(**result)
                db.add(ins)
            ins.deleted_at = None
            context.setdefault("instances", {})[result["source_id"]] = ins
        run_with_progress(items, f"[{category}]", run, interval=PROGRESS_PRINT)

    print(f"테이블 관계 설정 중...")
    connect_relationships(contexts)

    print(f"데이터 soft delete 처리 중...")
    for model, curr_map in MAP_ROUTER.items():
        items = list(curr_map.values())
        def run(idx: int, ins):
            ins.deleted_at = ins.deleted_at or func.now()
        run_with_progress(items, f"[{model.__tablename__}]", run, interval=PROGRESS_PRINT)


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
        
        files = list(get_files(
            directory_path,
            extensions=[".csv", ".txt", ".shp"],
            recursive=True,
        ))

        _main(db, files)
    except Exception as e:
        print()
        print(f"데이터 삽입 중 오류가 발생했습니다. 롤백을 진행합니다. ({e})")
        db.rollback()
        raise e
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
