"""4단계: 2024년 성능 검증. 팀 리포트 기대값과 비교하고, 벗어나면 원인 후보를 점검한 뒤 종료코드 1로 멈춘다."""
import json
import os
import sys

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import (accuracy_score, average_precision_score, confusion_matrix, f1_score,
                             precision_score, recall_score, roc_auc_score)
from xgboost import XGBClassifier

sys.path.insert(0, os.path.dirname(__file__))
from common import (LGB_PATH, OUT_DIR, TARGET, W_LGB, W_XGB, WORK_DIR, XGB_PATH,  # noqa: E402
                    load_feature_cols, setup_logging)

setup_logging('03_validate')

THRESHOLD = 0.5
# (기대값, 허용오차): 팀 리포트 기준
EXPECTED = {
    'roc_auc': (0.909, 0.005), 'pr_auc': (0.317, 0.005), 'precision': (0.137, 0.01),
    'recall': (0.842, 0.01), 'f1': (0.236, 0.01), 'accuracy': (0.831, 0.01),
}
EXPECTED_SINGLE = {'xgb': 0.9076, 'lgb': 0.9089}

df = pd.read_parquet(os.path.join(WORK_DIR, 'test_2024.parquet'))
pred = pd.read_parquet(os.path.join(WORK_DIR, 'pred_2024.parquet'))
y = pd.to_numeric(df[TARGET], errors='coerce').fillna(0).astype(int).to_numpy()


def metrics(p):
    yhat = (p >= THRESHOLD).astype(int)
    return {
        'roc_auc': roc_auc_score(y, p), 'pr_auc': average_precision_score(y, p),
        'precision': precision_score(y, yhat, zero_division=0), 'recall': recall_score(y, yhat),
        'f1': f1_score(y, yhat), 'accuracy': accuracy_score(y, yhat),
    }


res = {name: metrics(pred[col].to_numpy()) for name, col in
       [('ensemble', 'prob_final'), ('xgb', 'prob_xgb'), ('lgb', 'prob_lgb')]}
tn, fp, fn, tp = confusion_matrix(y, (pred['prob_final'] >= THRESHOLD).astype(int)).ravel()

LABELS = {'roc_auc': 'ROC-AUC', 'pr_auc': 'PR-AUC', 'precision': '정밀도 (위험 클래스)',
          'recall': '재현율 (위험 클래스)', 'f1': 'F1 (위험 클래스)', 'accuracy': '정확도'}
rows, ok_all = [], True
print(f'\n{"지표":<18}{"계산값":>10}{"기대값":>10}{"차이":>10}{"허용":>8}  판정')
for k, (exp, tol) in EXPECTED.items():
    v = res['ensemble'][k]
    ok = abs(v - exp) <= tol
    ok_all &= ok
    rows.append((LABELS[k], v, exp, v - exp, tol, ok))
    print(f'{LABELS[k]:<18}{v:>10.4f}{exp:>10.3f}{v - exp:>+10.4f}{tol:>8.3f}  {"OK" if ok else "벗어남"}')
print(f'\n단독 ROC-AUC: XGBoost {res["xgb"]["roc_auc"]:.4f} (리포트 {EXPECTED_SINGLE["xgb"]}), '
      f'LightGBM {res["lgb"]["roc_auc"]:.4f} (리포트 {EXPECTED_SINGLE["lgb"]})')
print(f'혼동행렬 (임계값 {THRESHOLD}): TN={tn:,} FP={fp:,} FN={fn:,} TP={tp:,}')

