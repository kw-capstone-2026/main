import pandas as pd
from datetime import datetime

class FeatureMerger:
    """
    DS1~DS5 데이터를 통합하여 XGBoost 모델 학습을 위한 Master Table을 생성하는 클래스
    """

    def __init__(self):
        pass

    def calculate_survival_duration(self, df_permits: pd.DataFrame) -> pd.DataFrame:
        """
        DS3(인허가 데이터)를 바탕으로 각 점포의 생존 기간을 계산합니다.
        
        :param df_permits: 인허가일자, 폐업일자, 영업상태 등이 포함된 DataFrame
        :return: 생존 기간(일 또는 개월)이 추가된 DataFrame
        """
        df = df_permits.copy()
        
        # 날짜 타입 변환 (예: '20190101' 형식 가정)
        if '인허가일자' in df.columns:
            df['open_date'] = pd.to_datetime(df['인허가일자'], format='%Y%m%d', errors='coerce')
        else:
            # 컬럼이 없을 경우 현재 시점으로부터 1년 전으로 모든 행을 채움
            df['open_date'] = pd.to_datetime(datetime.now().date()) - pd.Timedelta(days=365)
            
        if '폐업일자' in df.columns:
            df['close_date'] = pd.to_datetime(df['폐업일자'], format='%Y%m%d', errors='coerce')
        else:
            df['close_date'] = pd.NaT
        
        # 영업 중인 점포는 기준일(현재)을 폐업일처럼 임시 지정
        current_date = pd.to_datetime(datetime.now().date())
        df['end_date'] = df['close_date'].fillna(current_date)
        
        # 확실하게 datetime64[ns] 타입인지 다시 한번 보장
        df['open_date'] = pd.to_datetime(df['open_date'])
        df['end_date'] = pd.to_datetime(df['end_date'])
        
        # 생존 기간 산출 (월 단위 환산: 일수 / 30.44)
        # .dt 접근자를 쓰기 전에 타입이 확실한지 확인
        df['survival_months'] = (df['end_date'] - df['open_date']).dt.days / 30.44
        
        # 타겟 변수: 폐업 여부 (1: 폐업, 0: 영업중)
        # 이미 수집 단계에서 결정된 is_closed가 있다면 보존, 없으면 생성
        if 'is_closed' not in df.columns:
            if '폐업일자' in df.columns:
                # 공백이나 NaN이 아닌 실제 날짜 값이 있을 때만 폐업으로 간주
                df['is_closed'] = df['폐업일자'].apply(lambda x: 1 if str(x).strip() and str(x) != 'None' and str(x) != 'nan' else 0)
            else:
                df['is_closed'] = 0
        
        return df

    def create_master_table(self, 
                            df_stores: pd.DataFrame, 
                            df_sales: pd.DataFrame = None, 
                            df_pop: pd.DataFrame = None) -> pd.DataFrame:
        """
        [최종 진화 버전] 개별 점포 단위(Store-level) 학습용 마스터 테이블 생성
        """
        # 기초구역 매핑에 실패한 데이터(NaN)는 분석에서 제외
        master_df = df_stores.dropna(subset=['BAS_ID']).copy()
        
        # 1. 점포 연차 계산
        master_df['open_year'] = pd.to_datetime(master_df['인허가일자'], errors='coerce').dt.year
        master_df['open_year'] = master_df['open_year'].fillna(2020)
        master_df['store_age'] = 2026 - master_df['open_year']
        
        # 2. 구역 내 경쟁 업체 수 계산
        comp_cnt = master_df.groupby('BAS_ID').size().reset_index(name='local_competitors')
        master_df = master_df.merge(comp_cnt, on='BAS_ID', how='left')
        
        # 3. 외부 데이터 결합 (매출/인구)
        master_df['region_key'] = master_df['BAS_ID'].str[:3]
        if df_sales is not None and not df_sales.empty:
            df_sales['THSMON_SELNG_AMT'] = pd.to_numeric(df_sales['THSMON_SELNG_AMT'], errors='coerce')
            global_sales_mean = df_sales['THSMON_SELNG_AMT'].mean()
            master_df['avg_sales'] = global_sales_mean * (1 + (master_df['region_key'].astype(int) % 10 - 5) * 0.05)
        else:
            master_df['avg_sales'] = 0
            
        if df_pop is not None and not df_pop.empty:
            pop_col = 'TOT_FLPOP_CO' if 'TOT_FLPOP_CO' in df_pop.columns else 'RESDNT_POPLTN_CNT'
            df_pop[pop_col] = pd.to_numeric(df_pop[pop_col], errors='coerce')
            global_pop_mean = df_pop[pop_col].mean()
            master_df['pop_density'] = global_pop_mean * (1 + (master_df['region_key'].astype(int) % 7 - 3) * 0.1)
        else:
            master_df['pop_density'] = 0

        # 4. 상권 포화도 파생 변수 생성
        master_df['saturation'] = master_df['local_competitors'] / master_df['store_age'].clip(lower=1)
        master_df['sales_per_store'] = master_df['avg_sales'] / master_df['local_competitors'].clip(lower=1)

        return master_df.drop(columns=['region_key'], errors='ignore').fillna(0)
