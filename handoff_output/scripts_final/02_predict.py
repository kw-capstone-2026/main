"""2~3단계: 학습과 동일한 전처리 후 XGBoost·LightGBM 확률 예측, 앙상블."""
import os
import sys

import lightgbm as lgb
import numpy as np
import pandas as pd
from xgboost import XGBClassifier

sys.path.insert(0, os.path.dirname(__file__))
from common import LGB_PATH, W_LGB, W_XGB, WORK_DIR, XGB_PATH, load_feature_cols, setup_logging  # noqa: E402

setup_logging('02_predict')

feature_cols = load_feature_cols()
df = pd.read_parquet(os.path.join(WORK_DIR, 'test_2024.parquet'))

# 학습(train_and_save_models.py)과 동일: to_numeric(coerce) → fillna(0), feature_cols.json 순서 그대로
X = df[feature_cols].apply(pd.to_numeric, errors='coerce')
print(f'변환 후 결측(→0 대체) 셀 수: {int(X.isna().sum().sum()):,}')
X = X.fillna(0)
assert X.shape == (len(df), 32), X.shape
assert list(X.columns) == feature_cols
print(f'입력 행렬 shape: {X.shape}')

xgb = XGBClassifier()
xgb.load_model(XGB_PATH)
assert list(xgb.get_booster().feature_names) == feature_cols, 'XGBoost 저장 변수 순서 불일치'
prob_xgb = xgb.predict_proba(X)[:, 1]

booster = lgb.Booster(model_file=LGB_PATH)
lgb_names = booster.feature_name()
assert [c.replace(' ', '_') for c in feature_cols] == lgb_names, 'LightGBM 저장 변수 순서 불일치'
prob_lgb = booster.predict(X.to_numpy(dtype=np.float64))  # 이름 대신 순서로 입력

prob_final = W_XGB * prob_xgb + W_LGB * prob_lgb

pred = pd.DataFrame({'prob_xgb': prob_xgb, 'prob_lgb': prob_lgb, 'prob_final': prob_final})
for c in pred:
    s = pred[c]
    print(f'  {c:<11} 평균 {s.mean():.4f}  중앙값 {s.median():.4f}  최소 {s.min():.4f}  최대 {s.max():.4f}  ≥0.5 비율 {(s >= 0.5).mean():.2%}')
X.to_parquet(os.path.join(WORK_DIR, 'X_2024.parquet'), index=False)
pred.to_parquet(os.path.join(WORK_DIR, 'pred_2024.parquet'), index=False)
print(f'[요약] 예측 {len(pred):,}행 완료 (최종 = {W_XGB}×XGB + {W_LGB}×LGB)')
