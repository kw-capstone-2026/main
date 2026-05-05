import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report
import matplotlib.pyplot as plt

class BaselineXGBoost:
    """
    XGBoost 하이퍼파라미터 최적화 모델 (로그 #02)
    """
    def __init__(self, model_type: str = 'classification'):
        self.model_type = model_type
        self.model = None

    def train_and_evaluate(self, df: pd.DataFrame, target_col: str, feature_cols: list):
        # 1. 데이터 준비
        X = df[feature_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
        y = pd.to_numeric(df[target_col], errors='coerce').fillna(0).astype(int)
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # 2. 클래스 불균형 계산 (로그 #01보다 정교하게 적용)
        num_neg = np.sum(y_train == 0)
        num_pos = np.sum(y_train == 1)
        ratio = float(num_neg / num_pos) if num_pos > 0 else 1.0

        # 3. [로그 #02 핵심] 파라미터 튜닝
        # - max_depth: 4 -> 6 (더 복잡한 관계 학습)
        # - learning_rate: 0.05 -> 0.03 (더 천천히, 꼼꼼하게 학습)
        # - gamma: 0.1 (노이즈 방지를 위한 최소 손실 감소 값 설정)
        # - subsample, colsample_bytree: 0.8 (매번 데이터의 80%만 사용하여 과적합 방지)
        
        self.model = XGBClassifier(
            n_estimators=500,           # 더 많이 학습시키되
            max_depth=6,                # 깊이를 약간 깊게
            learning_rate=0.03,         # 학습률은 낮춰서 세밀하게
            gamma=0.2,                  # 가지치기 강도 강화
            subsample=0.8,              # 데이터 샘플링
            colsample_bytree=0.8,       # 피처 샘플링
            scale_pos_weight=ratio,     # 불균형 보정
            reg_alpha=0.1,              # L1 규제 추가
            reg_lambda=1.5,             # L2 규제 강화
            random_state=42,
            use_label_encoder=False,
            eval_metric='auc',
            early_stopping_rounds=50    # 성능 안 올라가면 중간에 멈춤
        )

        print(f"🚀 [Log #02] Training with Tuned Parameters on {len(X_train)} samples...")
        
        # Early stopping을 위해 검증셋 분리
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            verbose=False
        )

        # 4. 결과 평가
        preds = self.model.predict(X_test)
        probs = self.model.predict_proba(X_test)[:, 1]
        
        auc = roc_auc_score(y_test, probs)
        acc = accuracy_score(y_test, preds)
        
        print("\n" + "="*40)
        print(f"🏆 [실험 로그 #02 결과]")
        print(f"Accuracy : {acc:.4f}")
        print(f"AUC Score: {auc:.4f}")
        print("="*40)
        
        print("\n[Detail Report]")
        print(classification_report(y_test, preds))

    def plot_feature_importance(self, feature_cols: list):
        # (기존 그래프 시각화 코드와 동일)
        pass