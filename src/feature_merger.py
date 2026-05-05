import pandas as pd
from datetime import datetime
import numpy as np

class FeatureMerger:
    def calculate_survival_duration(self, df_permits: pd.DataFrame) -> pd.DataFrame:
        df = df_permits.copy()
        df['open_date'] = pd.to_datetime(df['인허가일자'], format='%Y%m%d', errors='coerce')
        df['close_date'] = pd.to_datetime(df['폐업일자'], format='%Y%m%d', errors='coerce')
        current_date = pd.to_datetime(datetime.now().date())
        df['end_date'] = df['close_date'].fillna(current_date)
        df['survival_months'] = (df['end_date'] - df['open_date']).dt.days / 30.44
        if 'is_closed' not in df.columns:
            df['is_closed'] = df['폐업일자'].apply(lambda x: 1 if str(x).strip() and str(x) not in ['None', 'nan', 'NaT'] else 0)
        return df

    def create_master_table(self, df_stores, df_sales=None, df_pop=None):
        # 1. BAS_ID가 없거나 공백(' ')인 행을 사전에 완벽히 제거
        master_df = df_stores.copy()
        master_df['BAS_ID'] = master_df['BAS_ID'].astype(str).str.strip() # 공백 제거
        master_df = master_df[master_df['BAS_ID'] != ''] # 빈 문자열 제거
        master_df = master_df[master_df['BAS_ID'] != 'nan'] # 문자열 nan 제거
        master_df = master_df.dropna(subset=['BAS_ID']).copy()
        
        # 2. 점포 기본 연차
        master_df['open_year'] = pd.to_datetime(master_df['인허가일자'], errors='coerce').dt.year.fillna(2020)
        master_df['store_age'] = 2026 - master_df['open_year']
        
        # 3. 경쟁 강도
        comp_cnt = master_df.groupby('BAS_ID').size().reset_index(name='local_competitors')
        master_df = master_df.merge(comp_cnt, on='BAS_ID', how='left')
        
        # 4. [수정 지점] 지역 가중치 로직 - 에러 방지 처리
        # 앞 3자리를 가져오되, 숫자로 바꿀 수 없는 데이터는 0으로 치환 후 계산
        master_df['region_key'] = master_df['BAS_ID'].str[:3]
        master_df['region_key_int'] = pd.to_numeric(master_df['region_key'], errors='coerce').fillna(0).astype(int)
        
        if df_sales is not None:
            df_s = pd.DataFrame(df_sales)
            df_s['THSMON_SELNG_AMT'] = pd.to_numeric(df_s['THSMON_SELNG_AMT'], errors='coerce')
            g_sales_mean = df_s['THSMON_SELNG_AMT'].mean()
            
            # region_key_int를 사용하여 민재님 원본 가중치 공식 수행
            master_df['avg_sales'] = g_sales_mean * (1 + (master_df['region_key_int'] % 10 - 5) * 0.05)
        
        # 5. 상권 포화도 및 점포당 매출액
        master_df['saturation'] = master_df['local_competitors'] / master_df['store_age'].clip(lower=1)
        master_df['sales_per_store'] = master_df.get('avg_sales', 0) / master_df['local_competitors'].clip(lower=1)
        
        # 좌표 데이터 유지
        master_df['lat'] = pd.to_numeric(master_df['lat'], errors='coerce')
        master_df['lon'] = pd.to_numeric(master_df['lon'], errors='coerce')
        
        # 계산용 임시 컬럼 삭제
        if 'region_key_int' in master_df.columns:
            master_df = master_df.drop(columns=['region_key_int'])
            
        return master_df.fillna(0)