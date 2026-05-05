import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report, confusion_matrix

class BaselineXGBoost:
    def __init__(self):
        self.model = None

    def train_and_evaluate(self, df: pd.DataFrame, target_col: str, feature_cols: list):
        # 데이터 준비
        X = df[feature_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
        y = df[target_col].astype(int)

        # 학습/테스트 데이터 분리 (8:2)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # 클래스 불균형 처리 (영업 vs 폐업 비율 계산)
        num_neg = np.sum(y_train == 0)
        num_pos = np.sum(y_train == 1)
        ratio = float(num_neg) / num_pos if num_pos > 0 else 1.0

        # 모델 설정 및 학습
        self.model = XGBClassifier(
            n_estimators=500,
            max_depth=6,
            learning_rate=0.03,
            scale_pos_weight=ratio,
            random_state=42,
            eval_metric='auc',
            early_stopping_rounds=50
        )

        self.model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

        # 예측 결과 산출
        y_pred = self.model.predict(X_test)
        probs = self.model.predict_proba(X_test)[:, 1]

        # 결과 출력
        print("\n" + "="*60)
        print("🏆 [실험 #05 모델 평가 결과]")
        print("-"*60)
        print(f"✅ Accuracy (정확도) : {accuracy_score(y_test, y_pred):.4f}")
        print(f"🔥 AUC Score         : {roc_auc_score(y_test, probs):.4f}")
        print("="*60)

        # 상세 지표 출력
        print("\n📊 [상세 분류 리포트]")
        print(classification_report(y_test, y_pred, target_names=['영업(0)', '폐업(1)']))

        # 변수 중요도 출력
        importances = pd.Series(self.model.feature_importances_, index=feature_cols).sort_values(ascending=False)
        print("\n📈 [변수 중요도 TOP 10]")
        print(importances.head(10))
        print("-"*60)

        return self.model