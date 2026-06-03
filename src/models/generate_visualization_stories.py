import pandas as pd
import numpy as np
import os
import sys
import io
import matplotlib.pyplot as plt
import seaborn as sns
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
import shap

# Windows 콘솔 인코딩 에러 방지 및 한글 폰트 설정
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8')

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def generate_stories():
    data_path = 'data/parquet_datas/final_merged_commercial_data_v5.parquet'
    img_dir = 'docs/0603_report/image'
    os.makedirs(img_dir, exist_ok=True)
    
    print("[Vis] 데이터 로드 중...")
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
    
    # ----------------------------------------------------
    # 📈 Story 1: 절대규모 지표 vs 상대적 밀도(Density) 변수 비교
    # ----------------------------------------------------
    print("[Vis] Plot 1: 절대규모 vs 밀도 피처 비교 생성 중...")
    sample_df = df.sample(n=3000, random_state=42).copy()
    sample_df[target_col] = pd.to_numeric(sample_df[target_col], errors='coerce').fillna(0).astype(int)
    
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    
    # Left: Absolute variables
    # x = 유사_업종_점포_수_y (경쟁업체수), y = 당월_매출_금액 (총매출)
    sample_df['유사_업종_점포_수_y'] = pd.to_numeric(sample_df['유사_업종_점포_수_y'], errors='coerce').fillna(0)
    sample_df['당월_매출_금액'] = pd.to_numeric(sample_df['당월_매출_금액'], errors='coerce').fillna(0) / 1e8  # 억 단위
    
    sns.scatterplot(
        data=sample_df, x='유사_업종_점포_수_y', y='당월_매출_금액', 
        hue=target_col, palette={0: '#3B82F6', 1: '#EF4444'}, alpha=0.7, ax=axes[0], s=30
    )
    axes[0].set_title("① 절대규모 지표 (총 매출액 vs 유사 업종 수)", fontsize=12, pad=10)
    axes[0].set_xlabel("유사 업종 점포 수 (개)", fontsize=10)
    axes[0].set_ylabel("당월 매출 금액 (억 원)", fontsize=10)
    axes[0].legend(title="과포화/폐업", labels=["안전 (0)", "위험/폐업 (1)"])
    
    # Right: Density variables
    # x = 유사업종_점포비율, y = 점포당_매출_밀도
    sample_df['유사업종_점포비율'] = pd.to_numeric(sample_df['유사업종_점포비율'], errors='coerce').fillna(0) * 100 # % 단위
    sample_df['점포당_매출_밀도'] = pd.to_numeric(sample_df['점포당_매출_밀도'], errors='coerce').fillna(0) / 1e6 # 백만 단위
    
    sns.scatterplot(
        data=sample_df, x='유사업종_점포비율', y='점포당_매출_밀도', 
        hue=target_col, palette={0: '#3B82F6', 1: '#EF4444'}, alpha=0.7, ax=axes[1], s=30
    )
    axes[1].set_title("② 밀도(Density) 지표 (점포당 매출 밀도 vs 유사업종 점포비율)", fontsize=12, pad=10)
    axes[1].set_xlabel("상권 내 유사업종 점포 비율 (%)", fontsize=10)
    axes[1].set_ylabel("점포당 매출 밀도 (백만 원)", fontsize=10)
    axes[1].legend(title="과포화/폐업", labels=["안전 (0)", "위험/폐업 (1)"])
    
    plt.suptitle("피처 디자인 혁신: 절대규모 변수의 편향 한계 극복 및 밀도 변수의 리스크 변별력 증명", fontsize=14, y=0.98, weight='bold')
    plt.tight_layout()
    plot1_path = os.path.join(img_dir, 'story1_density_comparison.png')
    plt.savefig(plot1_path, dpi=300)
    plt.close()
    print(f"[Vis] Plot 1 저장 완료: '{plot1_path}'")

    # ----------------------------------------------------
    # 📉 Story 2: 거시경제 외란과 시계열적 폐업률 변화 추이
    # ----------------------------------------------------
    print("[Vis] Plot 2: 시계열 수명 및 폐업률 추이 생성 중...")
    # 분기별 평균 계산
    time_df = df.groupby('기준_년분기_코드').agg({
        '폐업_영업_개월_평균': 'mean',
        '폐업_률_y': 'mean'
    }).reset_index()
    
    # 분기 코드를 보기 좋게 매핑 (예: 20191 -> '19.Q1)
    def map_quarter(q):
        q_str = str(int(q))
        year = q_str[:4][2:]
        quarter = q_str[4]
        return f"'{year}.Q{quarter}"
    
    time_df['quarter_label'] = time_df['기준_년분기_코드'].apply(map_quarter)
    time_df = time_df.sort_values(by='기준_년분기_코드')
    
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    # Left Axis: 폐업_영업_개월_평균 (수명)
    color = '#1D4ED8'
    ax1.set_xlabel('기준 년분기', fontsize=11, labelpad=10)
    ax1.set_ylabel('평균 폐업 영업 개월수 (생존 수명)', color=color, fontsize=11)
    line1 = ax1.plot(time_df['quarter_label'], time_df['폐업_영업_개월_평균'], color=color, marker='o', linewidth=2.5, label='평균 폐업 영업 개월수')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True, linestyle='--', alpha=0.5)
    plt.xticks(rotation=45, fontsize=9)
    
    # Right Axis: 폐업_률_y
    ax2 = ax1.twinx()
    color = '#DC2626'
    ax2.set_ylabel('상권 평균 폐업률 (%)', color=color, fontsize=11)
    line2 = ax2.plot(time_df['quarter_label'], time_df['폐업_률_y'], color=color, marker='s', linewidth=2, linestyle='--', label='상권 평균 폐업률')
    ax2.tick_params(axis='y', labelcolor=color)
    
    # 범례 합치기
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper left')
    
    plt.title("거시경제 충격에 따른 상권 생태계 수명(지속기간)의 급격한 단축 및 폐업률 시계열 추이", fontsize=13, weight='bold', pad=15)
    plt.tight_layout()
    plot2_path = os.path.join(img_dir, 'story2_time_series_drift.png')
    plt.savefig(plot2_path, dpi=300)
    plt.close()
    print(f"[Vis] Plot 2 저장 완료: '{plot2_path}'")

    # ----------------------------------------------------
    # 📊 Story 3: 비선형적 피처 인터랙션 (SHAP Dependence Plot)
    # ----------------------------------------------------
    print("[Vis] Plot 3: SHAP 의존성 인터랙션 플롯 생성 중...")
    # 학습에 필요한 시계열 분할
    train_df = df[df['기준_년분기_코드'] < 20241].copy()
    test_df = df[df['기준_년분기_코드'] >= 20241].copy()
    
    for col in feature_cols + [target_col]:
        train_df[col] = pd.to_numeric(train_df[col], errors='coerce').fillna(0)
        test_df[col] = pd.to_numeric(test_df[col], errors='coerce').fillna(0)

    X_train = train_df[feature_cols]
    y_train = train_df[target_col].astype(int)
    X_test = test_df[feature_cols]

    ratio = float(np.sum(y_train == 0)) / np.sum(y_train == 1) if np.sum(y_train == 1) > 0 else 1.0

    model = XGBClassifier(
        n_estimators=100, max_depth=4, learning_rate=0.1,
        scale_pos_weight=ratio, random_state=42, n_jobs=-1
    )
    model.fit(X_train, y_train)

    # 500개 테스트 샘플
    sample_size = min(500, len(X_test))
    np.random.seed(42)
    sample_indices = np.random.choice(X_test.index, size=sample_size, replace=False)
    X_sample = X_test.loc[sample_indices]

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_sample)

    # 점포당_평균_매출 피처 인덱스 및 인터랙션 변수 찾기
    feat_x = '점포당_평균_매출'
    feat_color = '점포당_매출_밀도'
    
    idx_x = feature_cols.index(feat_x)
    idx_color = feature_cols.index(feat_color)
    
    val_x = X_sample[feat_x].values / 1e6  # 백만 단위
    val_shap = shap_values[:, idx_x]
    val_color = X_sample[feat_color].values / 1e6  # 백만 단위

    # SHAP 폰트 마이너스 부호 패치를 적용한 산점도 그리기
    plt.figure(figsize=(10, 6))
    sc = plt.scatter(val_x, val_shap, c=val_color, cmap='coolwarm', s=35, alpha=0.8, edgecolor='none')
    cb = plt.colorbar(sc)
    cb.set_label('점포당 매출 밀도 (백만 원)', fontsize=10)
    
    plt.axhline(0, color='gray', linestyle='--', linewidth=0.8)
    plt.title(f"비선형 요인 분석: 점포당 평균 매출에 따른 폐업 기여도와 매출 밀도의 상호작용 (SHAP Dependence)", fontsize=12, pad=15, weight='bold')
    plt.xlabel('점포당 평균 매출 (백만 원)', fontsize=10)
    plt.ylabel(f'{feat_x}의 SHAP 기여도 (위험 증가도)', fontsize=10)
    
    # Tipping Point 주석 추가
    plt.annotate(
        '위험 임계점 (Tipping Point)\n월 매출 약 15~20M 이하에서\n위험 기여도 폭발적 증가',
        xy=(15, 0.5), xytext=(35, 1.5),
        arrowprops=dict(facecolor='black', shrink=0.08, width=1, headwidth=6),
        fontsize=9, color='#DC2626', bbox=dict(boxstyle="round,pad=0.3", fc="#FEF2F2", ec="#FCA5A5", lw=1)
    )

    plt.tight_layout()
    plot3_path = os.path.join(img_dir, 'story3_shap_dependence.png')
    plt.savefig(plot3_path, dpi=300)
    plt.close()
    print(f"[Vis] Plot 3 저장 완료: '{plot3_path}'")

    # ----------------------------------------------------
    # 🗺️ Story 4: 공간적 예측 위험도 핫스팟 분포 지도 (Spatial Risk Map)
    # ----------------------------------------------------
    print("[Vis] Plot 4: 공간 예측 리스크 맵 생성 중...")
    # 2024년 테스트셋에서 4000개 샘플링
    spatial_df = test_df.sample(n=4000, random_state=42).copy()
    X_sp = spatial_df[feature_cols]
    
    lgb = LGBMClassifier(
        n_estimators=100, max_depth=4, learning_rate=0.1,
        scale_pos_weight=ratio, random_state=42, n_jobs=-1, verbose=-1
    )
    lgb.fit(X_train, y_train)
    
    prob_xgb = model.predict_proba(X_sp)[:, 1]
    prob_lgb = lgb.predict_proba(X_sp)[:, 1]
    prob_ensemble = 0.3 * prob_xgb + 0.7 * prob_lgb
    
    # Log-odds 스케일링으로 위험 점수 산정
    epsilon = 1e-5
    prob_ensemble_clipped = np.clip(prob_ensemble, epsilon, 1 - epsilon)
    log_odds = np.log(prob_ensemble_clipped / (1 - prob_ensemble_clipped))
    scores = 50 + 15 * log_odds
    scores = np.clip(scores, 0, 100)
    
    spatial_df['risk_score'] = scores
    
    # 서울시 범위에 맞춤 (필터링)
    # 서울 중심좌표: 37.5665, 126.9780
    spatial_df = spatial_df[
        (spatial_df['lat'] > 37.40) & (spatial_df['lat'] < 37.70) &
        (spatial_df['lon'] > 126.75) & (spatial_df['lon'] < 127.25)
    ]

    plt.figure(figsize=(10, 8))
    # RdYlBu_r (적색=고위험, 황색=경계, 청색=안전)
    sc = plt.scatter(
        spatial_df['lon'], spatial_df['lat'], 
        c=spatial_df['risk_score'], cmap='coolwarm', 
        s=spatial_df['risk_score']/4 + 5, alpha=0.5, edgecolor='none'
    )
    cb = plt.colorbar(sc)
    cb.set_label('예측 위험도 지수 (Risk Score, 0~100점)', fontsize=10)
    
    plt.title("공간적 변별력: 앙상블 인공지능이 도출한 서울시 블록 단위 예측 위험도 핫스팟 맵", fontsize=12, pad=15, weight='bold')
    plt.xlabel('경도 (Longitude)', fontsize=10)
    plt.ylabel('위도 (Latitude)', fontsize=10)
    plt.grid(True, linestyle=':', alpha=0.5)
    
    # 주요 지역 주석 (마포구 홍대, 성수 등)
    # 마포구 인근 (37.556, 126.92)
    plt.annotate(
        '마포구 홍대/서교 상권\n(주의/위험 밀집)',
        xy=(126.92, 37.556), xytext=(126.83, 37.58),
        arrowprops=dict(facecolor='black', shrink=0.08, width=0.5, headwidth=4),
        fontsize=8.5, bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="gray", lw=0.5)
    )
    
    # 성동구 인근 (37.54, 127.06)
    plt.annotate(
        '성동구 성수 상권\n(안전/중간 밀집)',
        xy=(127.06, 37.54), xytext=(127.13, 37.48),
        arrowprops=dict(facecolor='black', shrink=0.08, width=0.5, headwidth=4),
        fontsize=8.5, bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="gray", lw=0.5)
    )

    plt.tight_layout()
    plot4_path = os.path.join(img_dir, 'story4_spatial_risk_map.png')
    plt.savefig(plot4_path, dpi=300)
    plt.close()
    print(f"[Vis] Plot 4 저장 완료: '{plot4_path}'")

    print("[Success] 모든 고민의 흔적을 담은 시각화 스토리라인 그래프가 성공적으로 빌드되었습니다.")

if __name__ == "__main__":
    generate_stories()