# ── 저장 ──
n = len(y)
out = {
    'test_period': '2024Q1~Q4 (기준_년분기_코드 20241~20244)', 'n_rows': int(n), 'n_positive': int(y.sum()),
    'threshold': THRESHOLD, 'ensemble_weights': {'xgb': W_XGB, 'lgb': W_LGB},
    'ensemble': {k: round(float(v), 4) for k, v in res['ensemble'].items()},
    'xgb_only': {k: round(float(v), 4) for k, v in res['xgb'].items()},
    'lgb_only': {k: round(float(v), 4) for k, v in res['lgb'].items()},
    'confusion_matrix': {'TN': int(tn), 'FP': int(fp), 'FN': int(fn), 'TP': int(tp)},
    'expected_from_team_report': {k: v[0] for k, v in EXPECTED.items()},
    'within_tolerance': bool(ok_all),
}
with open(os.path.join(OUT_DIR, 'model_metrics.json'), 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

md = [
    '# 모델 성능 (2024년 시험 구간)', '',
    f'- 학습: 2019~2023년 / 시험: 2024년 1~4분기 (모델이 처음 보는 데이터)',
    f'- 시험 데이터: {n:,}개 (상권×업종×분기), 이 중 실제 과포화 위험 {int(y.sum()):,}개 ({y.mean():.1%})',
    f'- 최종 모델: XGBoost × {W_XGB} + LightGBM × {W_LGB} 앙상블, 위험 판정 기준 확률 {THRESHOLD}', '',
    '## 앙상블 성능', '',
    '| 지표 | 값 | 팀 리포트 | 차이 |', '|---|---:|---:|---:|',
    *[f'| {r[0]} | {r[1]:.3f} | {r[2]:.3f} | {r[3]:+.4f} |' for r in rows], '',
    '## 모델별 비교', '',
    '| 모델 | ROC-AUC | PR-AUC | 정밀도 | 재현율 | F1 | 정확도 |', '|---|---:|---:|---:|---:|---:|---:|',
    *[f'| {lab} | ' + ' | '.join(f'{res[k][m]:.3f}' for m in EXPECTED) + ' |'
      for k, lab in [('xgb', 'XGBoost'), ('lgb', 'LightGBM'), ('ensemble', '앙상블 (0.3/0.7)')]], '',
    f'## 혼동행렬 (앙상블, 확률 ≥ {THRESHOLD} → 위험)', '',
    '| | 예측: 안전 | 예측: 위험 |', '|---|---:|---:|',
    f'| **실제: 안전** | {tn:,} | {fp:,} |', f'| **실제: 위험** | {fn:,} | {tp:,} |', '',
    f'- 실제 위험 {int(y.sum()):,}개 중 {tp:,}개({tp / (tp + fn):.1%})를 찾아냄 (재현율)',
    f'- 위험으로 예측한 {tp + fp:,}개 중 실제 위험은 {tp:,}개({tp / (tp + fp):.1%}) (정밀도). '
    '위험 클래스가 약 3%로 드물어 정밀도는 낮게 나옴',
]
with open(os.path.join(OUT_DIR, 'model_metrics.md'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(md) + '\n')
print('[저장] output/model_metrics.md, output/model_metrics.json')

if ok_all:
    print('[요약] 검증 통과: 모든 지표가 허용 오차 이내')
    sys.exit(0)

# ── 기준 벗어남: 원인 후보 점검 ──
print('\n[검증 실패] 원인 후보 점검 결과')
feature_cols = load_feature_cols()
X = pd.read_parquet(os.path.join(WORK_DIR, 'X_2024.parquet'))
xgb = XGBClassifier()
xgb.load_model(XGB_PATH)
booster = lgb.Booster(model_file=LGB_PATH)
print(' 1) 변수 순서: XGB 저장 순서 일치 =', list(xgb.get_booster().feature_names) == feature_cols,
      '/ LGB 저장 순서 일치 =', booster.feature_name() == [c.replace(' ', '_') for c in feature_cols])
raw = df[feature_cols].apply(pd.to_numeric, errors='coerce')
print(' 2) 결측 처리: 결측 셀', int(raw.isna().sum().sum()), '개 → 0 대체. 결측을 NaN으로 둘 때 앙상블 ROC-AUC =',
      round(roc_auc_score(y, W_XGB * xgb.predict_proba(raw)[:, 1]
                          + W_LGB * booster.predict(raw.to_numpy(dtype=np.float64))), 4))
print(' 3) 필터: 분기 =', sorted(df['기준_년분기_코드'].unique().tolist()), f'행 {n:,}, 양성 {int(y.sum()):,}')
print(' 4) 모델 로딩: XGB 트리 수', xgb.get_booster().num_boosted_rounds(), '/ LGB 트리 수', booster.num_trees(),
      '/ LGB를 이름 입력(DataFrame)으로 예측 시 차이 최대값',
      float(np.abs(booster.predict(X.set_axis(booster.feature_name(), axis=1)) - pred['prob_lgb']).max()))
print(' 분기별 앙상블 ROC-AUC:', {int(q): round(roc_auc_score(y[m], pred['prob_final'][m]), 4)
                            for q in sorted(df['기준_년분기_코드'].unique())
                            for m in [(df['기준_년분기_코드'] == q).to_numpy()]})
sys.exit('[중단] 4단계 검증 기준을 벗어남. 5단계로 진행하지 않음')
