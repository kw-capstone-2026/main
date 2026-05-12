"""
격자 → 상권 변환 스크립트
DS5 격자 데이터를 상권 단위로 집계합니다.
"""

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from pathlib import Path
from tqdm import tqdm

print("\n" + "="*70)
print("🗺️  격자 → 상권 변환 파이프라인")
print("="*70)

# ===========================================
# Step 1: 데이터 로드
# ===========================================

print("\n📂 Step 1: 데이터 로드")
print("-" * 70)

# DS5 격자 데이터 로드
ds5_path = Path('data/quarterly/grid_quarterly_all.parquet')
print(f"DS5 데이터 로드: {ds5_path}")
df_grid = pd.read_parquet(ds5_path)

print(f"  ✅ 격자 데이터: {len(df_grid):,}행")
print(f"  ✅ 고유 격자: {df_grid['grid_id'].nunique():,}개")
print(f"  ✅ 분기 수: {df_grid['년분기'].nunique()}개")

# 상권 맵 데이터 로드
shp_path = Path('서울시_상권분석서비스_영역-상권_.shp')
print(f"\n상권 맵 로드: {shp_path}")
gdf_sanggwon = gpd.read_file(shp_path)

print(f"  ✅ 상권 개수: {len(gdf_sanggwon):,}개")
print(f"  ✅ 좌표계: {gdf_sanggwon.crs}")

# 좌표계를 EPSG:4326으로 변환
if gdf_sanggwon.crs != 'EPSG:4326':
    print(f"  🔄 좌표계 변환: {gdf_sanggwon.crs} → EPSG:4326")
    gdf_sanggwon = gdf_sanggwon.to_crs('EPSG:4326')

# ===========================================
# Step 2: 격자 좌표 정보 추가
# ===========================================

print("\n📍 Step 2: 격자 좌표 정보 추가")
print("-" * 70)

# 격자 좌표 매핑 파일 로드
# (이 파일은 extract_grid_coordinates.py로 생성)
coord_path = Path('data/grid_coordinates.parquet')

if not coord_path.exists():
    print(f"❌ 격자 좌표 파일이 없습니다: {coord_path}")
    print("\n먼저 extract_grid_coordinates.py를 실행하여")
    print("격자 좌표 정보를 생성해주세요!")
    exit(1)

df_coords = pd.read_parquet(coord_path)
print(f"  ✅ 격자 좌표: {len(df_coords):,}개")

# 격자 데이터와 좌표 조인
print("\n격자 데이터 + 좌표 조인...")
df_grid = df_grid.merge(df_coords, on='grid_id', how='left')

# 좌표 없는 격자 확인
missing = df_grid[df_grid['lon'].isna()]
if len(missing) > 0:
    print(f"  ⚠️  좌표 없는 격자: {len(missing):,}개 (제외됨)")
    df_grid = df_grid.dropna(subset=['lon', 'lat'])

print(f"  ✅ 좌표 있는 격자: {len(df_grid):,}행")

# GeoDataFrame 생성
print("\nGeoDataFrame 변환...")
geometry = [Point(xy) for xy in zip(df_grid['lon'], df_grid['lat'])]
gdf_grid = gpd.GeoDataFrame(df_grid, geometry=geometry, crs='EPSG:4326')

print(f"  ✅ GeoDataFrame 생성 완료")

# ===========================================
# Step 3: Spatial Join (격자 → 상권)
# ===========================================

print("\n🔗 Step 3: Spatial Join (격자 → 상권 매칭)")
print("-" * 70)

print("격자가 어느 상권에 속하는지 계산 중...")
print("(시간이 좀 걸릴 수 있습니다...)")

# Spatial Join: 격자 point가 상권 polygon 안에 있는지
gdf_joined = gpd.sjoin(
    gdf_grid,
    gdf_sanggwon[['TRDAR_CD', 'geometry']],
    how='left',
    predicate='within'
)

print(f"  ✅ Spatial Join 완료")

# 상권에 속한 격자 수 확인
matched = gdf_joined[gdf_joined['TRDAR_CD'].notna()]
print(f"  ✅ 상권 매칭: {len(matched):,}행")
print(f"  ⚠️  미매칭: {len(gdf_joined) - len(matched):,}행")

# ===========================================
# Step 4: 상권별 집계
# ===========================================

print("\n📊 Step 4: 상권별 유동인구 집계")
print("-" * 70)

# 시나리오 컬럼
scenario_cols = [
    '주중_오전_avg', '주중_점심_avg', '주중_저녁_avg', '주중_야간_avg',
    '주말_주간_avg', '주말_야간_avg'
]

print("상권별 합산 중...")

# 상권 × 분기별 집계
df_sanggwon_agg = gdf_joined.groupby(['TRDAR_CD', '년분기']).agg({
    **{col: 'sum' for col in scenario_cols},
    'grid_id': 'count'  # 격자 개수
}).reset_index()

df_sanggwon_agg.rename(columns={'grid_id': 'grid_count'}, inplace=True)

print(f"  ✅ 집계 완료: {len(df_sanggwon_agg):,}행")
print(f"  ✅ 고유 상권: {df_sanggwon_agg['TRDAR_CD'].nunique():,}개")
print(f"  ✅ 분기 수: {df_sanggwon_agg['년분기'].nunique()}개")

