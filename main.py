import os
import pandas as pd
import numpy as np
from scipy.spatial import cKDTree
from dotenv import load_dotenv
from src.data_acquisition import DataAcquisition
from src.feature_merger import FeatureMerger
from src.models.baseline_xgboost import BaselineXGBoost

load_dotenv()

def main():
    api = DataAcquisition()
    merger = FeatureMerger()
    
    print("🚀 [Step 1] 전수 데이터 및 아파트 정보 수집 중...")
    df_raw = pd.DataFrame(api.get_store_info_hybrid()['body']['items'])
    df_sales = api.get_seoul_commercial_sales("20234")
    df_sub = api.get_seoul_subway()
    df_bus = api.get_seoul_bus_stops()
    df_large = api.get_seoul_large_stores()
    df_apt = api.get_seoul_apartments() # 신규

    print("🚀 [Step 2] 베이스라인 피처 병합 중...")
    df_prep = merger.calculate_survival_duration(df_raw)
    df_master = merger.create_master_table(df_prep, df_sales=df_sales)

    # 지리 연산을 위한 유효 좌표 필터링
    df_geo = df_master.dropna(subset=['lat', 'lon']).copy()
    coords = df_geo[['lat', 'lon']].values

    print("🚀 [Step 3] 고도화된 공간 연산 수행 중...")
    # 3-1. 지하철/버스 최단거리
    sub_tree = cKDTree(df_sub[['LAT', 'LOT']].apply(pd.to_numeric, errors='coerce').dropna().values)
    df_geo['subway_dist_m'] = sub_tree.query(coords)[0] * 111320

    bus_tree = cKDTree(df_bus[['YCRD', 'XCRD']].apply(pd.to_numeric, errors='coerce').dropna().values)
    df_geo['bus_dist_m'] = bus_tree.query(coords)[0] * 111320

    # 3-2. 대형마트 영향도
    df_large_clean = df_large.assign(
        X=pd.to_numeric(df_large['X'], errors='coerce'),
        Y=pd.to_numeric(df_large['Y'], errors='coerce')
    ).dropna(subset=['X', 'Y'])
    large_tree = cKDTree(df_large_clean[['Y', 'X']].values)
    df_geo['large_impact'] = 1 / (large_tree.query(coords)[0] * 111320 + 1)

    # 3-3. 아파트 배후 수요 (반경 500m 내 세대수 합산)
    df_apt_clean = df_apt.assign(
        X=pd.to_numeric(df_apt['XCRD'], errors='coerce'),
        Y=pd.to_numeric(df_apt['YCRD'], errors='coerce'),
        HH=pd.to_numeric(df_apt['TNOHSH'], errors='coerce').fillna(0)
    ).dropna(subset=['X', 'Y'])
    
    apt_tree = cKDTree(df_apt_clean[['Y', 'X']].values)
    # query_ball_point: 특정 반경(도 단위) 내의 모든 아파트 색인 탐색
    # 500m / 111320m = 약 0.0045도
    indices = apt_tree.query_ball_point(coords, r=500/111320)
    
    # 각 점포별로 반경 내 아파트 세대수 총합 계산
    df_geo['apt_household_count'] = [df_apt_clean.iloc[idx]['HH'].sum() for idx in indices]

    print("🚀 [Step 4] 실험 #05 모델 학습 시작...")
    # 모든 피처 포함
    features = [
        'open_year', 'store_age', 'local_competitors', 
        'avg_sales', 'saturation', 'sales_per_store',
        'subway_dist_m', 'bus_dist_m', 'large_impact',
        'apt_household_count' # 추가된 배후수요 피처
    ]
    
    model = BaselineXGBoost()
    model.train_and_evaluate(df_geo, 'is_closed', features)

if __name__ == "__main__":
    main()