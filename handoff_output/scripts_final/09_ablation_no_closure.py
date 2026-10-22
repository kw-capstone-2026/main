"""추가 실험: 폐업에서 직접 나온 변수를 빼고 모델 A를 같은 설정으로 다시 학습해 성능 비교.
시연·DB용 결과(ml-server 모델, master_2024.csv 등)는 바꾸지 않음. 결과는 output/ablation_no_closure.md, .json

- 기준 재학습: 32개 변수 그대로 (재학습 방식이 원래 성능을 재현하는지 확인용)
- 폐업 변수 제외: 아래 CLOSURE_COLS 3개를 뺀 29개 변수
- 학습 설정은 src/models/train_and_save_models.py와 같음 (2019~2023 학습, 2024 시험, XGB 0.3 + LGB 0.7)
"""
import json
import os
import sys

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.metrics import average_precision_score, precision_score, recall_score, roc_auc_score
from xgboost import XGBClassifier

sys.path.insert(0, os.path.dirname(__file__))
from common import (DATA_PATH, DEMO_QUARTER, GRADE_CAUTION, GRADE_DANGER, OUT_DIR, SEED, TARGET,  # noqa: E402
                    TEST_START, W_LGB, W_XGB, load_feature_cols, setup_logging)

# 이번 분기 폐업 정보에서 직접 계산되는 변수
CLOSURE_COLS = ['전년_동기_대비_폐업_증감률', '폐업_률_y', '폐업_영업_개월_평균']

setup_logging('09_ablation_no_closure')

feature_cols = load_feature_cols()
df = pd.read_parquet(DATA_PATH, columns=feature_cols + [TARGET, '기준_년분기_코드'])
df['기준_년분기_코드'] = pd.to_numeric(df['기준_년분기_코드'], errors='coerce')
for c in feature_cols + [TARGET]:
    df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
tr, te = df[df['기준_년분기_코드'] < TEST_START], df[df['기준_년분기_코드'] >= TEST_START]
y_tr, y_te = tr[TARGET].astype(int), te[TARGET].astype(int).to_numpy()
ratio = float((y_tr == 0).sum()) / (y_tr == 1).sum()
q4 = (te['기준_년분기_코드'] == DEMO_QUARTER).to_numpy()
print(f'학습 {len(tr):,}행 / 시험 {len(te):,}행, 클래스 가중치 {ratio:.2f}')


def to_score(p):
    p = np.clip(p, 1e-4, 1 - 1e-4)
    return np.rint(np.clip(50 + 15 * np.log(p / (1 - p)), 0, 100))


def run(cols, name):
    X_tr = tr[cols].to_numpy(dtype=np.float64)
    X_te = te[cols].to_numpy(dtype=np.float64)
    xgb = XGBClassifier(n_estimators=400, max_depth=4, learning_rate=0.03, subsample=0.8, colsample_bytree=0.8,
                        min_child_weight=3, gamma=0.2, reg_alpha=1, reg_lambda=15, scale_pos_weight=ratio,
                        random_state=SEED, eval_metric='auc', n_jobs=-1).fit(X_tr, y_tr)
    lgb = LGBMClassifier(n_estimators=400, max_depth=4, learning_rate=0.03, subsample=0.8, colsample_bytree=0.8,
                         min_child_samples=20, reg_alpha=1, reg_lambda=15, scale_pos_weight=ratio,
                         random_state=SEED, n_jobs=-1, verbose=-1).fit(X_tr, y_tr)
    p = W_XGB * xgb.predict_proba(X_te)[:, 1] + W_LGB * lgb.predict_proba(X_te)[:, 1]
    s = to_score(p)
    base = y_te[q4].mean()
    danger = q4 & (s >= GRADE_DANGER)
    caution_up = q4 & (s >= GRADE_CAUTION)
    imp = pd.Series(xgb.get_booster().get_score(importance_type='total_gain'))
    imp.index = [cols[int(k[1:])] for k in imp.index]
    imp = (imp / imp.sum()).sort_values(ascending=False)
    r = {
        'name': name, 'n_features': len(cols),
        'roc_auc': roc_auc_score(y_te, p), 'pr_auc': average_precision_score(y_te, p),
        'precision': precision_score(y_te, p >= 0.5), 'recall': recall_score(y_te, p >= 0.5),
        'q4_danger_share': danger[q4].mean(), 'q4_danger_actual_rate': y_te[danger].mean(),
        'q4_danger_lift': y_te[danger].mean() / base, 'q4_caution_up_capture': y_te[caution_up].sum() / y_te[q4].sum(),
        'top_features': {k: round(float(v) * 100, 1) for k, v in imp.head(5).items()},
    }
    print(f'[{name}] 변수 {len(cols)}개 | ROC-AUC {r["roc_auc"]:.4f} | PR-AUC {r["pr_auc"]:.4f} | '
          f'정밀도 {r["precision"]:.3f} | 재현율 {r["recall"]:.3f} | Q4 위험등급 실제 과포화 {r["q4_danger_actual_rate"]:.1%} '
          f'(평균의 {r["q4_danger_lift"]:.1f}배) | 주의 이상이 잡은 과포화 {r["q4_caution_up_capture"]:.1%}')
    print(f'   중요도 상위 5 (XGB gain %): {r["top_features"]}')
    return r


