"""
models/survival_model.py
-------------------------
담당: 팀원 D (모델링 파트)

목적: XGBoost AFT(Accelerated Failure Time) 모델을 학습하여
      특정 입지/업종의 생존 기간(폐업까지 버티는 시간)을 예측합니다.

타겟 변수:
    - duration   : 생존 기간 (개업일 ~ 폐업일 기간, 월 단위)
    - event      : 관측 여부 (1 = 폐업 확인, 0 = 아직 운영 중 = 중도절단)

참고: AFT 모델은 생존 시간을 직접 예측하는 방식으로 해석이 용이합니다.
"""

import xgboost as xgb
import pandas as pd
import shap


def train_aft_model(X_train: pd.DataFrame, y_lower: pd.Series, y_upper: pd.Series) -> xgb.Booster:
    """
    XGBoost AFT 모델을 학습합니다.

    Args:
        X_train   : 피처 행렬
        y_lower   : 생존 기간 하한 (폐업 시 duration, 운영 중 시 duration)
        y_upper   : 생존 기간 상한 (폐업 시 duration, 운영 중 시 +inf)

    Returns:
        학습된 xgb.Booster 모델
    """
    # TODO: dtrain 구성 및 XGBoost AFT 파라미터 설정 후 학습
    raise NotImplementedError("train_aft_model() 구현 필요")


def explain_with_shap(model: xgb.Booster, X: pd.DataFrame):
    """SHAP을 이용하여 각 변수의 생존 기간 기여도를 시각화합니다."""
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)
    shap.summary_plot(shap_values, X)
