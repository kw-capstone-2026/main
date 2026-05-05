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
    
    print("🚀 [실험 4-2] 베이스라인 + 대형마트 단독 실험 시작...")
    
    # 1. 데이터 수집 (마트 분석에 필요한 데이터만 로드)
    df_raw = pd.DataFrame(api.get_store_info_hybrid()['body']['items'])
    df_sales = api.get_seoul_commercial_sales("20234")
    df_large = api.get_seoul_large_stores() 

    # 2. 베이스라인 피처 생성 (D1~D5)
    df_prep = merger.calculate_survival_duration(df_raw)
    df_master = merger.create_master_table(df_prep, df_sales=df_sales)

    # 3. 공간 연산 (대형마트 영향도 지수 계산)
    df_geo = df_master.dropna(subset=['lat', 'lon']).copy()
    coords = df_geo[['lat', 'lon']].values
    
    # 대형마트 좌표 정제 (X, Y 좌표를 숫자로 변환)
    df_large_clean = df_large.assign(
        X=pd.to_numeric(df_large['X'], errors='coerce'),
        Y=pd.to_numeric(df_large['Y'], errors='coerce')
    ).dropna(subset=['X', 'Y'])
    
    # KD-Tree 생성 (Y=lat, X=lon)
    large_tree = cKDTree(df_large_clean[['Y', 'X']].values)
    
    # 최단 거리 계산 후 영향도(Impact) 지수로 변환
    # 1 / (거리 + 1) 공식을 사용하여 거리가 가까울수록 값이 커지게 설정 (0~1 사이)
    dist, _ = large_tree.query(coords)
    df_geo['large_impact'] = 1 / (dist * 111320 + 1)

    print("🚀 [Step 4] 모델 학습 (대형마트 변수 기여도 측정)...")
    
    # 실험 4-2 핵심: 'large_impact' 외에 지하철, 버스, 아파트는 모두 제외
    features = [
        'open_year', 'store_age', 'local_competitors', 
        'avg_sales', 'saturation', 'sales_per_store',
        'large_impact' 
    ]
    
    model = BaselineXGBoost()
    model.train_and_evaluate(df_geo, 'is_closed', features)

if __name__ == "__main__":
    main()