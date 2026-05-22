"""
Proposed 모델: DS5 포함
"""
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.metrics import roc_auc_score, accuracy_score, classification_report, confusion_matrix
import json
import joblib

print("=" * 60)
print("실험 2B: Proposed 모델 학습 (DS5 포함)")
print("=" * 60)

# =========================================================
# 1. 데이터 로드
# =========================================================
print("\n1. 데이터 로드...")

train_df = pd.read_parquet('data/ds5_period_train.parquet')
test_df = pd.read_parquet('data/ds5_period_test.parquet')

print(f"  Train: {len(train_df):,}행")
print(f"  Test: {len(test_df):,}행")

# =========================================================
# 2. Feature 선택 (DS5 포함)
# =========================================================
print("\n2. Feature 선택 (DS5 포함)...")

target_col = '과포화_위험_여부'

# 기본 feature
base_features = [
    '당월_매출_금액',
    '당월_매출_건수',
    '점포_수_y',
    '유사_업종_점포_수_y',
    '개업_율_y',
    '폐업_률_y',
    '프랜차이즈_점포_수_y',
    '프랜차이즈점포비율(%)',
    '개인점포비율(%)',
    '상권_전체점포_수',
    '상권 내부 업종 점유율(%)',
    '운영_영업_개월_평균',
    '폐업_영업_개월_평균',
    '유효_수요_전환율',
    '점포당_평균_매출',
    '전년_동기_대비_폐업_증감률',
    '소득_구간_코드',
    '상권_업종_적합도',
    '유사업종_점포비율',
    '점포당_매출_밀도'
]

# DS5 feature 추가
ds5_features = [
    '주중_오전_avg',
    '주중_점심_avg',
    '주중_저녁_avg',
    '주중_야간_avg',
    '주말_주간_avg',
    '주말_야간_avg',
    '주야간비율',
    'population_slope',
    'population_entropy',
    '평균인구'
]

feature_cols = base_features + ds5_features

# 실제 존재하는 컬럼만 사용
feature_cols = [c for c in feature_cols if c in train_df.columns]

print(f"  기본 Feature: {len(base_features)}개")
print(f"  DS5 Feature: {len(ds5_features)}개")
print(f"  총 Feature: {len(feature_cols)}개")

# DS5 매칭 확인
ds5_train = train_df['주중_오전_avg'].notna().sum()
ds5_test = test_df['주중_오전_avg'].notna().sum()
print(f"\n  DS5 데이터:")
print(f"    Train: {ds5_train:,}행 ({ds5_train/len(train_df)*100:.1f}%)")
print(f"    Test: {ds5_test:,}행 ({ds5_test/len(test_df)*100:.1f}%)")

# =========================================================
# 3. 데이터 준비
# =========================================================
print("\n3. 데이터 준비...")

# 숫자형 변환 (NaN 유지 - XGBoost가 처리)
for col in feature_cols + [target_col]:
    train_df[col] = pd.to_numeric(train_df[col], errors='coerce')
    test_df[col] = pd.to_numeric(test_df[col], errors='coerce')

# Target만 0으로 채우기
train_df[target_col] = train_df[target_col].fillna(0)
test_df[target_col] = test_df[target_col].fillna(0)

X_train = train_df[feature_cols]
y_train = train_df[target_col].astype(int)
X_test = test_df[feature_cols]
y_test = test_df[target_col].astype(int)

print(f"  X_train: {X_train.shape}")
print(f"  X_test: {X_test.shape}")
print(f"  클래스 분포 (Train):")
print(f"    정상: {(y_train==0).sum():,}개")
print(f"    과포화: {(y_train==1).sum():,}개")

# =========================================================
# 4. 모델 학습
# =========================================================
print("\n4. Proposed 모델 학습 (DS5 포함)...")

model = XGBClassifier(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    random_state=42,
    eval_metric='logloss'
)

model.fit(X_train, y_train)

print("  ✅ 학습 완료")

# =========================================================
# 5. 예측 및 평가
# =========================================================
print("\n5. 모델 평가...")

y_pred = model.predict(X_test)
y_pred_proba = model.predict_proba(X_test)[:, 1]

auc = roc_auc_score(y_test, y_pred_proba)
acc = accuracy_score(y_test, y_pred)

print(f"  AUC Score: {auc:.4f}")
print(f"  Accuracy: {acc:.4f}")

# =========================================================
# 6. 상세 결과
# =========================================================
print("\n6. 상세 결과...")

print("\n--- Classification Report ---")
print(classification_report(y_test, y_pred))

print("\n--- Confusion Matrix ---")
cm = confusion_matrix(y_test, y_pred)
print(cm)

# =========================================================
# 7. Feature Importance
# =========================================================
print("\n7. Feature Importance...")

feature_importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print("\n--- Top 15 Features ---")
for idx, row in feature_importance.head(15).iterrows():
    is_ds5 = row['feature'] in ds5_features
    marker = "🆕 " if is_ds5 else "   "
    print(f"{marker}{row['feature']:30s} {row['importance']:.6f}")

# DS5 feature 순위
print("\n--- DS5 Feature 순위 ---")
ds5_importance = feature_importance[feature_importance['feature'].isin(ds5_features)]
for idx, row in ds5_importance.iterrows():
    rank = feature_importance.index.get_loc(idx) + 1
    print(f"  #{rank:2d} {row['feature']:30s} {row['importance']:.6f}")

# =========================================================
# 8. 결과 저장
# =========================================================
print("\n8. 결과 저장...")

# 폴더 생성
import os
os.makedirs('results', exist_ok=True)

# 결과 저장
results = {
    'model_name': 'Proposed (DS5 포함)',
    'data_period': '2023-2024',
    'train_size': len(train_df),
    'test_size': len(test_df),
    'num_features': len(feature_cols),
    'ds5_included': True,
    'ds5_features': ds5_features,
    'metrics': {
        'auc': float(auc),
        'accuracy': float(acc)
    },
    'confusion_matrix': cm.tolist(),
    'feature_importance': feature_importance.to_dict('records')
}

with open('results/proposed_results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print("  ✅ results/proposed_results.json 저장 완료")

# 모델 저장
joblib.dump(model, 'results/proposed_model.pkl')
print("  ✅ results/proposed_model.pkl 저장 완료")

# Feature Importance CSV
feature_importance.to_csv('results/proposed_feature_importance.csv', index=False)
print("  ✅ results/proposed_feature_importance.csv 저장 완료")

# =========================================================
# 9. 요약
# =========================================================
print("\n" + "=" * 60)
print("Proposed 모델 학습 완료!")
print("=" * 60)
print(f"\n성능:")
print(f"  AUC Score: {auc:.4f}")
print(f"  Accuracy: {acc:.4f}")
print(f"\nFeature:")
print(f"  기본 {len(base_features)}개 + DS5 {len(ds5_features)}개 = 총 {len(feature_cols)}개")
print(f"\n다음 단계:")
print(f"  python src/experiments/compare_results.py")
