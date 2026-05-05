"""
scratch/experiment_geo.py
지리적/물리적 제약(Geo Constraints) 피처 추가 전후 AUC 비교 실험
  - Day 2: 베이스라인 vs Geo Constraints 추가 AUC 비교 + 피처 중요도
  - Day 3: Ablation Study + 하이퍼파라미터 튜닝

실행:
    cd /Users/baekjiyun/Documents/capstone/main
    python scratch/experiment_geo.py
"""

import os
import sys
import pickle
import itertools
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from dotenv import load_dotenv
load_dotenv()

from src.data_acquisition import PublicDataAPI
from src.spatial_processor import SpatialProcessor
from src.feature_merger import FeatureMerger
from src.feature_engineering.spatial_features import build_geo_constraint_features

# ──────────────────────────────────────────────────────────
# 설정
# ──────────────────────────────────────────────────────────
SHP_PATH  = "data/(도로명주소)기초구역_서울/TL_KODIS_BAS_11_202604.shp"
DUMP_PATH = "scratch/data_dump.pkl"
CACHE_DIR = "scratch"
RESULTS   = []

BASE_FEATURES = [
    'local_competitors', 'store_age', 'saturation',
    'avg_sales', 'pop_density', 'sales_per_store'
]
GEO_FEATURES = [
    'elevation', 'slope', 'dist_crosswalk',
    'dist_railway', 'dist_river'
]


def log(tag, msg, value=None):
    entry = f"[{tag}] {msg}" + (f" → {value}" if value is not None else "")
    print(entry)
    RESULTS.append(entry)


def run_cv(X, y, n_estimators=100, max_depth=4, learning_rate=0.05, reg_lambda=5):
    ratio = float(np.sum(y == 0)) / max(np.sum(y == 1), 1)
    model = XGBClassifier(
        n_estimators=n_estimators, max_depth=max_depth,
        learning_rate=learning_rate, reg_lambda=reg_lambda,
        scale_pos_weight=ratio, eval_metric='auc', random_state=42
    )
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(model, X, y, cv=cv, scoring='roc_auc')
    return scores.mean(), scores.std()


# ──────────────────────────────────────────────────────────
# Step 1: 데이터 로드 및 공간 매핑
# ──────────────────────────────────────────────────────────
print("\n" + "="*55)
print("Step 1: 데이터 로드 및 BAS_ID 매핑")
print("="*55)

with open(DUMP_PATH, 'rb') as f:
    raw = pickle.load(f)

df_stores = pd.DataFrame(raw['stores'])
df_sales  = pd.DataFrame(raw['sales'])
df_pop    = pd.DataFrame(raw['pop'])
log("Data", "점포 수", len(df_stores))
log("Data", "영업/폐업 비율",
    f"{(df_stores['is_closed']==0).sum()} / {(df_stores['is_closed']==1).sum()}")

sp         = SpatialProcessor(bas_shp_path=SHP_PATH)
gdf_stores = sp.create_point_geometry(df_stores, lat_col='lat', lng_col='lon')
gdf_mapped = sp.assign_bas_id(gdf_stores)
log("Spatial", "BAS_ID 매핑 성공", gdf_mapped['BAS_ID'].notna().sum())

# ──────────────────────────────────────────────────────────
# Step 2: 베이스라인 마스터 테이블
# ──────────────────────────────────────────────────────────
print("\n" + "="*55)
print("Step 2: 베이스라인 마스터 테이블 생성")
print("="*55)

fm          = FeatureMerger()
master_base = fm.create_master_table(
    df_stores=pd.DataFrame(gdf_mapped),
    df_sales=df_sales,
    df_pop=df_pop,
    df_geo=None
)
df_base = master_base.dropna(subset=BASE_FEATURES + ['is_closed'])
X_base  = df_base[BASE_FEATURES]
y_base  = df_base['is_closed'].astype(int)
log("Baseline", "학습 샘플 수", len(df_base))

# ──────────────────────────────────────────────────────────
# Step 3: Geo Constraints 피처 빌드 (캐시 활용)
# ──────────────────────────────────────────────────────────
print("\n" + "="*55)
print("Step 3: Geo Constraints 피처 빌드 (캐시 활용)")
print("="*55)