full = run(feature_cols, '기준 재학습 (32개)')
drop = run([c for c in feature_cols if c not in CLOSURE_COLS], '폐업 변수 제외 (29개)')
saved = json.load(open(os.path.join(OUT_DIR, 'model_metrics.json'), encoding='utf-8'))['ensemble']
print(f'참고: 저장된 시연 모델 ROC-AUC {saved["roc_auc"]} / PR-AUC {saved["pr_auc"]}')

out = {'closure_cols_removed': CLOSURE_COLS, 'saved_model': saved,
       'retrain_full': {k: (round(float(v), 4) if isinstance(v, (float, np.floating)) else v) for k, v in full.items()},
       'retrain_no_closure': {k: (round(float(v), 4) if isinstance(v, (float, np.floating)) else v) for k, v in drop.items()}}
with open(os.path.join(OUT_DIR, 'ablation_no_closure.json'), 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)


def row(label, r):
    return (f'| {label} | {r["n_features"]} | {r["roc_auc"]:.3f} | {r["pr_auc"]:.3f} | {r["precision"]:.3f} | {r["recall"]:.3f} | '
            f'{r["q4_danger_actual_rate"]:.1%} ({r["q4_danger_lift"]:.1f}배) | {r["q4_caution_up_capture"]:.1%} |')


md = [
    '# 추가 실험: 폐업 관련 변수를 빼도 진단이 되는가', '',
    '> 시연·DB에 쓰는 결과는 바꾸지 않았음. 같은 정답(`과포화_위험_여부`), 같은 학습 설정, 같은 기간(2019~2023 학습 / 2024 시험)으로 다시 학습해 비교만 함.', '',
    f'**뺀 변수 ({len(CLOSURE_COLS)}개, 이번 분기 폐업 정보에서 직접 계산됨):** ' + ', '.join(f'`{c}`' for c in CLOSURE_COLS), '',
    '| 모델 | 변수 수 | ROC-AUC | PR-AUC | 정밀도 | 재현율 | 4분기 위험 등급의 실제 과포화 비율 | 4분기 주의 이상이 잡은 과포화 |',
    '|---|---:|---:|---:|---:|---:|---:|---:|',
    row('기준 재학습 (시연 모델과 같은 변수)', full),
    row('**폐업 변수 제외**', drop), '',
    f'- 저장된 시연 모델 성능: ROC-AUC {saved["roc_auc"]:.3f} / PR-AUC {saved["pr_auc"]:.3f} (기준 재학습이 이 값과 비슷하면 비교가 공정함)',
    f'- 폐업 변수를 빼면 ROC-AUC가 {full["roc_auc"]:.3f} → {drop["roc_auc"]:.3f} ({drop["roc_auc"] - full["roc_auc"]:+.3f}), '
    f'PR-AUC가 {full["pr_auc"]:.3f} → {drop["pr_auc"]:.3f} ({drop["pr_auc"] - full["pr_auc"]:+.3f}) 로 바뀜.',
    f'- 폐업 변수를 뺀 모델의 중요 변수 상위 5개 (XGBoost gain %): ' + ', '.join(f'{k} {v}' for k, v in drop['top_features'].items()), '',
    '## 읽는 법', '',
    '- 폐업 변수를 빼도 성능이 크게 남아 있으면: 모델이 폐업 정보만 베낀 게 아니라 매출·점포·입지 같은 다른 신호로도 과포화를 진단한다는 근거가 됨.',
    '- 떨어진 만큼은 "폐업 정보가 진단에 보탠 몫"임. 그래서 작품 명칭을 "예측"이 아닌 "진단"으로 정함.',
    '- 위험 등급 기준(75/50)은 같은 점수 공식을 그대로 적용함.',
]
with open(os.path.join(OUT_DIR, 'ablation_no_closure.md'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(md) + '\n')
print('[저장] output/ablation_no_closure.md, output/ablation_no_closure.json')
print(f'[요약] 폐업 변수 제외 ROC-AUC {drop["roc_auc"]:.3f} (기준 재학습 {full["roc_auc"]:.3f}), '
      f'PR-AUC {drop["pr_auc"]:.3f} (기준 {full["pr_auc"]:.3f})')
