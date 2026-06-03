import pandas as pd
import numpy as np
import os
import sys
import io
import matplotlib.pyplot as plt
from xgboost import XGBClassifier
import shap

# Windows 콘솔 인코딩 에러 방지 및 폰트 설정
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8')

# SHAP format_value 몽키 패치: 마이너스 기호 깨짐(Glyph 8722 사각형 박스) 방지
try:
    import shap.plots._labels as labels
    import shap.plots._waterfall as wf
    import re
    from typing import Any
    
    def custom_format_value(s: Any, format_str: str) -> str:
        if not issubclass(type(s), str):
            s = format_str % s
        s = re.sub(r"\.?0+$", "", s)
        if len(s) > 0 and s[0] == "-":
            s = "-" + s[1:]
        return s
        
    labels.format_value = custom_format_value
    wf.format_value = custom_format_value
    print("[SHAP Patch] Unicode minus sign patch applied successfully.")
except Exception as e:
    print(f"[SHAP Patch Warning] {e}")

# Windows 한글 폰트 설정 (SHAP 플롯 출력 시 깨짐 방지)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def run_shap_explanation():
    data_path = 'data/parquet_datas/final_merged_commercial_data_v5.parquet'
    img_dir = 'docs/0603_report/image'
    os.makedirs(img_dir, exist_ok=True)
    
    print("[SHAP] 데이터 로드 및 모델 학습...")
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
    
    # 시계열 분할
    train_df = df[df['기준_년분기_코드'] < 20241].copy()
    test_df = df[df['기준_년분기_코드'] >= 20241].copy()
    
    for col in feature_cols + [target_col]:
        train_df[col] = pd.to_numeric(train_df[col], errors='coerce').fillna(0)
        test_df[col] = pd.to_numeric(test_df[col], errors='coerce').fillna(0)

    X_train = train_df[feature_cols]
    y_train = train_df[target_col].astype(int)
    X_test = test_df[feature_cols]
    y_test = test_df[target_col].astype(int)

    ratio = float(np.sum(y_train == 0)) / np.sum(y_train == 1) if np.sum(y_train == 1) > 0 else 1.0

    print("[SHAP] XGBoost 모델 학습 시작...")
    model = XGBClassifier(
        n_estimators=400, max_depth=4, learning_rate=0.03,
        subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
        gamma=0.2, reg_alpha=1, reg_lambda=15,
        scale_pos_weight=ratio, random_state=42, eval_metric='auc', n_jobs=-1
    )
    model.fit(X_train, y_train)
    print("[SHAP] 모델 학습 완료. Explainer 구축 중...")

    sample_size = min(500, len(X_test))
    np.random.seed(42)
    sample_indices = np.random.choice(X_test.index, size=sample_size, replace=False)
    X_sample = X_test.loc[sample_indices]
    y_sample = y_test.loc[sample_indices]

    explainer = shap.TreeExplainer(model)
    shap_values = explainer(X_sample)

    print("[SHAP] Global Summary Plot 생성 중...")
    plt.figure(figsize=(12, 8))
    shap.summary_plot(shap_values, X_sample, show=False)
    plt.title("서울시 상권 과포화/폐업 예측 모델 SHAP 글로벌 특징 기여도", fontsize=14, pad=15)
    plt.tight_layout()
    summary_path = os.path.join(img_dir, 'shap_summary_plot.png')
    plt.savefig(summary_path, dpi=300)
    plt.close()
    print(f"[SHAP] 글로벌 요약 중요도 플롯이 '{summary_path}' 에 성공적으로 저장되었습니다.")

    print("[SHAP] 로컬 점포별 시뮬레이션Waterfall Plot 생성 중...")
    
    probs_sample = model.predict_proba(X_sample)[:, 1]
    sample_analysis = X_sample.copy()
    sample_analysis['actual'] = y_sample
    sample_analysis['predicted_prob'] = probs_sample
    
    danger_candidates = sample_analysis[(sample_analysis['actual'] == 1) & (sample_analysis['predicted_prob'] > 0.4)]
    normal_candidates = sample_analysis[(sample_analysis['actual'] == 0) & (sample_analysis['predicted_prob'] < 0.2)]
    
    if danger_candidates.empty and not sample_analysis[sample_analysis['actual'] == 1].empty:
        danger_candidates = sample_analysis[sample_analysis['actual'] == 1].sort_values(by='predicted_prob', ascending=False).head(1)
    if normal_candidates.empty and not sample_analysis[sample_analysis['actual'] == 0].empty:
        normal_candidates = sample_analysis[sample_analysis['actual'] == 0].sort_values(by='predicted_prob', ascending=True).head(1)
        
    if not danger_candidates.empty:
        idx = danger_candidates.index[0]
        sample_loc_list = np.where(X_sample.index == idx)[0]
        if len(sample_loc_list) > 0:
            sample_loc = sample_loc_list[0]
            plt.figure(figsize=(10, 6))
            shap.plots.waterfall(shap_values[sample_loc], show=False)
            plt.title(f"고위험 상권 점포의 폐업 요인 기여도 시뮬레이션 (위험지수: {danger_candidates.loc[idx, 'predicted_prob']:.2%})", fontsize=12, pad=15)
            plt.tight_layout()
            danger_path = os.path.join(img_dir, 'shap_local_danger.png')
            plt.savefig(danger_path, dpi=300)
            plt.close()
            print(f"[SHAP] 고위험 점포의 SHAP Waterfall 플롯이 '{danger_path}' 에 저장되었습니다.")
            
    if not normal_candidates.empty:
        idx = normal_candidates.index[0]
        sample_loc_list = np.where(X_sample.index == idx)[0]
        if len(sample_loc_list) > 0:
            sample_loc = sample_loc_list[0]
            plt.figure(figsize=(10, 6))
            shap.plots.waterfall(shap_values[sample_loc], show=False)
            plt.title(f"안전 상권 점포의 요인 기여도 시뮬레이션 (위험지수: {normal_candidates.loc[idx, 'predicted_prob']:.2%})", fontsize=12, pad=15)
            plt.tight_layout()
            normal_path = os.path.join(img_dir, 'shap_local_normal.png')
            plt.savefig(normal_path, dpi=300)
            plt.close()
            print(f"[SHAP] 안전 상권 점포의 SHAP Waterfall 플롯이 '{normal_path}' 에 저장되었습니다.")

    print("[Success] SHAP XAI 해석 시뮬레이션 과정이 완료되었습니다.")

if __name__ == "__main__":
    run_shap_explanation()