api     = PublicDataAPI()
gdf_geo = build_geo_constraint_features(gdf_mapped, api, cache_dir=CACHE_DIR)

for col in GEO_FEATURES:
    valid = gdf_geo[col].notna().sum()
    mean  = gdf_geo[col].mean() if valid > 0 else float('nan')
    log("Geo", f"{col}: 유효={valid}/{len(gdf_geo)}", f"mean={mean:.2f}")

# ──────────────────────────────────────────────────────────
# Step 4: Geo 포함 마스터 테이블
# ──────────────────────────────────────────────────────────
print("\n" + "="*55)
print("Step 4: Geo Constraints 포함 마스터 테이블 생성")
print("="*55)

master_geo = fm.create_master_table(
    df_stores=pd.DataFrame(gdf_mapped),
    df_sales=df_sales,
    df_pop=df_pop,
    df_geo=pd.DataFrame(gdf_geo)
)
all_features = BASE_FEATURES + GEO_FEATURES
df_geo_full  = master_geo.dropna(subset=all_features + ['is_closed'])
X_geo        = df_geo_full[all_features]
y_geo        = df_geo_full['is_closed'].astype(int)
log("Geo+Base", "학습 샘플 수", len(df_geo_full))

# ──────────────────────────────────────────────────────────
# Step 5: 베이스라인 vs Geo 추가 AUC 비교
# ──────────────────────────────────────────────────────────
print("\n" + "="*55)
print("Step 5: AUC 비교 — 베이스라인 vs Geo Constraints (5-Fold CV)")
print("="*55)

auc_base, std_base = run_cv(X_base, y_base)
auc_geo,  std_geo  = run_cv(X_geo,  y_geo)
delta = auc_geo - auc_base

log("AUC", "베이스라인 (Geo 제외)", f"{auc_base:.4f} ±{std_base:.4f}")
log("AUC", "Geo Constraints 추가",  f"{auc_geo:.4f} ±{std_geo:.4f}")
log("Delta", "AUC 변화", f"{delta:+.4f} ({'향상' if delta > 0 else '하락'})")

# ──────────────────────────────────────────────────────────
# Step 6: 피처 중요도 (Geo 포함 모델)
# ──────────────────────────────────────────────────────────
print("\n" + "="*55)
print("Step 6: 피처 중요도")
print("="*55)

ratio = float(np.sum(y_geo == 0)) / max(np.sum(y_geo == 1), 1)
imp_model = XGBClassifier(
    n_estimators=100, max_depth=4, learning_rate=0.05,
    reg_lambda=5, scale_pos_weight=ratio,
    eval_metric='auc', random_state=42
)
imp_model.fit(X_geo, y_geo)

importances = sorted(
    zip(all_features, imp_model.feature_importances_),
    key=lambda x: x[1], reverse=True
)
for feat, imp in importances:
    marker = " ◀ Geo" if feat in GEO_FEATURES else ""
    log("Importance", feat, f"{imp:.4f}{marker}")

# ──────────────────────────────────────────────────────────
# Step 7: Ablation Study — Geo 피처 조합별 AUC
# ──────────────────────────────────────────────────────────
print("\n" + "="*55)
print("Step 7: Ablation Study — Geo 피처 조합별 AUC")
print("="*55)

ablation_cases = [
    ("베이스라인",                   BASE_FEATURES),
    ("+ elevation/slope",           BASE_FEATURES + ['elevation', 'slope']),
    ("+ dist_crosswalk",            BASE_FEATURES + ['dist_crosswalk']),
    ("+ dist_railway/river",        BASE_FEATURES + ['dist_railway', 'dist_river']),
    ("+ Geo 전체",                   BASE_FEATURES + GEO_FEATURES),
]

ablation_results = []
for label, feats in ablation_cases:
    auc, std = run_cv(df_geo_full[feats], y_geo)
    ablation_results.append((label, auc, std))
    log("Ablation", label, f"AUC={auc:.4f} ±{std:.4f}")

