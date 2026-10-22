"""인수인계 (a): output/master_2024.csv: 2024년 1~4분기 전체, 상권×업종×분기 1행."""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from common import TARGET, WORK_DIR, save_csv, setup_logging  # noqa: E402

setup_logging('06_build_master')

df = pd.read_parquet(os.path.join(WORK_DIR, 'test_2024.parquet'))
pred = pd.read_parquet(os.path.join(WORK_DIR, 'pred_2024.parquet'))
assert len(df) == len(pred)

master = pd.DataFrame({
    'row_id': range(len(df)),  # shap_top5_*.csv의 row_id와 연결
    '기준_년분기_코드': df['기준_년분기_코드'].astype(int),
    '상권_코드': df['상권_코드'],
    '상권명': df['상권_코드_명_x'],
    '상권_구분': df['상권_구분_코드_명_x'],
    '서비스_업종_코드': df['서비스_업종_코드'],
    '업종명': df['서비스_업종_코드_명_x'],
    'lat': df['lat'],
    'lon': df['lon'],
    '과포화_위험_여부': pd.to_numeric(df[TARGET], errors='coerce').fillna(0).astype(int),
    'prob_xgb': pred['prob_xgb'].round(6),
    'prob_lgb': pred['prob_lgb'].round(6),
    'prob_final': pred['prob_final'].round(6),
    'risk_score': pred['risk_score'].astype(int),
    'risk_grade': pred['risk_grade'],  # 확정 기준: 위험 ≥75 / 주의 50~74 / 안전 <50
    # 아래 _y 열과 점유율·운영개월은 상권 단위 값 (같은 상권의 모든 업종이 같은 값)
    '폐업_률_y': df['폐업_률_y'],
    '개업_율_y': df['개업_율_y'],
    '점포_수_y': df['점포_수_y'],
    '상권_내부_업종_점유율': df['상권 내부 업종 점유율(%)'],
    '운영_영업_개월_평균': df['운영_영업_개월_평균'],
    # 상권×업종 단위 실제 값 (참고용 추가 열)
    '점포_수_x': df['점포_수_x'],
    '폐업_률_x': df['폐업_률_x'],
    '개업_율_x': df['개업_율_x'],
})
save_csv(master, 'master_2024.csv')
print('분기별 행 수:', master['기준_년분기_코드'].value_counts().sort_index().to_dict())
print('결측 있는 열:', {c: int(v) for c, v in master.isna().sum().items() if v} or '없음')
print(f'[요약] master_2024.csv {len(master):,}행 × {master.shape[1]}열')
