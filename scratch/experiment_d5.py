"""
scratch/experiment_d5.py
D5 지리적/물리적 제약 피처 추가 전후 AUC 비교 실험

실행:
    cd /Users/baekjiyun/Documents/capstone/main
    python scratch/experiment_d5.py
"""

import os
import sys
import pickle
import numpy as np
import pandas as pd
import geopandas as gpd
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
SHP_PATH   = "data/(도로명주소)기초구역_서울/TL_KODIS_BAS_11_202604.shp"
DUMP_PATH  = "scratch/data_dump.pkl"
CACHE_DIR  = "scratch"
RESULTS    = []

BASE_FEATURES = [
    'local_competitors', 'store_age', 'saturation',
    'avg_sales', 'pop_density', 'sales_per_store'
]
D5_FEATURES = [
    'elevation', 'slope', 'dist_crosswalk',
    'dist_railway', 'dist_river'
]

def log(tag, msg, value=None):
    entry = f"[{tag}] {msg}" + (f" → {value}" if value is not None else "")
    print(entry)
    RESULTS.append(entry)


def run_cv(X, y, label):
    ratio = float(np.sum(y == 0)) / max(np.sum(y == 1), 1)
    model = XGBClassifier(
        n_estimators=100, max_depth=4, learning_rate=0.05,
        reg_lambda=5, scale_pos_weight=ratio,
        eval_metric='auc', random_state=42
    )
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(model, X, y, cv=cv, scoring='roc_auc')
    log("AUC", f"{label}", f"{scores.mean():.4f} ± {scores.std():.4f}")
    return scores.mean()


# ──────────────────────────────────────────────────────────
# 1. 데이터 로드 및 공간 매핑
# ──────────────────────────────────────────────────────────
print("\n" + "="*55)
print("Step 1: 데이터 로드 및 BAS_ID 매핑")
print("="*55)

with open(DUMP_PATH, 'rb') as f:
    raw = pickle.load(f)

df_stores = pd.DataFrame(raw['stores'])
df_sales  = pd.DataFrame(raw['sales'])
df_pop    = pd.DataFrame(raw['pop'])
log("Data", f"점포 수", len(df_stores))
log("Data", f"영업/폐업 비율",
    f"{(df_stores['is_closed']==0).sum()} / {(df_stores['is_closed']==1).sum()}")

sp         = SpatialProcessor(bas_shp_path=SHP_PATH)
gdf_stores = sp.create_point_geometry(df_stores, lat_col='lat', lng_col='lon')
gdf_mapped = sp.assign_bas_id(gdf_stores)
log("Spatial", f"BAS_ID 매핑 성공", gdf_mapped['BAS_ID'].notna().sum())

# ──────────────────────────────────────────────────────────
# 2. 베이스라인 마스터 테이블 (D5 피처 없음)
# ──────────────────────────────────────────────────────────
print("\n" + "="*55)
print("Step 2: 베이스라인 마스터 테이블 생성")
print("="*55)

fm = FeatureMerger()
master_base = fm.create_master_table(
    df_stores=pd.DataFrame(gdf_mapped),
    df_sales=df_sales,
    df_pop=df_pop,
    df_geo=None
)
df_base = master_base.dropna(subset=BASE_FEATURES + ['is_closed'])
X_base  = df_base[BASE_FEATURES]
y_base  = df_base['is_closed'].astype(int)
log("Baseline", f"학습 샘플 수", len(df_base))

# ──────────────────────────────────────────────────────────
# 3. D5 피처 빌드
# ──────────────────────────────────────────────────────────
print("\n" + "="*55)
print("Step 3: D5 지리적 제약 피처 빌드 (캐시 활용)")
print("="*55)

api     = PublicDataAPI()
gdf_d5  = build_geo_constraint_features(gdf_mapped, api, cache_dir=CACHE_DIR)

for col in D5_FEATURES:
    valid = gdf_d5[col].notna().sum()
    mean  = gdf_d5[col].mean() if valid > 0 else float('nan')
    log("D5", f"{col}: 유효={valid}/{len(gdf_d5)}", f"mean={mean:.2f}")

# ──────────────────────────────────────────────────────────
# 4. D5 포함 마스터 테이블
# ──────────────────────────────────────────────────────────
print("\n" + "="*55)
print("Step 4: D5 포함 마스터 테이블 생성")
print("="*55)

master_d5 = fm.create_master_table(
    df_stores=pd.DataFrame(gdf_mapped),
    df_sales=df_sales,
    df_pop=df_pop,
    df_geo=pd.DataFrame(gdf_d5)
)
all_features = BASE_FEATURES + D5_FEATURES
df_d5 = master_d5.dropna(subset=all_features + ['is_closed'])
X_d5  = df_d5[all_features]
y_d5  = df_d5['is_closed'].astype(int)
log("D5+Base", f"학습 샘플 수", len(df_d5))

# ──────────────────────────────────────────────────────────
# 5. AUC 비교
# ──────────────────────────────────────────────────────────
print("\n" + "="*55)
print("Step 5: AUC 비교 (5-Fold CV)")
print("="*55)

auc_base = run_cv(X_base, y_base, "베이스라인 (D5 제외)")
auc_d5   = run_cv(X_d5,   y_d5,   "D5 추가")
delta    = auc_d5 - auc_base
log("Delta", "AUC 변화", f"{delta:+.4f} ({'향상' if delta > 0 else '하락'})")

# ──────────────────────────────────────────────────────────
# 6. 피처 중요도 (D5 포함 모델)
# ──────────────────────────────────────────────────────────
print("\n" + "="*55)
print("Step 6: 피처 중요도")
print("="*55)

ratio = float(np.sum(y_d5 == 0)) / max(np.sum(y_d5 == 1), 1)
final_model = XGBClassifier(
    n_estimators=100, max_depth=4, learning_rate=0.05,
    reg_lambda=5, scale_pos_weight=ratio,
    eval_metric='auc', random_state=42
)
final_model.fit(X_d5, y_d5)

importances = sorted(
    zip(all_features, final_model.feature_importances_),
    key=lambda x: x[1], reverse=True
)
for feat, imp in importances:
    marker = " ◀ D5" if feat in D5_FEATURES else ""
    log("Importance", f"{feat}", f"{imp:.4f}{marker}")

# ──────────────────────────────────────────────────────────
# 결과 저장
# ──────────────────────────────────────────────────────────
report_path = "scratch/experiment_d5_report.txt"
with open(report_path, 'w', encoding='utf-8') as f:
    f.write("=== D5 지리적/물리적 제약 피처 AUC 비교 실험 결과 ===\n\n")
    for line in RESULTS:
        f.write(line + "\n")

print(f"\n[Report] 결과 저장 → {report_path}")
print("\n" + "="*55)
print("실험 완료")
print("="*55)
