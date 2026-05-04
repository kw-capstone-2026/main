import pandas as pd
import numpy as np
from xgboost import XGBClassifier, XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_squared_error, classification_report
import matplotlib.pyplot as plt

class BaselineXGBoost:
    """
    XGBoost 베이스라인 모델 클래스
    분류(폐업 여부) 또는 회귀(생존 기간) 모델을 지원합니다.
    """

    def __init__(self, model_type: str = 'classification'):
        """
        :param model_type: 'classification' (폐업 여부 분류) 또는 'regression' (생존 기간 회귀)
        """
        self.model_type = model_type
        
        if self.model_type == 'classification':
            self.model = XGBClassifier(
                n_estimators=100, 
                learning_rate=0.1, 
                max_depth=5, 
                random_state=42, 
                use_label_encoder=False, 
                eval_metric='logloss'
            )
        elif self.model_type == 'regression':
            self.model = XGBRegressor(
                n_estimators=100, 
                learning_rate=0.1, 
                max_depth=5, 
                random_state=42
            )
        else:
            raise ValueError("model_type must be 'classification' or 'regression'")

    def train_and_evaluate(self, df: pd.DataFrame, target_col: str, feature_cols: list):
        """
        모델을 학습하고 성능을 평가합니다. (클래스 불균형 자동 보정 및 점포 단위 분류 최적화)
        """
        df_clean = df.copy()
        for col in feature_cols:
            if col in df_clean.columns:
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)
        
        # 타겟 컬럼은 결측치를 0으로 강제 치환 후 정수로 변환
        if target_col in df_clean.columns:
            df_clean[target_col] = pd.to_numeric(df_clean[target_col], errors='coerce').fillna(0)
            y = df_clean[target_col].astype(int)
        else:
            raise ValueError(f"Target column '{target_col}' missing.")
            
        X = df_clean[feature_cols]
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # 모델 규제 및 불균형 보정
        if self.model_type == 'classification':
            from sklearn.metrics import roc_auc_score
            ratio = float(np.sum(y_train == 0)) / np.sum(y_train == 1) if np.sum(y_train == 1) > 0 else 1.0
            self.model = XGBClassifier(
                n_estimators=100,
                max_depth=4,
                learning_rate=0.05,
                reg_lambda=5,
                scale_pos_weight=ratio,
                random_state=42,
                use_label_encoder=False,
                eval_metric='auc'
            )
        elif self.model_type == 'regression':
            self.model = XGBRegressor(
                n_estimators=50,
                max_depth=3,
                learning_rate=0.05,
                reg_lambda=10,
                random_state=42
            )
        
        print(f"Training XGBoost ({self.model_type}) on {len(X_train)} samples...")
        self.model.fit(X_train, y_train)
        
        preds = self.model.predict(X_test)
        
        print("\n--- Prediction Samples (Actual vs Predicted) ---")
        comparison = pd.DataFrame({'Actual': y_test, 'Predicted': preds}).head(10)
        print(comparison)
        
        print("\n--- Evaluation Results ---")
        if self.model_type == 'classification':
            acc = accuracy_score(y_test, preds)
            probs = self.model.predict_proba(X_test)[:, 1]
            auc = roc_auc_score(y_test, probs)
            print(f"Accuracy: {acc:.4f}")
            print(f"AUC Score: {auc:.4f}")
        else:
            rmse = np.sqrt(mean_squared_error(y_test, preds))
            print(f"RMSE: {rmse:.4f}")
            
        self.plot_feature_importance(feature_cols)

    def plot_feature_importance(self, feature_cols: list):
        """
        모델의 변수 중요도를 시각화합니다.
        
        :param feature_cols: 독립 변수 리스트
        """
        importance = self.model.feature_importances_
        # Feature Importance 정렬
        sorted_idx = np.argsort(importance)
        
        plt.figure(figsize=(10, 6))
        plt.barh(range(len(sorted_idx)), importance[sorted_idx], align='center')
        plt.yticks(range(len(sorted_idx)), [feature_cols[i] for i in sorted_idx])
        plt.title(f'XGBoost ({self.model_type}) - Feature Importance')
        plt.xlabel('Importance Score')
        plt.tight_layout()
        
        # 실제 환경에서는 plt.show() 하거나 이미지로 저장
        # plt.savefig('feature_importance.png')
        print("\nFeature importance plot is ready.")

# 사용 예시 (스크립트 직접 실행 시)
if __name__ == '__main__':
    # 테스트용 더미 데이터 생성
    dummy_data = pd.DataFrame({
        'BAS_ID': [1, 2, 3, 4, 5],
        'competitor_cnt': [10, 20, 5, 50, 15],
        'total_sales': [1000, 2000, 500, 5000, 1500],
        'floating_pop': [500, 800, 300, 2000, 700],
        'is_closed': [0, 1, 0, 1, 0],
        'survival_months': [36, 12, 48, 6, 24]
    })
    
    features = ['competitor_cnt', 'total_sales', 'floating_pop']
    
    # 1. 분류 모델 테스트 (폐업 여부)
    clf_model = BaselineXGBoost(model_type='classification')
    clf_model.train_and_evaluate(dummy_data, target_col='is_closed', feature_cols=features)
    
    # 2. 회귀 모델 테스트 (생존 기간)
    reg_model = BaselineXGBoost(model_type='regression')
    reg_model.train_and_evaluate(dummy_data, target_col='survival_months', feature_cols=features)
