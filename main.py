import os
import pandas as pd
import sys
from dotenv import load_dotenv
from src.data_acquisition import PublicDataAPI
from src.spatial_processor import SpatialProcessor
from src.feature_merger import FeatureMerger
from src.models.baseline_xgboost import BaselineXGBoost

# 1. .env 파일의 API 키 로드
load_dotenv()

def main():
    print("🚀 [System] 서울시 폐업 예측 파이프라인 가동...")
    
    # 2. 객체 초기화
    api = PublicDataAPI()
    shp_path = "data/(도로명주소)기초구역_서울/TL_KODIS_BAS_11_202604.shp"
    
    if not os.path.exists(shp_path):
        print(f"❌ [Error] SHP 파일을 찾을 수 없습니다: {shp_path}")
        return

    print(f"📦 [Info] 기준점 데이터 로드 중: {shp_path}")
    sp = SpatialProcessor(bas_shp_path=shp_path)
    fm = FeatureMerger()

    # 3. 데이터 수집 (API 활용)
    print("\n[Step 1] API를 통한 데이터 수집 시도...")
    # 하이브리드 수집 (영업중 + 폐업 데이터를 섞어 균형 잡힌 데이터셋 구축)
    stores_json = api.get_store_info_hybrid()
    
    # API 호출 실패 시 즉시 중단
    if not stores_json or 'body' not in stores_json or 'items' not in stores_json['body'] or not stores_json['body']['items']:
        print("❌ [Error] 상가 정보 API 호출에 실패했거나 데이터가 비어 있습니다.")
        print("API 키의 권한이나 네트워크 상태를 확인해 주세요. 파이프라인을 중단합니다.")
        sys.exit(1) # 더미 데이터 없이 종료

    # 실제 데이터 로드
    df_stores_raw = pd.DataFrame(stores_json['body']['items'])
    print(f"✅ 상가 데이터 {len(df_stores_raw)}건 수집 완료.")

    # 4. 공간 연산 및 BAS_ID 할당
    print("\n[Step 2] 공간 연산 및 기초구역(BAS_ID) 매핑 중...")
    gdf_stores = sp.create_point_geometry(df_stores_raw, lat_col='lat', lng_col='lon')
    gdf_mapped = sp.assign_bas_id(gdf_stores)
    
    mapped_count = gdf_mapped['BAS_ID'].notna().sum()
    print(f"✅ 공간 매핑 완료: {mapped_count} / {len(gdf_mapped)} 건 매핑 성공")

    # 5. 생존 기간 및 피처 생성
    print("\n[Step 3] 특징 변수(Feature) 및 타겟 생성 중...")
    gdf_mapped['YEAR_QUARTER'] = '20231'
    df_with_survival = fm.calculate_survival_duration(gdf_mapped)
    
    # 상권/유동인구 데이터 (필요 시 API 추가 호출 로직 구현)
    df_sales_dummy = pd.DataFrame(columns=['BAS_ID', 'YEAR_QUARTER', 'total_sales'])
    df_pop_dummy = pd.DataFrame(columns=['BAS_ID', 'YEAR_QUARTER', 'floating_pop'])
    
    master_table = fm.create_master_table(df_with_survival, df_sales_dummy, df_pop_dummy)
    print(f"✅ 최종 마스터 테이블 생성 완료 (행: {len(master_table)})")

    # 6. 모델 학습 및 평가
    print("\n[Step 4] XGBoost 베이스라인 모델 학습 시작...")
    features = ['competitor_cnt', 'avg_survival_months']
    target = 'closure_rate' 
    
    if len(master_table) < 3:
        print("⚠️ [Warning] 데이터가 너무 적어 모델 학습을 중단합니다.")
        sys.exit(1)
        
    model = BaselineXGBoost(model_type='regression')
    model.train_and_evaluate(master_table, target_col=target, feature_cols=features)
    print("\n🚀 [System] 모든 파이프라인 과정이 완료되었습니다!")

if __name__ == "__main__":
    main()
