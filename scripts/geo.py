import admdongkor as adk
import geopandas as gpd
from decimal import Decimal
from shapely.geometry import Point


gdf = adk.get("20260401", "emd")
gdf = gdf.set_crs(epsg=5179)
gdf = gdf.to_crs(epsg=4326)

def get_address_from_coords(lat: Decimal, lon: Decimal) -> tuple[str, str, str] | None:
    point = Point(lon, lat)
    result = gdf[gdf.contains(point)]
    if result.empty:
        return None
    sido = result["sidonm"].iloc[0]
    sgg = result["sggnm"].iloc[0]
    emd = result["emdnm"].iloc[0]
    return sido, sgg, emd
