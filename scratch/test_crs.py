import pyproj
import pandas as pd

# 샘플 데이터 (서울시 LOCALDATA에서 흔히 보이는 값)
x_sample = 198422.31
y_sample = 450912.34

# 후보 좌표계 리스트
crs_list = ["EPSG:2097", "EPSG:5174", "EPSG:5181", "EPSG:5179"]

print(f"Testing Point: X={x_sample}, Y={y_sample}")

for crs_name in crs_list:
    try:
        # 1. 원래 순서 (X, Y)
        transformer = pyproj.Transformer.from_crs(crs_name, "EPSG:4326", always_xy=True)
        lon, lat = transformer.transform(x_sample, y_sample)
        if 126 < lon < 128 and 36 < lat < 38:
            print(f"FOUND (Standard X,Y): {crs_name} -> Lat: {lat:.5f}, Lon: {lon:.5f}")
            
        # 2. 바뀐 순서 (Y, X)
        lon_inv, lat_inv = transformer.transform(y_sample, x_sample)
        if 126 < lon_inv < 128 and 36 < lat_inv < 38:
            print(f"FOUND (Swapped Y,X): {crs_name} -> Lat: {lat_inv:.5f}, Lon: {lon_inv:.5f}")
            
    except Exception as e:
        print(f"ERROR {crs_name}: {e}")
