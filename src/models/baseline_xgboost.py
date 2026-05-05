import pandas as pd
import numpy as np
from xgboost import XGBClassifier, XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_squared_error, classification_report, roc_auc_score

class BaselineXGBoost:
    """
    XGBoost 베이스라인 모델 클래스 (Log #03 최적화 버전)
    분류(폐업 여부) 또는 회귀(생존 기간) 모델을 지원합니다.
    """

    def __init__(self, model_type: str = 'classification'):
        """
        :param model_type: 'classification' (폐업 여부 분류) 또는 'regression' (생존 기간 회귀)
        """
        self.model_type = model_type
        self.model = None

    def train_and_evaluate(self, df: pd.DataFrame, target_col: str, feature_cols: list):
        """
        모델을 학습하고 성능을 평가합니다. (Log #02 튜닝 파라미터 적용)
        """
        df_clean = df.copy()
        for col in feature_cols:
            if col in df_clean.columns:
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)
        
        # 타겟 컬럼 처리
        if target_col in df_clean.columns:
            df_clean[target_col] = pd.to_numeric(df_clean[target_col], errors='coerce').fillna(0)
            y = df_clean[target_col].astype(int)
        else:
            raise ValueError(f"Target column '{target_col}' missing.")
            
        X = df_clean[feature_cols]
        
        # 학습/테스트 데이터 분리 (불균형 보존을 위해 stratify 권장되나 기존 로직 유지)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        if self.model_type == 'classification':
            # 클래스 불균형 비율 계산
            ratio = float(np.sum(y_train == 0)) / np.sum(y_train == 1) if np.sum(y_train == 1) > 0 else 1.0
            
            # [Log #02 & #03 핵심] 튜닝된 하이퍼파라미터 적용
            self.model = XGBClassifier(
                n_estimators=500,           # 학습 횟수 증가
                max_depth=6,                # 깊이 최적화
                learning_rate=0.03,         # 세밀한 학습
                gamma=0.2,                  # 가지치기 강도
                subsample=0.8,              # 데이터 샘플링
                colsample_bytree=0.8,       # 피처 샘플링
                scale_pos_weight=ratio,     # 불균형 보정
                reg_alpha=0.1,              # L1 규제
                reg_lambda=1.5,             # L2 규제 (기존 5에서 로그#02 기준으로 조정)
                random_state=42,
                use_label_encoder=False,
                eval_metric='auc',
                early_stopping_rounds=50    # 조기 종료 설정
            )
            
            print(f"🚀 [Log #03] Training Tuned XGBoost on {len(X_train)} samples...")
            # Early Stopping을 위해 eval_set 추가
            self.model.fit(
                X_train, y_train, 
                eval_set=[(X_test, y_test)], 
                verbose=False
            )
            
        elif self.model_type == 'regression':
            self.model = XGBRegressor(
                n_estimators=200,
                max_depth=4,
                learning_rate=0.05,
                reg_lambda=10,
                random_state=42
            )
            print(f"Training XGBoost Regressor on {len(X_train)} samples...")
            self.model.fit(X_train, y_train)
        
        # --- 예측 및 결과 출력 ---
        preds = self.model.predict(X_test)
        
        print("\n--- Prediction Samples (Actual vs Predicted) ---")
        comparison = pd.DataFrame({'Actual': y_test, 'Predicted': preds}).head(10)
        print(comparison)
        
        print("\n" + "="*50)
        print(f"🏆 [실험 로그 #03 결과 리포트]")
        
        if self.model_type == 'classification':
            acc = accuracy_score(y_test, preds)
            probs = self.model.predict_proba(X_test)[:, 1]
            auc = roc_auc_score(y_test, probs)
            print(f"✅ Accuracy : {acc:.4f}")
            print(f"🔥 AUC Score: {auc:.4f}")
            print("="*50)
            print("\n[상세 리포트 (Detail Report)]")
            print(classification_report(y_test, preds))
        else:
            rmse = np.sqrt(mean_squared_error(y_test, preds))
            print(f"RMSE: {rmse:.4f}")
            print("="*50)
            
        # 변수 중요도 출력 (그래프 대신 텍스트)
        self.print_feature_importance(feature_cols)

    def print_feature_importance(self, feature_cols: list):
        """
        모델의 변수 중요도를 텍스트로 출력합니다. (시각화 라이브러리 미사용)
        """
        importance = self.model.feature_importances_
        indices = np.argsort(importance)[::-1]
        
        print("\n📊 [변수 중요도 (Feature Importance) TOP 10]")
        print("-" * 45)
        for f in range(min(len(feature_cols), 10)):
            feature_name = feature_cols[indices[f]]
            importance_val = importance[indices[f]]
            print(f"{f+1:2d}. {feature_name:<20} : {importance_val:.4f}")
        print("-" * 45)