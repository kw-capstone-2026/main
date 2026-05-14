import pandas as pd
import numpy as np
import os
from datetime import datetime

class FeatureMerger:
    """
    DS1~DS5 데이터를 통합하여 XGBoost 모델 학습을 위한 Master Table을 생성하는 클래스.
    10년 단위 메인 모델링을 위한 정제 및 병합 로직을 포함합니다.
    """

    def __init__(self, data_dir: str = 'data/parquet_datas'):
        self.data_dir = data_dir

    def load_and_preprocess_df_final(self, file_name: str = 'df_final.parquet') -> pd.DataFrame:
        """
        팀원 DS1이 제공한 대용량 점포 데이터를 로드하고 모델링에 맞게 정제합니다.
        """
        path = os.path.join(self.data_dir, file_name)
        if not os.path.exists(path):
            print(f"Warning: {path} 를 찾을 수 없습니다.")
            return pd.DataFrame()

        # 모델 학습에 필수적인 수치형 컬럼만 선택 로드
        cols_to_keep = [
            '기준_년분기_코드', '상권_코드', '점포_수', '유사_업종_점포_수',
            '프랜차이즈_점포_수', '프랜차이즈점포비율(%)', '개인점포비율(%)', 
            '상권_전체점포_수', '상권 내부 업종 점유율(%)', '개업_율', '폐업_률', 
            '운영_영업_개월_평균', '폐업_영업_개월_평균'
        ]
        
        # Parquet 스키마 확인 후 존재하는 컬럼만 로드
        import pyarrow.parquet as pq
        pq_schema = pq.ParquetFile(path).schema.names
        actual_cols = [c for c in cols_to_keep if c in pq_schema]
        
        df = pd.read_parquet(path, columns=actual_cols)
        
        # 데이터 타입 정규화
        df['기준_년분기_코드'] = df['기준_년분기_코드'].astype('int64')
        df['상권_코드'] = df['상권_코드'].astype('int64')
        
        # 문자열로 된 수치 컬럼들 숫자형 변환
        numeric_cols = ['개업_율', '폐업_률', '운영_영업_개월_평균', '폐업_영업_개월_평균']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # 동일 상권/분기 중복 데이터 평균 집계
        df = df.groupby(['기준_년분기_코드', '상권_코드']).mean().reset_index()
        return df

    def create_integrated_dataset(self, base_file: str = 'processed_commercial_data.parquet', output_file: str = 'final_merged_commercial_data.parquet'):
        """
        베이스라인 데이터와 팀원 데이터를 병합하여 최종 분석용 파일을 생성합니다.
        """
        base_path = os.path.join(self.data_dir, base_file)
        if not os.path.exists(base_path):
            print(f"Error: 베이스라인 파일 {base_path} 가 없습니다.")
            return

        print("1. 베이스라인 데이터 로딩...")
        df_base = pd.read_parquet(base_path)
        df_base['기준_년분기_코드'] = df_base['기준_년분기_코드'].astype('int64')
        df_base['상권_코드'] = df_base['상권_코드'].astype('int64')

        print("2. 팀원 점포 데이터(df_final) 정제 및 병합...")
        df_store = self.load_and_preprocess_df_final()
        
        if not df_store.empty:
            df_final = pd.merge(df_base, df_store, on=['기준_년분기_코드', '상권_코드'], how='left')
            
            output_path = os.path.join(self.data_dir, output_file)
            df_final.to_parquet(output_path, index=False)
            print(f"3. 통합 완료! 저장 경로: {output_path}")
            print(f"   최종 규모: {df_final.shape}")
        else:
            print("병합할 추가 데이터가 없습니다.")

if __name__ == "__main__":
    merger = FeatureMerger()
    merger.create_integrated_dataset()
