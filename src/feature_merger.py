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
        if '폐업일자' in df.columns:
            df['is_closed'] = df['폐업일자'].notna().astype(int)
        else:
            df['is_closed'] = 0
        
        return df

    def create_master_table(self, 
                            df_stores: pd.DataFrame, 
                            df_sales: pd.DataFrame, 
                            df_pop: pd.DataFrame) -> pd.DataFrame:
        """
        통합 마스터 테이블 생성
        """
        # 컬럼명 매핑 (영문 -> 한글 또는 표준화)
        if 'bizesId' in df_stores.columns and '상가업소번호' not in df_stores.columns:
            df_stores = df_stores.rename(columns={'bizesId': '상가업소번호'})
            
        # 필수 컬럼(YEAR_QUARTER) 확인
        if 'YEAR_QUARTER' not in df_stores.columns:
            df_stores['YEAR_QUARTER'] = '2024Q1' # 기본값
            
        # 1. 기초구역별 집계 (상가 수, 평균 생존기간, 폐업률)
        master_df = df_stores.groupby(['BAS_ID', 'YEAR_QUARTER']).agg(
            competitor_cnt=('상가업소번호', 'count'),
            avg_survival_months=('survival_months', 'mean'),
            closure_rate=('is_closed', 'mean')
        ).reset_index()
        
        # 2. 상권 매출 정보 병합
        master_df = master_df.merge(df_sales, on=['BAS_ID', 'YEAR_QUARTER'], how='left')
        
        # 3. 유동인구 정보 병합
        master_df = master_df.merge(df_pop, on=['BAS_ID', 'YEAR_QUARTER'], how='left')
        
        # 추가 결측치 처리 로직 필요 시 적용
        # master_df = master_df.fillna(0)
        
        return master_df
