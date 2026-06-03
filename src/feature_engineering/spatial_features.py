"""
feature_engineering/spatial_features.py
-----------------------------------------
담당: 팀원 B (피처 엔지니어링 파트)

목적: 점포의 위치(GPS)를 기준으로 주변 마이크로 POI 데이터와
      공간 연산(반경 내 개수, 가장 가까운 거리 등)을 수행하여
      최종 피처 테이블을 생성합니다.

주요 피처 예시:
    - dist_nearest_subway     : 가장 가까운 지하철역까지의 거리 (m)
    - cnt_subway_500m         : 반경 500m 내 지하철역 수
    - dist_nearest_kindergarten: 가장 가까운 유치원까지의 거리 (m)
    - cnt_competitor_100m     : 반경 100m 내 동일 업종 경쟁 점포 수
    - cnt_supermarket_1km     : 반경 1km 내 대형마트/슈퍼마켓 수
"""

import geopandas as gpd
from shapely.geometry import Point


def compute_nearest_distance(stores_gdf: gpd.GeoDataFrame, poi_gdf: gpd.GeoDataFrame, col_name: str) -> gpd.GeoDataFrame:
    """각 점포로부터 가장 가까운 POI까지의 거리(m)를 계산합니다."""
    # TODO: EPSG:5179 (미터 단위 좌표계)로 변환 후 nearest 거리 연산
    raise NotImplementedError("compute_nearest_distance() 구현 필요")


def compute_count_within_radius(stores_gdf: gpd.GeoDataFrame, poi_gdf: gpd.GeoDataFrame, radius_m: int, col_name: str) -> gpd.GeoDataFrame:
    """각 점포 반경 radius_m(미터) 내 POI 개수를 계산합니다."""
    # TODO: sjoin 또는 buffer를 이용한 공간 조인 구현
    raise NotImplementedError("compute_count_within_radius() 구현 필요")
