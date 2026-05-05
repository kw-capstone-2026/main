import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report, confusion_matrix

class BaselineXGBoost:
    """
    민재님의 상권 데이터와 지리 정보를 바탕으로 
    폐업 여부를 예측하는 최적화된 XGBoost 모델 클래스
    """
    def __init__(self, model_type: str = 'classification'):
        self.model_type = model_type
        self.model = None

    def train_and_evaluate(self, df: pd.DataFrame, target_col: str, feature_cols: list):
        """
        모델 학습 및 상세 성능 리포트 출력
        """
        # 1. 학습 데이터 준비
        # 모든 피처를 수치형으로 변환하고 결측치는 0으로 채움
        X = df[feature_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
        y = df[target_col].astype(int)

        # 2. 데이터 분할 (8:2 비율, 층화 추출 적용)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # 3. 데이터 불균형(영업 vs 폐업) 보정 가중치 계산
        num_neg = np.sum(y_train == 0)
        num_pos = np.sum(y_train == 1)
        ratio = float(num_neg) / num_pos if num_pos > 0 else 1.0

        # 4. XGBoost 모델 설정 (실험 로그 #02 최적화 파라미터 적용)
        self.model = XGBClassifier(
            n_estimators=500,           # 반복 횟수
            max_depth=6,                # 트리 깊이
            learning_rate=0.03,         # 학습률
            gamma=0.2,                  # 분할 결정 가중치
            subsample=0.8,              # 데이터 샘플링 비율
            colsample_bytree=0.8,       # 피처 샘플링 비율
            scale_pos_weight=ratio,     # 불균형 데이터 가중치
            reg_alpha=0.1,              # L1 규제
            reg_lambda=1.5,             # L2 규제
            random_state=42,
            eval_metric='auc',
            early_stopping_rounds=50    # AUC 개선 없을 시 조기 종료
        )

        # 5. 모델 학습 시작
        print(f"\n🔥 [실험 #04] XGBoost 학습 시작 (피처 수: {len(feature_cols)})")
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            verbose=False
        )

        # 6. 예측 및 결과 도출
        preds = self.model.predict(X_test)
        probs = self.model.predict_proba(X_test)[:, 1]

        # 7. 성능 리포트 출력
        print("\n" + "="*50)
        print("🏆 [실험 로그 #04 최종 결과]")
        print("-" * 50)
        print(f"✅ Accuracy : {accuracy_score(y_test, preds):.4f}")
        print(f"🔥 AUC Score: {roc_auc_score(y_test, probs):.4f}")
        print("="*50)

        # 상세 분류 성능 (Precision, Recall 등)
        print("\n[상세 분류 지표 (Classification Report)]")
        print(classification_report(y_test, preds))

        # 8. 변수 중요도(Feature Importance) 분석
        importances = self.model.feature_importances_
        indices = np.argsort(importances)[::-1]
        
        print("\n📊 [변수 중요도 순위 (Feature Importance TOP 10)]")
        print("-" * 50)
        for i in range(min(10, len(feature_cols))):
            f_name = feature_cols[indices[i]]
            f_val = importances[indices[i]]
            print(f"{i+1:2d}. {f_name:<22} : {f_val:.4f}")
        print("-" * 50)

        return self.model