# ──────────────────────────────────────────────────────────
# Step 8: 하이퍼파라미터 튜닝
# ──────────────────────────────────────────────────────────
print("\n" + "="*55)
print("Step 8: 하이퍼파라미터 튜닝 (Grid Search)")
print("="*55)

param_grid = {
    'n_estimators':  [100, 200, 300],
    'max_depth':     [3, 4, 5],
    'learning_rate': [0.01, 0.05, 0.1],
    'reg_lambda':    [1, 5, 10],
}

total = (len(param_grid['n_estimators']) * len(param_grid['max_depth']) *
         len(param_grid['learning_rate']) * len(param_grid['reg_lambda']))
print(f"총 {total}가지 조합 탐색 중...")

tuning_results = []
best_auc, best_params = 0.0, {}

for n_est, depth, lr, lam in itertools.product(
    param_grid['n_estimators'],
    param_grid['max_depth'],
    param_grid['learning_rate'],
    param_grid['reg_lambda'],
):
    auc, std = run_cv(X_geo, y_geo,
                      n_estimators=n_est, max_depth=depth,
                      learning_rate=lr, reg_lambda=lam)
    tuning_results.append({
        'n_estimators': n_est, 'max_depth': depth,
        'learning_rate': lr, 'reg_lambda': lam,
        'auc': auc, 'std': std
    })
    if auc > best_auc:
        best_auc = auc
        best_params = dict(n_estimators=n_est, max_depth=depth,
                           learning_rate=lr, reg_lambda=lam)

df_tuning = pd.DataFrame(tuning_results).sort_values('auc', ascending=False)

print("\n상위 5개 조합:")
for _, row in df_tuning.head(5).iterrows():
    print(f"  n={int(row['n_estimators'])}, depth={int(row['max_depth'])}, "
          f"lr={row['learning_rate']}, λ={int(row['reg_lambda'])}  "
          f"→ AUC {row['auc']:.4f} ±{row['std']:.4f}")

log("BestParams", str(best_params), f"AUC={best_auc:.4f}")

# ──────────────────────────────────────────────────────────
# Step 9: 최종 요약
# ──────────────────────────────────────────────────────────
print("\n" + "="*55)
print("Step 9: 최종 AUC 요약")
print("="*55)

log("Final", "베이스라인",              f"{auc_base:.4f}")
log("Final", "Geo 추가 (기본 파라미터)", f"{auc_geo:.4f}")
log("Final", "Geo + 튜닝 (최적 파라미터)", f"{best_auc:.4f}")
log("Final", "총 AUC 향상",             f"{best_auc - auc_base:+.4f}")

# ──────────────────────────────────────────────────────────
# 결과 저장
# ──────────────────────────────────────────────────────────
report_path = "scratch/experiment_geo_report.txt"
with open(report_path, 'w', encoding='utf-8') as f:
    f.write("=== Geo Constraints 피처 AUC 비교 실험 결과 ===\n\n")

    f.write("[ 베이스라인 vs Geo Constraints ]\n")
    f.write(f"  베이스라인          AUC={auc_base:.4f} ±{std_base:.4f}\n")
    f.write(f"  Geo Constraints 추가 AUC={auc_geo:.4f}  ±{std_geo:.4f}\n")
    f.write(f"  변화                    {delta:+.4f}\n\n")

    f.write("[ Ablation Study ]\n")
    for label, auc, std in ablation_results:
        f.write(f"  {label:<25} AUC={auc:.4f} ±{std:.4f}\n")

    f.write("\n[ 상위 5 하이퍼파라미터 조합 ]\n")
    for _, row in df_tuning.head(5).iterrows():
        f.write(f"  n={int(row['n_estimators'])}, depth={int(row['max_depth'])}, "
                f"lr={row['learning_rate']}, λ={int(row['reg_lambda'])}  "
                f"AUC={row['auc']:.4f} ±{row['std']:.4f}\n")

    f.write("\n[ 전체 로그 ]\n")
    for line in RESULTS:
        f.write(line + "\n")

print(f"\n[Report] 결과 저장 → {report_path}")
print("\n" + "="*55)
print("실험 완료")
print("="*55)
