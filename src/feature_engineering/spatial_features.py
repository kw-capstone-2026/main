"""
feature_engineering/spatial_features.py
"""

import os
import pickle
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from scipy.spatial import cKDTree
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.data_acquisition import PublicDataAPI


# ───────────────────────────────────────────────────────────
# 공통 공간 연산 함수 (다른 피처 모듈에서도 재사용 가능)
# ───────────────────────────────────────────────────────────

def compute_nearest_distance(
    stores_gdf: gpd.GeoDataFrame,
    poi_gdf: gpd.GeoDataFrame,
    col_name: str
) -> gpd.GeoDataFrame:
    """
    각 점포로부터 가장 가까운 POI까지의 거리(m)를 계산합니다.
    EPSG:5179 (미터 단위) 좌표계로 내부 변환 후 cKDTree로 연산합니다.
    """
    stores_proj = stores_gdf.to_crs(epsg=5179)
    pois_proj   = poi_gdf.to_crs(epsg=5179)

    store_coords = np.array([(g.x, g.y) for g in stores_proj.geometry])
    poi_coords   = np.array([(g.x, g.y) for g in pois_proj.geometry])

    result = stores_gdf.copy()
    if len(poi_coords) == 0:
        result[col_name] = np.nan
        return result

    tree = cKDTree(poi_coords)
    distances, _ = tree.query(store_coords, k=1)
    result[col_name] = distances
    return result


def compute_count_within_radius(
    stores_gdf: gpd.GeoDataFrame,
    poi_gdf: gpd.GeoDataFrame,
    radius_m: int,
    col_name: str
) -> gpd.GeoDataFrame:
    """
    각 점포 반경 radius_m(미터) 내 POI 개수를 계산합니다.
    """
    stores_proj = stores_gdf.to_crs(epsg=5179)
    pois_proj   = poi_gdf.to_crs(epsg=5179)

    store_coords = np.array([(g.x, g.y) for g in stores_proj.geometry])
    poi_coords   = np.array([(g.x, g.y) for g in pois_proj.geometry])

    result = stores_gdf.copy()
    if len(poi_coords) == 0:
        result[col_name] = 0
        return result

    tree   = cKDTree(poi_coords)
    counts = tree.query_ball_point(store_coords, r=radius_m, return_length=True)
    result[col_name] = counts
    return result

"""
지리적/물리적 제약 (Geographic & Physical Constraints) 피처 생성 모듈

생성 피처:
    - elevation      : 기초구역(BAS_ID) 중심점의 고도(m) — 브이월드 LT_C_LHFPC
    - slope          : 경사도 proxy (반경 300m 이내 이웃 블록 고도 표준편차)
    - dist_crosswalk : 가장 가까운 횡단보도까지의 거리(m)
"""
# ───────────────────────────────────────────────────────────
# 피처 1·2: 고도(elevation) + 경사도(slope)
# ───────────────────────────────────────────────────────────

def _load_elevation_cache(cache_path: str) -> dict:
    if os.path.exists(cache_path):
        with open(cache_path, 'rb') as f:
            return pickle.load(f)
    return {}


def _save_elevation_cache(cache: dict, cache_path: str) -> None:
    with open(cache_path, 'wb') as f:
        pickle.dump(cache, f)


def _fetch_elevation_for_bas(
    bas_centroids: pd.DataFrame,
    api: "PublicDataAPI",
    cache_path: str
) -> dict:
    """
    BAS_ID별 중심 좌표를 VWorld API로 조회해 고도 캐시를 채웁니다.
    중간마다 100건 단위로 저장하여 API 중단 시 손실을 최소화합니다.
    """
    cache   = _load_elevation_cache(cache_path)
    missing = bas_centroids[~bas_centroids['BAS_ID'].isin(cache)]

    print(f"[Elevation] Cached: {len(cache)}, Fetching: {len(missing)} BAS_IDs...")

    for i, (_, row) in enumerate(missing.iterrows()):
        elev = api.get_elevation_srtm(lat=row['lat'], lng=row['lng'])
        cache[row['BAS_ID']] = elev if elev is not None else np.nan

        if (i + 1) % 100 == 0:
            _save_elevation_cache(cache, cache_path)
            print(f"  ... {i + 1}/{len(missing)} 완료 (중간 저장)")

    _save_elevation_cache(cache, cache_path)
    return cache


