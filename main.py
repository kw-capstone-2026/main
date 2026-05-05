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
    
    print("🚀 [Step 1] 전수 데이터 수집 중...")
    # 1. 데이터 수집
    raw_data = api.get_store_info_hybrid()
    df_raw = pd.DataFrame(raw_data['body']['items'])
    df_sales = api.get_seoul_commercial_sales("20234")
    df_sub = api.get_seoul_subway()
    df_bus = api.get_seoul_bus_stops()
    df_large = api.get_seoul_large_stores()

    print("🚀 [Step 2] 피처 생성 및 병합 중...")
    df_prep = merger.calculate_survival_duration(df_raw)
    df_master = merger.create_master_table(df_prep, df_sales=df_sales)

    # 지리 연산을 위한 좌표 필터링
    df_geo = df_master.dropna(subset=['lat', 'lon']).copy()
    coords = df_geo[['lat', 'lon']].values

    print("🚀 [Step 3] 공간 거리 연산 수행 중 (KD-Tree)...")
    # 3-1. 지하철 거리
    sub_tree = cKDTree(df_sub[['LAT', 'LOT']].apply(pd.to_numeric, errors='coerce').dropna().values)
    d_sub, _ = sub_tree.query(coords)
    df_geo['subway_dist_m'] = d_sub * 111320

    # 3-2. 버스 거리
    bus_tree = cKDTree(df_bus[['YCRD', 'XCRD']].apply(pd.to_numeric, errors='coerce').dropna().values)
    d_bus, _ = bus_tree.query(coords)
    df_geo['bus_dist_m'] = d_bus * 111320

    # 3-3. 대규모 점포 거리 및 영향도 (에러 발생 지점 수정)
    # X, Y 컬럼을 숫자로 변환하되, 공백 같은 쓰레기 값은 NaN으로 만듭니다.
    df_large['X'] = pd.to_numeric(df_large['X'], errors='coerce')
    df_large['Y'] = pd.to_numeric(df_large['Y'], errors='coerce')
    
    # 좌표가 제대로 변환된 데이터만 남깁니다.
    df_large_clean = df_large.dropna(subset=['X', 'Y']).copy()
    
    large_tree = cKDTree(df_large_clean[['Y', 'X']].values) # 이미 숫자이므로 apply 필요 없음
    d_large, _ = large_tree.query(coords)
    df_geo['large_store_dist_m'] = d_large * 111320
    df_geo['large_impact'] = 1 / (df_geo['large_store_dist_m'] + 1)

    print("🚀 [Step 4] 모델 학습 및 평가...")
    features = [
        'open_year', 'store_age', 'survival_months', 'local_competitors', 
        'avg_sales', 'saturation', 'sales_per_store',
        'subway_dist_m', 'bus_dist_m', 'large_impact'
    ]
    
    model = BaselineXGBoost()
    model.train_and_evaluate(df_geo, 'is_closed', features)

if __name__ == "__main__":
    main()