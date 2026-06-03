"""STEP 1 — 전처리, XGBoost 학습, 성능 지표 계산.

- 타겟: 분기 폐업 발생 여부 (폐업_점포_수 > 0)
- 누수 변수 제외, 시계열 분할(2024 = 테스트)
- Baseline vs scale_pos_weight(비용민감) 두 모델 학습
- ROC/PR 곡선, 임계값 스윕, 혼동행렬, 변수 중요도를 artifacts/ 에 저장

실행:  python step1_model.py
"""
import json
import warnings

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import (accuracy_score, average_precision_score,
                             confusion_matrix, f1_score, precision_recall_curve,
                             precision_score, recall_score, roc_auc_score, roc_curve)

import config as C

warnings.filterwarnings("ignore")


def build_xy(df):
    """피처 행렬 X와 타겟 y를 구성."""
    df[C.TARGET] = (df["폐업_점포_수"] > 0).astype(int)

    num_feats = [c for c in C.NUM_FEATURES if c in df.columns]
    X = df[num_feats].copy()
    for c in C.CAT_FEATURES:
        X[c + "_enc"] = df[c].astype("category").cat.codes

    X = X.replace([np.inf, -np.inf], np.nan)
    X = X.fillna(X.median(numeric_only=True))
    y = df[C.TARGET].values
    return X, y


def metrics_at(y_true, p, thr):
    """주어진 임계값에서의 분류 지표."""
    yp = (p >= thr).astype(int)
    return dict(
        acc=accuracy_score(y_true, yp),
        prec=precision_score(y_true, yp, zero_division=0),
        rec=recall_score(y_true, yp, zero_division=0),
        f1=f1_score(y_true, yp, zero_division=0),
        cm=confusion_matrix(y_true, yp).tolist(),
    )


def main():
    df = pd.read_parquet(C.DATA_PATH)
    X, y = build_xy(df)
    print(f"피처수 {X.shape[1]} | 표본 {X.shape[0]:,} | 양성률 {y.mean():.4f}")

    # 시계열 분할: 최근 4개 분기를 테스트셋으로 (미래 정보 누수 방지)
    q = df["기준_년분기_코드"].values
    test_mask = np.isin(q, C.TEST_QUARTERS)
    Xtr, ytr = X[~test_mask], y[~test_mask]
    Xte, yte = X[test_mask], y[test_mask]
    print(f"train {Xtr.shape[0]:,} | test {Xte.shape[0]:,}")

    common = dict(n_estimators=300, max_depth=6, learning_rate=0.1,
                  subsample=0.8, colsample_bytree=0.8, tree_method="hist",
                  eval_metric="aucpr", n_jobs=4, random_state=42)

    # A) Baseline (불균형 무처리)
    m_base = xgb.XGBClassifier(**common)
    m_base.fit(Xtr, ytr)
    p_base = m_base.predict_proba(Xte)[:, 1]

    # B) 비용민감 학습 (scale_pos_weight = 음성/양성 비율)
    spw = (ytr == 0).sum() / (ytr == 1).sum()
    m_w = xgb.XGBClassifier(**common, scale_pos_weight=spw)
    m_w.fit(Xtr, ytr)
    p_w = m_w.predict_proba(Xte)[:, 1]
    print(f"scale_pos_weight = {spw:.2f}")

    # ── 지표 집계 ────────────────────────────────────────────
    results = {
        "pos_rate_test": float(yte.mean()),
        "base": dict(roc=roc_auc_score(yte, p_base),
                     pr=average_precision_score(yte, p_base)),
        "weighted": dict(roc=roc_auc_score(yte, p_w),
                         pr=average_precision_score(yte, p_w)),
        "always_neg_acc": float((yte == 0).mean()),
    }

    # ROC / PR 곡선 좌표
    fpr_b, tpr_b, _ = roc_curve(yte, p_base)
    fpr_w, tpr_w, _ = roc_curve(yte, p_w)
    pr_b, rc_b, _ = precision_recall_curve(yte, p_base)
    pr_w, rc_w, _ = precision_recall_curve(yte, p_w)
    np.savez(C.ART_DIR / "curves.npz",
             fpr_b=fpr_b, tpr_b=tpr_b, fpr_w=fpr_w, tpr_w=tpr_w,
             pr_b=pr_b, rc_b=rc_b, pr_w=pr_w, rc_w=rc_w)

    # 임계값 스윕 (baseline 확률 기준)
    ths = np.linspace(0.05, 0.95, 19)
    sweep = {"thr": ths.tolist(), "prec": [], "rec": [], "f1": []}
    for t in ths:
        yp = (p_base >= t).astype(int)
        sweep["prec"].append(precision_score(yte, yp, zero_division=0))
        sweep["rec"].append(recall_score(yte, yp, zero_division=0))
        sweep["f1"].append(f1_score(yte, yp, zero_division=0))
    best_t = float(ths[int(np.argmax(sweep["f1"]))])

    # 혼동행렬: 기본 0.5  vs  F1 최적 임계값
    cm_05 = metrics_at(yte, p_base, 0.5)
    cm_bt = metrics_at(yte, p_base, best_t)

    # 변수 중요도(gain) 상위 15
    imp = pd.Series(m_w.get_booster().get_score(importance_type="gain"))
    fmap = {f"f{i}": c for i, c in enumerate(X.columns)}
    imp.index = [fmap.get(i, i) for i in imp.index]
    imp = imp.sort_values(ascending=False).head(15)

    out = dict(results=results, sweep=sweep, best_t=best_t,
               cm_05=cm_05, cm_bt=cm_bt, spw=float(spw),
               imp_idx=imp.index.tolist(), imp_val=imp.values.tolist())
    with open(C.ART_DIR / "model_out.json", "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("=== 요약 ===")
    print(f"Baseline  ROC-AUC {results['base']['roc']:.3f} | PR-AUC {results['base']['pr']:.3f}")
    print(f"Weighted  ROC-AUC {results['weighted']['roc']:.3f} | PR-AUC {results['weighted']['pr']:.3f}")
    print(f"always-neg accuracy {results['always_neg_acc']:.3f}")
    print(f"best F1 threshold {best_t:.2f}  (재현율 {cm_05['rec']:.0%} → {cm_bt['rec']:.0%})")


if __name__ == "__main__":
    main()