def add_elevation_slope_features(
    stores_gdf: gpd.GeoDataFrame,
    api: "PublicDataAPI",
    cache_path: str = 'scratch/elevation_cache.pkl'
) -> gpd.GeoDataFrame:
    """
    각 점포의 기초구역(BAS_ID) 중심점 기준 고도(m)와 경사도(%)를 추가합니다.

    경사도 계산 방식:
        반경 300m 내 이웃 BAS_ID 고도값들의 표준편차를 경사 proxy로 사용합니다.
        (개별 점포마다 DEM을 4방향 조회하면 API 호출이 4배 증가하므로 BAS_ID 단위로 근사)
    """
    result = stores_gdf.copy()

    if 'BAS_ID' not in result.columns:
        print("[Warning] BAS_ID 없음 — elevation/slope 피처 생략")
        result['elevation'] = np.nan
        result['slope']     = np.nan
        return result

    # BAS_ID별 중심 좌표 (WGS84)
    stores_4326     = result.to_crs(epsg=4326)
    stores_4326['_lat'] = stores_4326.geometry.y
    stores_4326['_lng'] = stores_4326.geometry.x
    bas_centroids = (
        stores_4326.groupby('BAS_ID')[['_lat', '_lng']]
        .mean()
        .reset_index()
        .rename(columns={'_lat': 'lat', '_lng': 'lng'})
    )

    # 고도 캐시 조회
    elev_cache = _fetch_elevation_for_bas(bas_centroids, api, cache_path)
    result['elevation'] = result['BAS_ID'].map(elev_cache)

    # 경사도: 이웃 BAS_ID 고도값의 표준편차
    bas_elev = bas_centroids.copy()
    bas_elev['elevation'] = bas_elev['BAS_ID'].map(elev_cache)

    bas_proj = gpd.GeoDataFrame(
        bas_elev,
        geometry=gpd.points_from_xy(bas_elev['lng'], bas_elev['lat']),
        crs='EPSG:4326'
    ).to_crs(epsg=5179)

    coords = np.array([(g.x, g.y) for g in bas_proj.geometry])
    tree   = cKDTree(coords)

    slope_rows = []
    for i, row in bas_elev.iterrows():
        neighbor_idx   = tree.query_ball_point(coords[list(bas_elev.index).index(i)], r=300)
        neighbor_elevs = [
            bas_elev.iloc[j]['elevation']
            for j in neighbor_idx
            if not np.isnan(bas_elev.iloc[j]['elevation'])
        ]
        slope_val = float(np.std(neighbor_elevs)) if len(neighbor_elevs) > 1 else 0.0
        slope_rows.append({'BAS_ID': row['BAS_ID'], 'slope': slope_val})

    slope_df = pd.DataFrame(slope_rows)
    result   = result.merge(slope_df, on='BAS_ID', how='left')

    valid_elev = result['elevation'].notna().sum()
    print(f"[GeoFeature] elevation 유효: {valid_elev}/{len(result)}건  "
          f"mean={result['elevation'].mean():.1f}m  "
          f"slope mean={result['slope'].mean():.3f}")
    return result


# ───────────────────────────────────────────────────────────
# 지리적 제약 피처 3: 횡단보도 거리(dist_crosswalk)
# ───────────────────────────────────────────────────────────

def _load_crosswalk_gdf(
    api: "PublicDataAPI",
    cache_path: str
) -> Optional[gpd.GeoDataFrame]:
    """횡단보도 GeoDataFrame을 캐시에서 로드하거나 API로 수집합니다."""
    if os.path.exists(cache_path):
        with open(cache_path, 'rb') as f:
            gdf = pickle.load(f)
        print(f"[Cache] 횡단보도 {len(gdf)}건 캐시 로드.")
        return gdf

    data = api.get_crosswalk_locations_seoul()
    if not data:
        print("[Warning] 횡단보도 데이터 수집 실패.")
        return None

    gdf = gpd.GeoDataFrame(
        data,
        geometry=gpd.points_from_xy([r['lng'] for r in data], [r['lat'] for r in data]),
        crs='EPSG:4326'
    )
    with open(cache_path, 'wb') as f:
        pickle.dump(gdf, f)
    print(f"[API] 횡단보도 {len(gdf)}건 수집 및 캐시 저장.")
    return gdf


def add_crosswalk_distance(
    stores_gdf: gpd.GeoDataFrame,
    crosswalk_gdf: gpd.GeoDataFrame
) -> gpd.GeoDataFrame:
    """각 점포로부터 가장 가까운 횡단보도까지의 거리(m)를 추가합니다."""
    return compute_nearest_distance(stores_gdf, crosswalk_gdf, 'dist_crosswalk')


# ───────────────────────────────────────────────────────────
# 피처 4·5: 보행 단절 — 지상 철도(dist_railway), 하천(dist_river)
# ───────────────────────────────────────────────────────────

