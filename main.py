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
    
    print("🚀 [실험 3-2] 데이터 수집 (베이스라인 + 버스 단독)...")
    df_raw = pd.DataFrame(api.get_store_info_hybrid()['body']['items'])
    df_sales = api.get_seoul_commercial_sales("20234")
    df_bus = api.get_seoul_bus_stops() # 버스 데이터만 집중

    print("🚀 [Step 2] 베이스라인 피처 생성 (D1~D5)...")
    df_prep = merger.calculate_survival_duration(df_raw)
    df_master = merger.create_master_table(df_prep, df_sales=df_sales)

    # 좌표가 있는 데이터만 필터링
    df_geo = df_master.dropna(subset=['lat', 'lon']).copy()
    coords = df_geo[['lat', 'lon']].values

    print("🚀 [Step 3] 공간 연산 (버스 정류장 최단거리)...")
    # 버스 정류장 KD-Tree 생성 및 거리 계산
    bus_tree = cKDTree(df_bus[['YCRD', 'XCRD']].apply(pd.to_numeric, errors='coerce').dropna().values)
    df_geo['bus_dist_m'] = bus_tree.query(coords)[0] * 111320

    print("🚀 [Step 4] 모델 학습 및 평가 (버스 기여도 확인)...")
    # 지하철, 마트, 아파트를 제외한 버스 전용 피처 리스트
    features = [
        'open_year', 'store_age', 'local_competitors', 
        'avg_sales', 'saturation', 'sales_per_store',
        'bus_dist_m' # 이번 실험의 핵심 변수
    ]
    
    model = BaselineXGBoost()
    model.train_and_evaluate(df_geo, 'is_closed', features)

if __name__ == "__main__":
    main()