# ===========================================
# Step 5: 질적 지표 계산
# ===========================================

print("\n📈 Step 5: 질적 지표 계산")
print("-" * 70)

# 1. 주야간 비율
print("  1️⃣  주야간 비율 계산...")
df_sanggwon_agg['주간인구'] = (
    df_sanggwon_agg['주중_오전_avg'] +
    df_sanggwon_agg['주중_점심_avg'] +
    df_sanggwon_agg['주말_주간_avg']
) / 3

df_sanggwon_agg['야간인구'] = (
    df_sanggwon_agg['주중_저녁_avg'] +
    df_sanggwon_agg['주중_야간_avg'] +
    df_sanggwon_agg['주말_야간_avg']
) / 3

df_sanggwon_agg['주야간비율'] = (
    df_sanggwon_agg['주간인구'] / (df_sanggwon_agg['야간인구'] + 1)
)

# 2. 성장 트렌드 (분기별 인구 변화)
print("  2️⃣  성장 트렌드 계산...")

# 전체 평균 인구
df_sanggwon_agg['평균인구'] = df_sanggwon_agg[scenario_cols].mean(axis=1)

# 상권별 트렌드 계산
trends = []
for sanggwon_cd in tqdm(df_sanggwon_agg['TRDAR_CD'].unique(), desc="트렌드"):
    sanggwon_data = df_sanggwon_agg[
        df_sanggwon_agg['TRDAR_CD'] == sanggwon_cd
    ].sort_values('년분기')
    
    if len(sanggwon_data) >= 2:
        # 선형 회귀 (간단 버전)
        x = range(len(sanggwon_data))
        y = sanggwon_data['평균인구'].values
        
        # 기울기 계산
        if len(x) > 1:
            from numpy import polyfit
            slope, _ = polyfit(x, y, 1)
        else:
            slope = 0
    else:
        slope = 0
    
    trends.append({'TRDAR_CD': sanggwon_cd, 'population_slope': slope})

df_trends = pd.DataFrame(trends)
df_sanggwon_agg = df_sanggwon_agg.merge(df_trends, on='TRDAR_CD', how='left')

print(f"  ✅ 트렌드 계산 완료")

# 3. 인구 집중도 (Entropy) - 상권별 계산
print("  3️⃣  인구 집중도 계산...")

# 상권별로 격자 인구 분포의 엔트로피 계산
from scipy.stats import entropy

concentrations = []
for sanggwon_cd in tqdm(df_sanggwon_agg['TRDAR_CD'].unique(), desc="집중도"):
    # 해당 상권의 격자들
    grids_in_sanggwon = gdf_joined[gdf_joined['TRDAR_CD'] == sanggwon_cd]
    
    if len(grids_in_sanggwon) > 0:
        # 각 격자의 평균 인구
        grid_pops = grids_in_sanggwon[scenario_cols].mean(axis=1).values
        
        # 엔트로피 계산 (값이 클수록 고르게 분포)
        if len(grid_pops) > 1 and grid_pops.sum() > 0:
            probs = grid_pops / grid_pops.sum()
            ent = entropy(probs)
        else:
            ent = 0
    else:
        ent = 0
    
    concentrations.append({
        'TRDAR_CD': sanggwon_cd,
        'population_entropy': ent
    })

df_concentration = pd.DataFrame(concentrations)
df_sanggwon_agg = df_sanggwon_agg.merge(
    df_concentration, on='TRDAR_CD', how='left'
)

print(f"  ✅ 집중도 계산 완료")

# ===========================================
# Step 6: 최종 포맷 변환
# ===========================================

print("\n💾 Step 6: 최종 파일 생성")
print("-" * 70)

# 컬럼명 변경 (요청 규격에 맞춤)
df_final = df_sanggwon_agg.rename(columns={
    'TRDAR_CD': '상권_코드',
    '년분기': '기준_년분기_코드'
})

# 필수 컬럼 순서
required_cols = ['상권_코드', '기준_년분기_코드']
other_cols = [col for col in df_final.columns if col not in required_cols]
df_final = df_final[required_cols + other_cols]

# 저장
output_path = Path('data/commercial_population_quarterly.parquet')
output_path.parent.mkdir(parents=True, exist_ok=True)

df_final.to_parquet(output_path, index=False)

file_size = output_path.stat().st_size / 1024**2
print(f"\n✅ 저장 완료: {output_path}")
print(f"   파일 크기: {file_size:.1f}MB")

# 최종 통계
print("\n" + "="*70)
print("📊 최종 결과")
print("="*70)
print(f"총 행 수: {len(df_final):,}행")
print(f"상권 수: {df_final['상권_코드'].nunique():,}개")
print(f"분기 수: {df_final['기준_년분기_코드'].nunique()}개")
print(f"컬럼 수: {len(df_final.columns)}개")

print("\n📋 컬럼 목록:")
for i, col in enumerate(df_final.columns, 1):
    print(f"  {i:2d}. {col}")

print("\n📌 샘플 데이터 (상위 5행):")
print(df_final.head().to_string())

print("\n" + "="*70)
print("🎉 변환 완료!")
print("="*70)
