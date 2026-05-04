import os
import pandas as pd
import sys
import numpy as np
from scipy.spatial import cKDTree
from dotenv import load_dotenv
from src.data_acquisition import PublicDataAPI
from src.spatial_processor import SpatialProcessor
from src.feature_merger import FeatureMerger
from src.models.baseline_xgboost import BaselineXGBoost

load_dotenv()

def main():
    print("[System] 서울시 폐업 예측 지리 정보 강화 파이프라인 가동...")
    
    api = PublicDataAPI()
    shp_path = "data/(도로명주소)기초구역_서울/TL_KODIS_BAS_11_202604.shp"
    
    if not os.path.exists(shp_path):
        print(f"❌ [Error] SHP 파일을 찾을 수 없습니다: {shp_path}")
        return

    sp = SpatialProcessor(bas_shp_path=shp_path)
    fm = FeatureMerger()

    # Step 1: 데이터 수집
    print("\n[Step 1] 데이터 수집 시도...")
    stores_json = api.get_store_info_hybrid()
    if not stores_json: sys.exit(1)
    df_stores_raw = pd.DataFrame(stores_json['body']['items'])
    
    subway_raw = api.get_seoul_subway_master()
    df_subway = pd.DataFrame(subway_raw)

    # Step 2: 지리 변수 생성 및 결측치 처리
    if not df_subway.empty:
        print("\n[Step 2] 점포별 최단 지하철 거리(m) 계산 중...")
        df_stores_raw['lat'] = pd.to_numeric(df_stores_raw['lat'], errors='coerce')
        df_stores_raw['lon'] = pd.to_numeric(df_stores_raw['lon'], errors='coerce')
        df_stores_raw = df_stores_raw.dropna(subset=['lat', 'lon'])
        
        df_subway['LAT'] = pd.to_numeric(df_subway['LAT'], errors='coerce')
        df_subway['LOT'] = pd.to_numeric(df_subway['LOT'], errors='coerce')
        df_subway = df_subway.dropna(subset=['LAT', 'LOT'])
        
        subway_coords = df_subway[['LAT', 'LOT']].values
        store_coords = df_stores_raw[['lat', 'lon']].values
        
        if len(store_coords) > 0:
            tree = cKDTree(subway_coords)
            dists, _ = tree.query(store_coords)
            df_stores_raw['subway_dist_m'] = dists * 110000 
            df_stores_raw['geo_access_score'] = 1 / (df_stores_raw['subway_dist_m'] + 1)

    # BAS_ID 할당
    gdf_stores = sp.create_point_geometry(df_stores_raw, lat_col='lat', lng_col='lon')
    gdf_mapped = sp.assign_bas_id(gdf_stores)

    # Step 3: 마스터 테이블 생성
    print("\n[Step 3] 최종 마스터 테이블 생성 중...")
    df_with_survival = fm.calculate_survival_duration(gdf_mapped)
    master_table = fm.create_master_table(
        df_stores=df_with_survival,
        df_sales=pd.DataFrame(api.get_seoul_commercial_sales("20241")),
        df_pop=pd.DataFrame(api.get_seoul_commercial_pop("20241"))
    )

    # Step 4: 모델 학습 및 중요도 출력
    print("\n[Step 4] XGBoost 모델 학습 및 변수 중요도 분석...")
    target = 'is_closed'
    exclude_cols = ['BAS_ID', '상가업소번호', '상호명', '인허가일자', '폐업일자', 
                    'open_date', 'close_date', 'lat', 'lon', 'geometry', target, 'survival_months', 'index_right']
    features = [col for col in master_table.columns if col not in exclude_cols]
    
    model = BaselineXGBoost(model_type='classification')
    model.train_and_evaluate(master_table, target_col=target, feature_cols=features)

    # --- 변수 중요도 출력 추가 ---
    print("\n" + "="*50)
    print("🚀 [실험 결과] 변수 중요도 (Feature Importance) TOP 10")
    print("="*50)
    importances = model.model.feature_importances_
    feat_imp = pd.DataFrame({'Feature': features, 'Importance': importances})
    feat_imp = feat_imp.sort_values(by='Importance', ascending=False)
    print(feat_imp.head(10).to_string(index=False))
    print("="*50)

if __name__ == "__main__":
    main()