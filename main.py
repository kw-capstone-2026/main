import os
import pandas as pd
import sys
from dotenv import load_dotenv
from src.data_acquisition import PublicDataAPI
from src.spatial_processor import SpatialProcessor
from src.feature_merger import FeatureMerger
from src.models.baseline_xgboost import BaselineXGBoost
from src.data_acquisition import PublicDataAPI, fetch_macro_data
from src.feature_merger import FeatureMerger, merge_macro_features

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
    
    # === [Suin] 데이터 연도 범위 확인 + 마스터 테이블 캐싱 ===
    print("\n[Inspect] 데이터 연도 범위 분석...")
    if 'open_year' in master_table.columns:
        valid_years = master_table[master_table['open_year'] > 0]['open_year']
        print(f"  - open_year 범위: {int(valid_years.min())} ~ {int(valid_years.max())}")
        print(f"  - 연도별 점포 수 분포:")
        print(master_table['open_year'].value_counts().sort_index())
    
    # 마스터 테이블 CSV 저장 (재사용을 위해)
    cache_path = 'master_table.csv'
    master_table.to_csv(cache_path, index=False, encoding='utf-8-sig')
    print(f"[Saved] 마스터 테이블 저장 완료: {cache_path}")
    # === [Suin] 추가 코드 끝 ===

    print(master_table['is_closed'].value_counts())

    # 거시 경제 데이터 로드 및 병합 
    # =====================================================================
    print("\n[Step 3.5] 거시 경제 데이터(부동산/금리/CPI/최저임금) 통합 중...")
    macro_dict = fetch_macro_data()
    master_table = merge_macro_features(master_table, macro_dict)
    print(f"[Success] 거시 피처 병합 완료! 현재 마스터 테이블 컬럼 수: {len(master_table.columns)}")
    # =====================================================================

    # 6. 모델 학습 및 평가 (점포 단위 이진 분류)
    print("\n[Step 4] XGBoost (Classification) 모델 학습 시작...")
    target = 'is_closed'
    exclude_cols = ['BAS_ID', '상가업소번호', '상호명', '인허가일자', '폐업일자', 'open_date', 'close_date', 'lat', 'lon', 'geometry', target, 'survival_months']
    features = [col for col in master_table.columns if col not in exclude_cols]
    
    if len(master_table) < 10:
        print("[Warning] 데이터가 너무 적어 모델 학습을 중단합니다.")
        return
        
    print(f"[Data] 학습에 사용될 핵심 피처 목록: {features}")
    model = BaselineXGBoost(model_type='classification')
    model.train_and_evaluate(master_table, target_col=target, feature_cols=features)
    # 피처 중요도 수치 출력 로직
    # =====================================================================
    print("\n[Analysis] 피처 중요도 (상위 10개):")
    
    # 모델 안에 저장된 feature importances 가져오기
    if hasattr(model, 'model') and hasattr(model.model, 'feature_importances_'):
        importances = model.model.feature_importances_
        feature_names = features
        
        # 데이터프레임으로 만들어서 보기 좋게 내림차순 정렬
        imp_df = pd.DataFrame({'Feature': feature_names, 'Importance': importances})
        imp_df = imp_df.sort_values(by='Importance', ascending=False)
        
        # 1. 전체 상위 10개 출력
        print(imp_df.head(10).to_string(index=False))
        
        # 2. 내가 추가한 '거시경제 지표'들만 쏙 뽑아서 확인하기
        print("\n[Analysis] 🔍 거시경제 지표 기여도 특별 확인:")
        macro_cols = ['real_estate_index', 'interest_rate', 'cpi', 'min_wage_hourly']
        macro_result = imp_df[imp_df['Feature'].isin(macro_cols)]
        
        if not macro_result.empty:
            print(macro_result.to_string(index=False))
        else:
            print("거시경제 지표가 모델 학습에 사용되지 않았습니다. 컬럼명을 확인해주세요.")
    else:
        print("피처 중요도를 추출할 수 없습니다. (모델 객체 구조 확인 필요)")
    # =====================================================================
    print("\n[System] 모든 파이프라인 과정이 성공적으로 완료되었습니다!")

if __name__ == "__main__":
    main()
