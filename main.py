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
    print("[System] 서울시 폐업 예측 파이프라인 (api.md 통합 버전) 가동...")
    
    # 2. 객체 초기화
    api = PublicDataAPI()
    shp_path = "data/(도로명주소)기초구역_서울/TL_KODIS_BAS_11_202604.shp"
    
    if not os.path.exists(shp_path):
        print(f"[Error] SHP 파일을 찾을 수 없습니다: {shp_path}")
        return

    print(f"[Info] 기준점 데이터 로드 중: {shp_path}")
    sp = SpatialProcessor(bas_shp_path=shp_path)
    fm = FeatureMerger()

    # 3. 데이터 수집 (DS1~DS5)
    print("\n[Step 1] 전수 데이터 수집 시도 (DS1~DS5)...")
    
    # 하이브리드 상가 데이터 수집 (DS1+DS3)
    stores_json = api.get_store_info_hybrid()
    if not stores_json or 'body' not in stores_json:
        print("❌ [Error] 상가 데이터 수집 실패.")
        sys.exit(1)
        
    df_stores_raw = pd.DataFrame(stores_json['body']['items'])
    print(f"[Success] 상가 데이터 {len(df_stores_raw)}건 수집 완료.")

    # 상권 매출/유동인구 데이터 수집 (DS2) - 2024년 1분기 기준
    sales_raw = api.get_seoul_commercial_sales("20241")
    pop_raw = api.get_seoul_commercial_pop("20241")
    living_pop_raw = api.get_seoul_living_pop_grid("20240101")
    
    print(f"[Data] DS2 Sales Records: {len(sales_raw) if sales_raw else 0}")
    print(f"[Data] DS2 Population Records: {len(pop_raw) if pop_raw else 0}")
    print(f"[Data] DS5 Grid Pop Records: {len(living_pop_raw) if living_pop_raw else 0}")

    # 4. 공간 연산 및 BAS_ID 할당
    print("\n[Step 2] 공간 연산 및 기초구역(BAS_ID) 매핑 중...")
    gdf_stores = sp.create_point_geometry(df_stores_raw, lat_col='lat', lng_col='lon')
    gdf_mapped = sp.assign_bas_id(gdf_stores)
    
    mapped_count = gdf_mapped['BAS_ID'].notna().sum()
    print(f"[Success] 공간 매핑 완료: {mapped_count} / {len(gdf_mapped)} 건 매핑 성공")

    # 5. 특징 변수 및 최종 마스터 테이블 생성
    print("\n[Step 3] 특징 변수(Feature) 및 타겟 생성 중...")
    df_with_survival = fm.calculate_survival_duration(gdf_mapped)
    
    # 데이터프레임 변환
    df_sales = pd.DataFrame(sales_raw) if sales_raw else pd.DataFrame()
    df_pop = pd.DataFrame(pop_raw) if pop_raw else pd.DataFrame()
    
    # 모든 외부 데이터를 통합하여 마스터 테이블 생성
    master_table = fm.create_master_table(
        df_stores=df_with_survival,
        df_sales=df_sales,
        df_pop=df_pop
    )
    
    print(f"[Success] 최종 마스터 테이블 생성 완료 (행: {len(master_table)}, 피처 수: {len(master_table.columns)})")
    
    print("\n[Data] Target(Closure) Distribution:")
    print(master_table['is_closed'].value_counts())

    # 6. 모델 학습 및 평가 (점포 단위 이진 분류)
    print("\n[Step 4] XGBoost (Classification) 모델 학습 시작...")
    target = 'is_closed'
    exclude_cols = ['BAS_ID', '상가업소번호', '상호명', '인허가일자', '폐업일자', 'open_date', 'close_date', 'lat', 'lon', 'geometry', target, 'survival_months']
    features = [col for col in master_table.columns if col not in exclude_cols]
    
    if len(master_table) < 10:
        print("[Warning] 데이터가 너무 적어 모델 학습을 중단합니다.")
        return
        
    # main.py의 Step 3 마스터 테이블 생성 직후
    print(f"현재 사용 가능한 데이터 항목들: {master_table.columns.tolist()}")    
    print(f"[Data] 학습에 사용될 핵심 피처 목록: {features}")
    model = BaselineXGBoost(model_type='classification')
    model.train_and_evaluate(master_table, target_col=target, feature_cols=features)
    print("\n[System] 모든 파이프라인 과정이 성공적으로 완료되었습니다!")

if __name__ == "__main__":
    main()
