import pandas as pd
import numpy as np
import os
import sys
import io
import json
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

# Windows 콘솔 인코딩 에러 방지
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8')

def train_and_save():
    data_path = 'data/parquet_datas/final_merged_commercial_data_v5.parquet'
    output_dir = 'ml-server'
    os.makedirs(output_dir, exist_ok=True)
    
    print("[Info] 데이터 로드 중...")
    if not os.path.exists(data_path):
        print(f"[Error] {data_path} 를 찾을 수 없습니다.")
        return

    df = pd.read_parquet(data_path)
    df['기준_년분기_코드'] = pd.to_numeric(df['기준_년분기_코드'], errors='coerce')
    
    target_col = '과포화_위험_여부'
    
    feature_cols = [
        '당월_매출_금액', '당월_매출_건수',
        '점포_수_y', '유사_업종_점포_수_y',
        '개업_율_y', '폐업_률_y',
        '프랜차이즈_점포_수_y', '프랜차이즈점포비율(%)', '개인점포비율(%)',
        '상권_전체점포_수', '상권 내부 업종 점유율(%)',
        '운영_영업_개월_평균', '폐업_영업_개월_평균',
        '유효_수요_전환율', '점포당_평균_매출',
        '전년_동기_대비_폐업_증감률',
        
        # 외부 API 기반 파생 변수들
        '소득_구간_코드', '상권_업종_적합도',
        '총_아파트_세대수', '아파트_평균_시가',
        '총_직장_인구_수', '남성_직장_인구_수', '여성_직장_인구_수',
        
        # Density 기반 변수들
        '직장인구_100명당_점포수', '아파트_100세대당_점포수', '유사업종_점포비율',
        '직장인구_100명당_유사업종수', '점포당_매출_밀도', '직장인구_1인당_매출', '아파트세대당_매출',
        
        # 집객시설 관련 변수들
        '집객시설_수', '집객시설_밀도'
    ]

    feature_cols = [c for c in feature_cols if c in df.columns]
    
    # 시계열 분할 (Train: 2019 ~ 2023)
    train_df = df[df['기준_년분기_코드'] < 20241].copy()
    
    for col in feature_cols + [target_col]:
        train_df[col] = pd.to_numeric(train_df[col], errors='coerce').fillna(0)

    X_train = train_df[feature_cols]
    y_train = train_df[target_col].astype(int)

    # 불균형 가중치
    ratio = float(np.sum(y_train == 0)) / np.sum(y_train == 1) if np.sum(y_train == 1) > 0 else 1.0
    print(f"[Info] 클래스 불균형 비율: {ratio:.4f}")
    
    # 1. XGBoost 학습 및 저장
    print("[Model] XGBoost 학습 중...")
    xgb = XGBClassifier(
        n_estimators=400, max_depth=4, learning_rate=0.03,
        subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
        gamma=0.2, reg_alpha=1, reg_lambda=15,
        scale_pos_weight=ratio, random_state=42, eval_metric='auc', n_jobs=-1
    )
    xgb.fit(X_train, y_train)
    
    xgb_path = os.path.join(output_dir, 'xgb_model.json')
    xgb.save_model(xgb_path)
    print(f"[Success] XGBoost 모델 저장 완료: '{xgb_path}'")
    
    # 2. LightGBM 학습 및 저장
    print("[Model] LightGBM 학습 중...")
    lgb = LGBMClassifier(
        n_estimators=400, max_depth=4, learning_rate=0.03,
        subsample=0.8, colsample_bytree=0.8, min_child_samples=20,
        reg_alpha=1, reg_lambda=15,
        scale_pos_weight=ratio, random_state=42, n_jobs=-1, verbose=-1
    )
    lgb.fit(X_train, y_train)
    
    lgb_path = os.path.join(output_dir, 'lgb_model.txt')
    lgb.booster_.save_model(lgb_path)
    print(f"[Success] LightGBM 모델 저장 완료: '{lgb_path}'")
    
    # 3. 피처명 리스트 저장 (모델 호출 시 순서 유지를 위함)
    features_path = os.path.join(output_dir, 'feature_cols.json')
    with open(features_path, 'w', encoding='utf-8') as f:
        json.dump(feature_cols, f, ensure_ascii=False, indent=2)
    print(f"[Success] 피처 목록 저장 완료: '{features_path}'")

if __name__ == "__main__":
    train_and_save()
