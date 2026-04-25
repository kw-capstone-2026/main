import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

# 1. SHP 파일 로드 및 경계 확인
shp_path = "e:/capstone/kw-capstone-2026/data/(도로명주소)기초구역_서울/TL_KODIS_BAS_11_202604.shp"
bas_gdf = gpd.read_file(shp_path)
if bas_gdf.crs is None:
    bas_gdf.set_crs(epsg=5179, inplace=True)
else:
    bas_gdf = bas_gdf.to_crs(epsg=5179)

print(f"SHP File CRS: {bas_gdf.crs}")
print(f"SHP Bounds (MinX, MinY, MaxX, MaxY): {bas_gdf.total_bounds}")

# 2. 샘플 포인트 변환 테스트 (DS3 폐업 데이터 스타일)
# X=198422, Y=450912 (EPSG:2097) -> EPSG:5179 변환 테스트
from pyproj import Transformer
transformer = Transformer.from_crs("EPSG:2097", "EPSG:5179", always_xy=True)
p_x, p_y = transformer.transform(198422.31, 450912.34)

print(f"\nSample Point (EPSG:2097) -> EPSG:5179: X={p_x:.2f}, Y={p_y:.2f}")

# 3. 샘플 포인트 (WGS84) -> EPSG:5179 변환 테스트
transformer_wgs = Transformer.from_crs("EPSG:4326", "EPSG:5179", always_xy=True)
p_w_x, p_w_y = transformer_wgs.transform(126.98004, 37.56049)
print(f"Sample Point (WGS84) -> EPSG:5179: X={p_w_x:.2f}, Y={p_w_y:.2f}")

# 범위 비교
min_x, min_y, max_x, max_y = bas_gdf.total_bounds
if min_x <= p_x <= max_x and min_y <= p_y <= max_y:
    print("\n✅ Success: Closed Point is INSIDE SHP bounds!")
else:
    print("\n❌ Error: Closed Point is OUTSIDE SHP bounds.")

if min_x <= p_w_x <= max_x and min_y <= p_w_y <= max_y:
    print("✅ Success: Open Point (WGS84) is INSIDE SHP bounds!")
else:
    print("❌ Error: Open Point (WGS84) is OUTSIDE SHP bounds.")
