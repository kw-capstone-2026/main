import pandas as pd
import numpy as np
import os
import sys
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report

# 내부 모듈 참조를 위한 경로 설정
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.models.baseline_xgboost import BaselineXGBoost

def train_and_export_baseline():
    """
    통합 데이터셋을 사용하여 XGBoost 베이스라인 모델을 학습하고 결과를 출력합니다.
    팀원들이 보조 데이터를 추가했을 때 비교 기준으로 활용됩니다.
    """
    data_path = 'data/parquet_datas/final_merged_commercial_data.parquet'
    
    if not os.path.exists(data_path):
        print(f"Error: {data_path} 를 찾을 수 없습니다. 데이터 병합을 먼저 진행하세요.")
        return

    print("1. 데이터 로딩 및 피처 선택...")
    df = pd.read_parquet(data_path)
    
    target_col = '과포화_위험_여부'
    feature_cols = [
        '당월_매출_금액', '당월_매출_건수', '점포_수', '유사_업종_점포_수', 
        '개업_율', '폐업_률', '프랜차이즈_점포_수', '프랜차이즈점포비율(%)', 
        '개인점포비율(%)', '상권_전체점포_수', '상권 내부 업종 점유율(%)', 
        '운영_영업_개월_평균', '폐업_영업_개월_평균', '유효_수요_전환율', 
        '점포당_평균_매출', '전년_동기_대비_폐업_증감률'
    ]
    
    # 존재하는 컬럼만 사용
    feature_cols = [c for c in feature_cols if c in df.columns]

    # 2. 시계열 기반 데이터 분할 (2019-2023: Train / 2024: Test)
    train_df = df[df['기준_년분기_코드'] < 20241].copy()
    test_df = df[df['기준_년분기_코드'] >= 20241].copy()
    
    for col in feature_cols + [target_col]:
        train_df[col] = pd.to_numeric(train_df[col], errors='coerce').fillna(0)
        test_df[col] = pd.to_numeric(test_df[col], errors='coerce').fillna(0)
        
    X_train = train_df[feature_cols]
    y_train = train_df[target_col].astype(int)
    X_test = test_df[feature_cols]
    y_test = test_df[target_col].astype(int)

    # 3. 모델 학습 (클래스 불균형 처리 포함)
    print(f"2. XGBoost 모델 학습 시작 (데이터 규모: {len(X_train)} 행)...")
    ratio = float(np.sum(y_train == 0)) / np.sum(y_train == 1) if np.sum(y_train == 1) > 0 else 1.0
    
    model = XGBClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.05,
        scale_pos_weight=ratio,
        reg_lambda=10,
        random_state=42,
        eval_metric='auc'
    )
    
    model.fit(X_train, y_train)
    
    # 4. 성능 평가 및 리포팅
    preds = model.predict(X_test)
    probs = model.predict_proba(X_test)[:, 1]
    
    print("\n" + "="*30)
    print(" [XGBoost Baseline Report] ")
    print("="*30)
    print(f"AUC Score: {roc_auc_score(y_test, probs):.4f}")
    print(f"Accuracy:  {accuracy_score(y_test, preds):.4f}")
    print("\n--- Classification Report ---")
    print(classification_report(y_test, preds))

    # 5. 피처 중요도 출력 (Top 10)
    importance = model.feature_importances_
    feat_imp = pd.Series(importance, index=feature_cols).sort_values(ascending=False)
    print("\n--- Top 10 Feature Importance ---")
    print(feat_imp.head(10))

    return model

if __name__ == "__main__":
    train_and_export_baseline()
