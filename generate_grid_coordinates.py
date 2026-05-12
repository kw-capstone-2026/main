"""
격자 ID → 좌표 변환 (최종 버전)
Grid ID → TM 좌표 → WGS84 좌표
"""

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import re
from pathlib import Path

print("="*70)
print("🗺️  격자 좌표 생성")
print("="*70)

# 기준점 (100m 격자로 검증됨!)
ORIGIN_X = 852500
ORIGIN_Y = 1838125

print(f"\n기준점 (100m 격자로 검증 완료!):")
print(f"  X: {ORIGIN_X:,}")
print(f"  Y: {ORIGIN_Y:,}")

# DS5 분기별 데이터 로드
print("\n" + "="*70)
print("📂 데이터 로드")
print("="*70)

ds5_path = Path('data/quarterly/grid_quarterly_all.parquet')
df = pd.read_parquet(ds5_path)

print(f"✅ 격자 데이터: {len(df):,}행")
print(f"✅ 고유 격자: {df['grid_id'].nunique():,}개")

# Grid ID 파싱 함수
def parse_grid_id(grid_id):
    """다사35005075 → (3500, 5075)"""
    numbers = re.findall(r'\d+', str(grid_id))
    if numbers and len(numbers[0]) == 8:
        num = numbers[0]
        x = int(num[:4])
        y = int(num[4:])
        return x, y
    return None, None

# 고유 격자 목록
print("\n" + "="*70)
print("🔢 격자 번호 추출")
print("="*70)

unique_grids = df['grid_id'].unique()
print(f"처리할 격자: {len(unique_grids):,}개")

grid_coords = []

for grid_id in unique_grids:
    x_grid, y_grid = parse_grid_id(grid_id)
    
    if x_grid is not None:
        # TM 좌표 계산
        tm_x = ORIGIN_X + (x_grid * 25)
        tm_y = ORIGIN_Y + (y_grid * 25)
        
        grid_coords.append({
            'grid_id': grid_id,
            'x_grid': x_grid,
            'y_grid': y_grid,
            'tm_x': tm_x,
            'tm_y': tm_y
        })

df_coords = pd.DataFrame(grid_coords)

print(f"✅ 좌표 생성 완료: {len(df_coords):,}개")

# TM → WGS84 변환
print("\n" + "="*70)
print("🌐 좌표계 변환 (TM → WGS84)")
print("="*70)

# GeoDataFrame 생성 (TM 좌표계)
geometry = [Point(xy) for xy in zip(df_coords['tm_x'], df_coords['tm_y'])]
gdf = gpd.GeoDataFrame(df_coords, geometry=geometry, crs='EPSG:5179')

print(f"  원본 좌표계: {gdf.crs}")

# WGS84로 변환
gdf = gdf.to_crs('EPSG:4326')

print(f"  변환 좌표계: {gdf.crs}")

# 위도/경도 추출
df_coords['lon'] = gdf.geometry.x
df_coords['lat'] = gdf.geometry.y

print(f"✅ 변환 완료")

# 샘플 확인
print("\n" + "="*70)
print("📍 좌표 샘플 (상위 5개):")
print("="*70)
print(df_coords[['grid_id', 'tm_x', 'tm_y', 'lon', 'lat']].head())

# 범위 확인
print("\n" + "="*70)
print("📊 좌표 범위:")
print("="*70)
print(f"TM X: {df_coords['tm_x'].min():,.0f} ~ {df_coords['tm_x'].max():,.0f}")
print(f"TM Y: {df_coords['tm_y'].min():,.0f} ~ {df_coords['tm_y'].max():,.0f}")
print(f"경도: {df_coords['lon'].min():.6f} ~ {df_coords['lon'].max():.6f}")
print(f"위도: {df_coords['lat'].min():.6f} ~ {df_coords['lat'].max():.6f}")

# 서울 범위 확인
seoul_lon_range = (126.7, 127.2)
seoul_lat_range = (37.4, 37.7)

in_seoul = (
    (df_coords['lon'] >= seoul_lon_range[0]) &
    (df_coords['lon'] <= seoul_lon_range[1]) &
    (df_coords['lat'] >= seoul_lat_range[0]) &
    (df_coords['lat'] <= seoul_lat_range[1])
)

print(f"\n서울 범위 내 격자: {in_seoul.sum():,}개 / {len(df_coords):,}개 ({in_seoul.mean()*100:.1f}%)")

if in_seoul.mean() < 0.8:
    print("\n⚠️  경고: 서울 범위 밖 격자가 많습니다!")
    print("   기준점이 부정확할 수 있습니다.")
else:
    print("\n✅ 대부분 격자가 서울 범위 내에 있습니다!")

# 저장
print("\n" + "="*70)
print("💾 저장")
print("="*70)

output_path = Path('data/grid_coordinates.parquet')
output_path.parent.mkdir(parents=True, exist_ok=True)

# 필요한 컬럼만 저장
df_final = df_coords[['grid_id', 'lat', 'lon']].copy()
df_final.to_parquet(output_path, index=False)

file_size = output_path.stat().st_size / 1024
print(f"✅ 저장 완료: {output_path}")
print(f"   파일 크기: {file_size:.1f}KB")
print(f"   격자 수: {len(df_final):,}개")

# 최종 확인
print("\n" + "="*70)
print("🎉 완료!")
print("="*70)
print(f"""
생성 파일: data/grid_coordinates.parquet
격자 수: {len(df_final):,}개
컬럼: grid_id, lat, lon

다음 단계:
  python grid_to_commercial.py
""")

print("="*70)
