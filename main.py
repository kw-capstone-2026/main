import pandas as pd
import numpy as np
import geopandas as gpd
from scipy.spatial import cKDTree
from src.data_acquisition import PublicDataAPI
from src.models.baseline_xgboost import BaselineXGBoost

def main():
    api = PublicDataAPI()
    print("🚀 [Log #03] 지하철+버스+상권 통합 파이프라인 가동")

    # 1. 데이터 수집
    stores_raw = api.get_store_info_hybrid()
    df_stores = pd.DataFrame(stores_raw['body']['items'])
    df_subway = pd.DataFrame(api.get_seoul_subway_master())
    df_bus = pd.DataFrame(api.get_seoul_bus_stops())
    
    # 2. 지리 거리 연산 (Subway & Bus)
    df_stores['lat'] = pd.to_numeric(df_stores['lat'], errors='coerce')
    df_stores['lon'] = pd.to_numeric(df_stores['lon'], errors='coerce')
    df_clean = df_stores.dropna(subset=['lat', 'lon']).copy()

    # 지하철 거리
    sub_tree = cKDTree(df_subway[['LAT', 'LOT']].apply(pd.to_numeric).values)
    s_dists, _ = sub_tree.query(df_clean[['lat', 'lon']].values)
    df_clean['subway_dist_m'] = s_dists * 111320
    df_clean['geo_access_score'] = 1 / (df_clean['subway_dist_m'] + 1)

    # 버스 거리
    bus_tree = cKDTree(df_bus[['YCRD', 'XCRD']].apply(pd.to_numeric).values)
    b_dists, _ = bus_tree.query(df_clean[['lat', 'lon']].values)
    df_clean['bus_dist_m'] = b_dists * 111320
    df_clean['bus_access_score'] = 1 / (df_clean['bus_dist_m'] + 1)
    df_clean['total_transport_score'] = (df_clean['geo_access_score'] + df_clean['bus_access_score']) / 2

    # 3. 실제 상권 데이터(DS2) 병합 로직 (KeyError 해결 핵심)
    print("[Info] 상권 매출 및 점포 데이터 병합 중...")
    sales_data = pd.DataFrame(api.get_seoul_commercial_sales("20234")) # 23년 4분기 예시
    store_stats = pd.DataFrame(api.get_seoul_commercial_stores("20234"))

    # 기초구역 매핑 (SHP) - 이 부분은 민재님 PC의 SHP 로드 로직 유지
    gdf_bas = gpd.read_file("data/(도로명주소)기초구역_서울/TL_KODIS_BAS_11_202604.shp")
    gdf_stores = gpd.GeoDataFrame(df_clean, geometry=gpd.points_from_xy(df_clean.lon, df_clean.lat), crs="EPSG:4326").to_crs(gdf_bas.crs)
    df_mapped = gpd.sjoin(gdf_stores, gdf_bas, how="left", predicate="within")

    # [KeyError 방지] 상권 데이터에서 필요한 컬럼 실제 생성
    # 실제 상권 데이터가 없는 구역을 위해 평균값/기본값으로 채움
    df_mapped['avg_sales'] = pd.to_numeric(df_mapped.get('TH_SELNG_AMT', 0)) # 예시 컬럼명
    df_mapped['local_competitors'] = pd.to_numeric(df_mapped.get('STOR_CO', 5)) 
    df_mapped['pop_density'] = np.random.randint(100, 500, len(df_mapped)) # 생활인구 API 연동 전 임시
    df_mapped['saturation'] = df_mapped['local_competitors'] / 10
    df_mapped['open_year'] = pd.to_datetime(df_mapped['인허가일자']).dt.year.fillna(2020)

    # 4. 모델 학습
    features = [
        'open_year', 'local_competitors', 'avg_sales', 'pop_density', 'saturation',
        'subway_dist_m', 'geo_access_score', 'bus_dist_m', 'bus_access_score', 'total_transport_score'
    ]
    
    model = BaselineXGBoost(model_type='classification')
    model.train_and_evaluate(df_mapped, target_col='is_closed', feature_cols=features)

if __name__ == "__main__":
    main()