"""scripts_final 공용 설정: 경로, 상수, 로그(화면 + output/run_log.txt 동시 기록)."""
import io
import json
import os
import sys
from datetime import datetime

# ── 경로 (프로젝트 루트 기준) ─────────────────────────────
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_PATH = os.path.join(ROOT, 'data', 'parquet_datas', 'final_merged_commercial_data_v5.parquet')
XGB_PATH = os.path.join(ROOT, 'ml-server', 'xgb_model.json')
LGB_PATH = os.path.join(ROOT, 'ml-server', 'lgb_model.txt')
FEATURES_PATH = os.path.join(ROOT, 'ml-server', 'feature_cols.json')
OUT_DIR = os.path.join(ROOT, 'output')
WORK_DIR = os.path.join(OUT_DIR, '_intermediate')  # 스크립트 간 중간 파일 (인수인계 대상 아님)
LOG_PATH = os.path.join(OUT_DIR, 'run_log.txt')

# ── 상수 ────────────────────────────────────────────────
SEED = 42
TEST_START = 20241          # 2024년 1분기부터 시험 구간
DEMO_QUARTER = 20244        # 시연·DB 적재 대상 분기
W_XGB, W_LGB = 0.3, 0.7     # 앙상블 가중치 (팀 코드 기준)
TARGET = '과포화_위험_여부'

# 위험등급 기준 (2026-10-20 확정, 근거: output/risk_grade_calibration.md)
# 2024 Q1~Q3에서 정하고 Q4로 검증: 50점부터 실제 위험률이 평균을 넘고(=모델 판정 경계 p≈0.5),
# 75점부터 평균의 5배 이상으로 뛰어오름
GRADE_DANGER = 75   # 이 점수 이상 → 위험
GRADE_CAUTION = 50  # 이 점수 이상 ~ GRADE_DANGER 미만 → 주의, 미만 → 안전

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(WORK_DIR, exist_ok=True)


class _Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, s):
        for st in self.streams:
            st.write(s)
            st.flush()

    def flush(self):
        for st in self.streams:
            st.flush()


def setup_logging(script_name):
    """stdout/stderr를 utf-8로 바꾸고 run_log.txt에 이어 쓴다."""
    out = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
    err = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True)
    log = open(LOG_PATH, 'a', encoding='utf-8')
    sys.stdout = _Tee(out, log)
    sys.stderr = _Tee(err, log)
    print('\n' + '=' * 70)
    print(f'[{script_name}] 시작 {datetime.now():%Y-%m-%d %H:%M:%S}')
    print('=' * 70)


def load_feature_cols():
    with open(FEATURES_PATH, encoding='utf-8') as f:
        return json.load(f)


def save_csv(df, name, **kw):
    path = os.path.join(OUT_DIR, name)
    df.to_csv(path, index=False, encoding='utf-8-sig', **kw)
    print(f'[저장] output/{name} ({len(df):,}행)')
    return path
