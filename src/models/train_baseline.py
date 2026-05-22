import pandas as pd
import numpy as np
import os
import sys
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report

# 내부 모듈 참조를 위한 경로 설정
sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), '../..')
    )
)

from src.models.baseline_xgboost import BaselineXGBoost


def train_and_export_baseline():

    """
    튜닝된 XGBoost 모델 실험
    """

    data_path = 'data/parquet_datas/final_merged_commercial_data_v4.parquet'

    if not os.path.exists(data_path):

        print(
            f"Error: {data_path} 를 찾을 수 없습니다."
        )

        return

    # =========================================================
    # 1. 데이터 로드
    # =========================================================

    print("1. 데이터 로딩 및 피처 선택...")

    df = pd.read_parquet(data_path)

    df['기준_년분기_코드'] = pd.to_numeric(
        df['기준_년분기_코드'],
        errors='coerce'
    )

    target_col = '과포화_위험_여부'

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

        '총_아파트_세대수',
        '아파트_평균_시가',

        '총_직장_인구_수',
        '남성_직장_인구_수',
        '여성_직장_인구_수'
    ]

    # 실제 존재하는 컬럼만 사용
    feature_cols = [
        c for c in feature_cols
        if c in df.columns
    ]

    # =========================================================
    # 2. 시계열 분할
    # =========================================================

    train_df = df[
        df['기준_년분기_코드'] < 20241
    ].copy()

    test_df = df[
        df['기준_년분기_코드'] >= 20241
    ].copy()

    for col in feature_cols + [target_col]:

        train_df[col] = pd.to_numeric(
            train_df[col],
            errors='coerce'
        ).fillna(0)

        test_df[col] = pd.to_numeric(
            test_df[col],
            errors='coerce'
        ).fillna(0)

    X_train = train_df[feature_cols]
    y_train = train_df[target_col].astype(int)

    X_test = test_df[feature_cols]
    y_test = test_df[target_col].astype(int)

    # =========================================================
    # 3. 클래스 불균형 비율 계산
    # =========================================================

    ratio = (
        float(np.sum(y_train == 0))
        / np.sum(y_train == 1)
        if np.sum(y_train == 1) > 0
        else 1.0
    )

    # =========================================================
    # 4. 튜닝된 XGBoost 모델
    # =========================================================

    print(
        f"2. XGBoost 튜닝 모델 학습 시작 "
        f"(데이터 규모: {len(X_train)} 행)..."
    )

    model = XGBClassifier(

        # 부스팅 개수 증가
        n_estimators=500,

        # 과적합 방지 위해 깊이 약간 축소
        max_depth=4,

        # learning rate 감소
        learning_rate=0.03,

        # 샘플링 추가
        subsample=0.8,
        colsample_bytree=0.8,

        # leaf 최소 샘플 증가
        min_child_weight=5,

        # gamma 추가
        gamma=0.2,

        # 정규화 강화
        reg_alpha=1,
        reg_lambda=15,

        # 클래스 불균형 처리
        scale_pos_weight=ratio,

        # 기타
        random_state=42,
        eval_metric='auc',
        n_jobs=-1
    )

    # =========================================================
    # 5. 학습
    # =========================================================

    model.fit(
        X_train,
        y_train
    )

    # =========================================================
    # 6. 예측
    # =========================================================

    preds = model.predict(X_test)

    probs = model.predict_proba(X_test)[:, 1]

    # =========================================================
    # 7. 결과 출력
    # =========================================================

    print("\n" + "=" * 30)
    print(" [XGBoost Tuned Report] ")
    print("=" * 30)

    print(
        f"AUC Score: "
        f"{roc_auc_score(y_test, probs):.4f}"
    )

    print(
        f"Accuracy:  "
        f"{accuracy_score(y_test, preds):.4f}"
    )

    print("\n--- Classification Report ---")

    print(
        classification_report(
            y_test,
            preds
        )
    )

    # =========================================================
    # 8. 피처 중요도
    # =========================================================

    importance = model.feature_importances_

    feat_imp = pd.Series(
        importance,
        index=feature_cols
    ).sort_values(ascending=False)

    print("\n--- Top 10 Feature Importance ---")

    print(
        feat_imp.head(10)
    )

    return model


if __name__ == "__main__":

    train_and_export_baseline()