def _load_barrier_gdf(
    cache_path: str,
    fetch_fn,
    label: str
) -> Optional[gpd.GeoDataFrame]:
    """장벽 GeoDataFrame을 캐시에서 로드하거나 fetch_fn으로 수집합니다."""
    if os.path.exists(cache_path):
        with open(cache_path, 'rb') as f:
            gdf = pickle.load(f)
        print(f"[Cache] {label} {len(gdf)}건 캐시 로드.")
        return gdf

    gdf = fetch_fn()
    if gdf is None or len(gdf) == 0:
        print(f"[Warning] {label} 데이터 수집 실패.")
        return None

    with open(cache_path, 'wb') as f:
        pickle.dump(gdf, f)
    print(f"[OSM] {label} {len(gdf)}건 캐시 저장.")
    return gdf


def compute_nearest_line_distance(
    stores_gdf: gpd.GeoDataFrame,
    lines_gdf: gpd.GeoDataFrame,
    col_name: str
) -> gpd.GeoDataFrame:
    """
    각 점포로부터 가장 가까운 선형 피처(철도/하천)까지의 거리(m)를 계산합니다.
    선형 피처를 unary_union으로 합친 뒤 shapely distance로 계산합니다.
    """
    stores_proj = stores_gdf.to_crs(epsg=5179)
    lines_proj  = lines_gdf.to_crs(epsg=5179)

    merged_lines = lines_proj.geometry.union_all()

    result = stores_gdf.copy()
    result[col_name] = stores_proj.geometry.apply(
        lambda pt: pt.distance(merged_lines)
    ).values
    return result


def add_barrier_features(
    stores_gdf: gpd.GeoDataFrame,
    api: "PublicDataAPI",
    cache_dir: str = 'scratch'
) -> gpd.GeoDataFrame:
    """
    보행 단절 요인 거리 피처를 추가합니다.
        dist_railway : 가장 가까운 지상 철도까지 거리(m)
        dist_river   : 가장 가까운 하천까지 거리(m)
    """
    result = stores_gdf.copy()

    railway_gdf = _load_barrier_gdf(
        cache_path=os.path.join(cache_dir, 'railway_cache.pkl'),
        fetch_fn=api.get_railway_ground_seoul,
        label='지상 철도'
    )
    if railway_gdf is not None:
        result = compute_nearest_line_distance(result, railway_gdf, 'dist_railway')
        print(f"[GeoFeature] dist_railway 유효: {result['dist_railway'].notna().sum()}/{len(result)}건  "
              f"mean={result['dist_railway'].mean():.0f}m")
    else:
        result['dist_railway'] = np.nan

    river_gdf = _load_barrier_gdf(
        cache_path=os.path.join(cache_dir, 'river_cache.pkl'),
        fetch_fn=api.get_river_seoul,
        label='하천'
    )
    if river_gdf is not None:
        result = compute_nearest_line_distance(result, river_gdf, 'dist_river')
        print(f"[GeoFeature] dist_river 유효: {result['dist_river'].notna().sum()}/{len(result)}건  "
              f"mean={result['dist_river'].mean():.0f}m")
    else:
        result['dist_river'] = np.nan

    return result


# ───────────────────────────────────────────────────────────
# 통합 빌더
# ───────────────────────────────────────────────────────────

def build_geo_constraint_features(
    stores_gdf: gpd.GeoDataFrame,
    api: "PublicDataAPI",
    cache_dir: str = 'scratch'
) -> gpd.GeoDataFrame:
    """
    D5 지리적/물리적 제약 피처를 모두 빌드하여 반환합니다.

    추가되는 컬럼:
        elevation      (float): 고도(m)
        slope          (float): 경사도 proxy
        dist_crosswalk (float): 횡단보도까지 거리(m)
        dist_railway   (float): 지상 철도까지 거리(m)
        dist_river     (float): 하천까지 거리(m)
    """
    print("\n[GeoConstraints] 지리적/물리적 제약 피처 빌드 시작...")
    os.makedirs(cache_dir, exist_ok=True)

    result = add_elevation_slope_features(
        stores_gdf,
        api,
        cache_path=os.path.join(cache_dir, 'elevation_cache.pkl')
    )

    crosswalk_gdf = _load_crosswalk_gdf(
        api,
        cache_path=os.path.join(cache_dir, 'crosswalk_cache.pkl')
    )
    if crosswalk_gdf is not None:
        result = add_crosswalk_distance(result, crosswalk_gdf)
    else:
        result['dist_crosswalk'] = np.nan

    result = add_barrier_features(result, api, cache_dir=cache_dir)

    print(f"[GeoConstraints] 완료 — 추가된 피처: elevation, slope, dist_crosswalk, dist_railway, dist_river")
    return result
