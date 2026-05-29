import pandas as pd
import geopandas as gpd

from app.utils import sniff_encoding


def read_pandas(
    file_path: str,
    **kwargs,
) -> pd.DataFrame:
    try:
        enc = sniff_encoding(file_path)
        return pd.read_csv(
            file_path,
            encoding=enc,
            sep="|",
            header=None,
            dtype=str,
            **kwargs,
        )
    except FileNotFoundError:
        print(f"파일을 찾을 수 없습니다: {file_path}")
        raise e
    except Exception as e:
        print(f"파일 읽기 중 오류 발생: {e}")
        raise e

def read_shp_file(
    file_path: str,
    *,
    columns: list[str] | None = None,
    rename_columns: dict[str, str] | None = None,
):
    """
    SHP 파일을 읽어 리스트로 반환합니다.
    
    Args:
        file_path (str): SHP 파일 경로
        columns (list[str] | None): SHP 컬럼명을 직접 지정할 때 사용
        rename_columns (dict[str, str] | None): 기존 컬럼명을 새 컬럼명으로 매핑할 때 사용 (예: {"old_name": "new_name"})
        
    Returns:
        GeoDataFrame: SHP 파일의 데이터를 GeoDataFrame 형태로 반환
    """

    try:
        enc = sniff_encoding(file_path)
        gdf = gpd.read_file(file_path, encoding=enc)
        if columns and len(gdf.columns) == len(columns):
            gdf.columns = columns
        elif rename_columns:
            gdf.rename(columns=rename_columns, inplace=True)
        return gdf
    except FileNotFoundError:
        print(f"파일을 찾을 수 없습니다: {file_path}")
        raise e
    except Exception as e:
        print(f"파일 읽기 중 오류 발생: {e}")
        raise e


def find_polygon_from_coords(gdf: gpd.GeoDataFrame, lat: float, lon: float):
    """
    주어진 좌표가 포함된 폴리곤을 찾습니다.
    
    Args:
        gdf (GeoDataFrame): 폴리곤이 포함된 GeoDataFrame
        lat (float): 위도
        lon (float): 경도
        
    Returns:
        GeoSeries | None: 해당 좌표가 포함된 폴리곤의 GeoSeries 또는 None
    """

    raw_point = gpd.points_from_xy([lon], [lat], crs="EPSG:4326")[0]
    point_5179 = gpd.GeoSeries([raw_point], crs="EPSG:4326").to_crs(gdf.crs).iloc[0]
    result = gdf[gdf.geometry.contains(point_5179)]
    if result.empty:
        result = gdf[gdf.geometry.within(point_5179)]
    if result.empty:
        nearest_idx = gdf.geometry.distance(point_5179).idxmin()
        return gdf.loc[[nearest_idx]]
    if len(result) > 1:
        distances = result.geometry.centroid.distance(point_5179)
        result = result.loc[[distances.idxmin()]]
    return result
