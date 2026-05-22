"""
Baseline 모델: DS5 제외
"""
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.metrics import roc_auc_score, accuracy_score, classification_report, confusion_matrix
import json
import joblib

print("=" * 60)
print("실험 2A: Baseline 모델 학습 (DS5 제외)")
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
# 2. Feature 선택 (DS5 제외)
# =========================================================
print("\n2. Feature 선택 (DS5 제외)...")

target_col = '과포화_위험_여부'

# DS5 제외한 feature 목록
feature_cols = [
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

# 실제 존재하는 컬럼만 사용
feature_cols = [c for c in feature_cols if c in train_df.columns]

print(f"  총 Feature 수: {len(feature_cols)}개")
print(f"  DS5 Feature: 제외")

# =========================================================
# 3. 데이터 준비
# =========================================================
print("\n3. 데이터 준비...")

# 숫자형 변환
for col in feature_cols + [target_col]:
    train_df[col] = pd.to_numeric(train_df[col], errors='coerce').fillna(0)
    test_df[col] = pd.to_numeric(test_df[col], errors='coerce').fillna(0)

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
print("\n4. Baseline 모델 학습...")

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
    print(f"  {row['feature']:30s} {row['importance']:.6f}")

# =========================================================
# 8. 결과 저장
# =========================================================
print("\n8. 결과 저장...")

# 폴더 생성
import os
os.makedirs('results', exist_ok=True)

# 결과 저장
results = {
    'model_name': 'Baseline (DS5 제외)',
    'data_period': '2023-2024',
    'train_size': len(train_df),
    'test_size': len(test_df),
    'num_features': len(feature_cols),
    'ds5_included': False,
    'metrics': {
        'auc': float(auc),
        'accuracy': float(acc)
    },
    'confusion_matrix': cm.tolist(),
    'feature_importance': feature_importance.to_dict('records')
}

with open('results/baseline_results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print("  ✅ results/baseline_results.json 저장 완료")

# 모델 저장
joblib.dump(model, 'results/baseline_model.pkl')
print("  ✅ results/baseline_model.pkl 저장 완료")

# Feature Importance CSV
feature_importance.to_csv('results/baseline_feature_importance.csv', index=False)
print("  ✅ results/baseline_feature_importance.csv 저장 완료")

# =========================================================
# 9. 요약
# =========================================================
print("\n" + "=" * 60)
print("Baseline 모델 학습 완료!")
print("=" * 60)
print(f"\n성능:")
print(f"  AUC Score: {auc:.4f}")
print(f"  Accuracy: {acc:.4f}")
print(f"\nFeature:")
print(f"  총 {len(feature_cols)}개 (DS5 제외)")
print(f"\n다음 단계:")
print(f"  python src/experiments/train_proposed_model.py")
