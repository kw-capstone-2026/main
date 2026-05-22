import pandas as pd
import numpy as np

# =========================================================
# 1. 설정
# =========================================================

INPUT_PATH = "data/final_merged_commercial_data.parquet"
OUTPUT_PATH = "data/final_merged_commercial_data_with_ds5.parquet"

# =========================================================
# 2. 데이터 로드
# =========================================================

print("📂 parquet 로드 중...")

df = pd.read_parquet(INPUT_PATH)

print("✅ 로드 완료")
print(df.shape)

# =========================================================
# 3. 숫자형 변환
# =========================================================

numeric_cols = [
    '점포_수_y',
    '유사_업종_점포_수_y',
    '상권_전체점포_수',
    # '총_아파트_세대수',  # 컬럼 없음
    # '총_직장_인구_수',   # 컬럼 없음
    '당월_매출_금액',
    '당월_매출_건수'
]

for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(
            df[col],
            errors='coerce'
        ).fillna(0)

print("✅ 숫자형 변환 완료")

# =========================================================
# 🔧 업종별 → 상권별 집계
# =========================================================
print("🔧 업종별 데이터를 상권별로 집계 중...")

# 집계 전 행 수
before_agg = len(df)

# 집계 방법 정의
# sum: 합산 (매출, 점포수 등)
# mean: 평균 (비율, 유동인구 등)
# first: 첫 번째 값 (상권 정보 등)

agg_dict = {}

# 상권 정보 (첫 번째 값)
for col in ['상권_구분_코드_x', '상권_구분_코드_명_x', '상권_코드_명_x',
            'TRDAR_CD', 'lat', 'lon', 'TRDAR_CD_N', '상권_구분_코드',
            '상권_구분_코드_명', '상권_코드_명']:
    if col in df.columns:
        agg_dict[col] = 'first'

# 매출 (합산)
for col in df.columns:
    if '매출' in col and ('금액' in col or '건수' in col):
        agg_dict[col] = 'sum'

# 점포수 (합산)
for col in ['점포_수_x', '점포_수_y', '유사_업종_점포_수_x', '유사_업종_점포_수_y',
            '개업_점포_수', '폐업_점포_수', '프랜차이즈_점포_수_x', '프랜차이즈_점포_수_y',
            '상권_전체점포_수']:
    if col in df.columns:
        agg_dict[col] = 'sum'

# 유동인구 (합산)
for col in df.columns:
    if '유동인구' in col:
        agg_dict[col] = 'sum'

# 비율/율 (평균)
for col in df.columns:
    if any(x in col for x in ['비율', '율', '평균']):
        agg_dict[col] = 'mean'

# 기타 숫자형 (평균)
for col in df.columns:
    if col not in agg_dict and df[col].dtype in ['int64', 'float64']:
        # 이미 처리한 컬럼 제외
        if col not in ['기준_년분기_코드', '상권_코드']:
            agg_dict[col] = 'mean'

# 집계 실행
df = df.groupby(['기준_년분기_코드', '상권_코드'], as_index=False).agg(agg_dict)

# 결과 확인
after_agg = len(df)
print(f"  집계 전: {before_agg:,}행")
print(f"  집계 후: {after_agg:,}행")
print(f"  ✅ {before_agg - after_agg:,}행 감소 (업종 통합)")

# =========================================================
# 🆕 DS5 생활인구 데이터 병합
# =========================================================
print("📊 DS5 생활인구 데이터 병합 중...")

# DS5 데이터 로드
try:
    df_ds5 = pd.read_parquet('data/ds5_clean.parquet')
    
    # 필요한 컬럼만 선택
    ds5_cols = [
        '기준_년분기_코드',
        '상권_코드',
        '주중_오전_avg',
        '주중_점심_avg',
        '주중_저녁_avg',
        '주중_야간_avg',
        '주말_주간_avg',
        '주말_야간_avg',
        '주야간비율',
        'population_slope',
        'population_entropy',
        '평균인구'
    ]
    
    df_ds5_selected = df_ds5[ds5_cols].copy()
    
    # 타입 통일 (필수!)
    def convert_quarter(q):
        """2023Q1 → 20231"""
        if isinstance(q, str) and 'Q' in q:
            year = q[:4]
            quarter = q[-1]
            return int(year + quarter)
        return int(q)

    df_ds5_selected['기준_년분기_코드'] = df_ds5_selected['기준_년분기_코드'].apply(convert_quarter)
    df_ds5_selected['상권_코드'] = df_ds5_selected['상권_코드'].astype('int64')
    
    print(f"  DS5 데이터: {len(df_ds5_selected):,}행")
    print(f"  DS5 상권: {df_ds5_selected['상권_코드'].nunique():,}개")
    print(f"  DS5 기간: {df_ds5_selected['기준_년분기_코드'].min()} ~ {df_ds5_selected['기준_년분기_코드'].max()}")
    
    # Left Join (메인 데이터 크기 유지)
    before_rows = len(df)
    df = df.merge(
        df_ds5_selected,
        on=['기준_년분기_코드', '상권_코드'],
        how='left'
    )
    after_rows = len(df)
    
    # 매칭 확인
    ds5_matched = df['주중_오전_avg'].notna().sum()
    ds5_null = df['주중_오전_avg'].isna().sum()
    
    print(f"  ✅ 병합 완료: {after_rows:,}행 (변화 없음: {before_rows == after_rows})")
    print(f"  DS5 매칭: {ds5_matched:,}행 ({ds5_matched/len(df)*100:.1f}%)")
    print(f"  DS5 Null: {ds5_null:,}행 ({ds5_null/len(df)*100:.1f}%)")
    
except FileNotFoundError:
    print("  ⚠️  DS5 파일 없음 - 건너뜀")
except Exception as e:
    print(f"  ⚠️  DS5 병합 실패: {e}")
    print("  → DS5 없이 계속 진행")

print("✅ DS5 병합 단계 완료")

# =========================================================
# 4. Density / Ratio Feature 생성
# =========================================================

print("🧠 Density Feature 생성 중...")

# ---------------------------------------------------------
# 4-1. 직장인구 대비 점포 밀도 (컬럼 없음 - 건너뜀)
# ---------------------------------------------------------
print("  ⚠️ 직장인구_100명당_점포수: 건너뜀 (컬럼 없음)")

# ---------------------------------------------------------
# 4-2. 아파트 세대 대비 점포 밀도 (컬럼 없음 - 건너뜀)
# ---------------------------------------------------------
print("  ⚠️ 아파트_100세대당_점포수: 건너뜀 (컬럼 없음)")

# ---------------------------------------------------------
# 4-3. 유사 업종 경쟁 강도
# ---------------------------------------------------------
# 전체 점포 중 유사업종 비율
df['유사업종_점포비율'] = np.where(
    df['상권_전체점포_수'] > 0,
    (df['유사_업종_점포_수_y'] / df['상권_전체점포_수']) * 100,
    0
)

# ---------------------------------------------------------
# 4-4. 직장인구 대비 유사업종 경쟁 강도 (컬럼 없음 - 건너뜀)
# ---------------------------------------------------------
print("  ⚠️ 직장인구_100명당_유사업종수: 건너뜀 (컬럼 없음)")

# ---------------------------------------------------------
# 4-5. 매출 밀도
# ---------------------------------------------------------
# 점포당 평균 매출
df['점포당_매출_밀도'] = np.where(
    df['점포_수_y'] > 0,
    df['당월_매출_금액'] / df['점포_수_y'],
    0
)

# ---------------------------------------------------------
# 4-6. 직장인구 대비 매출 (컬럼 없음 - 건너뜀)
# ---------------------------------------------------------
print("  ⚠️ 직장인구_1인당_매출: 건너뜀 (컬럼 없음)")

# ---------------------------------------------------------
# 4-7. 아파트 세대 대비 매출 (컬럼 없음 - 건너뜀)
# ---------------------------------------------------------
print("  ⚠️ 아파트세대당_매출: 건너뜀 (컬럼 없음)")

print("✅ Density Feature 생성 완료")

# =========================================================
# 5. 무한대 처리
# =========================================================

print("🧹 inf 값 처리 중...")

# 실제로 생성된 컬럼만 처리
replace_cols = [
    '유사업종_점포비율',
    '점포당_매출_밀도'
]

for col in replace_cols:
    if col in df.columns:
        df[col] = df[col].replace(
            [np.inf, -np.inf],
            0
        )
        df[col] = df[col].fillna(0)

print("✅ inf 처리 완료")

# =========================================================
# 6. 저장
# =========================================================

print("💾 parquet 저장 중...")

df.to_parquet(
    OUTPUT_PATH,
    index=False
)

print("🎉 저장 완료!")
print(f"📁 저장 위치: {OUTPUT_PATH}")

# =========================================================
# 7. 생성 컬럼 확인
# =========================================================

# 실제로 생성된 컬럼만 확인
new_cols = [
    '유사업종_점포비율',
    '점포당_매출_밀도'
]

# DS5 컬럼 추가
ds5_feature_cols = [
    '주중_오전_avg',
    '주중_점심_avg',
    '주중_저녁_avg',
    '주중_야간_avg',
    '주말_주간_avg',
    '주말_야간_avg',
    '주야간비율',
    'population_slope',
    'population_entropy',
    '평균인구'
]

print("\n===== 생성 Feature 확인 =====")
print("\n[기본 Feature]")
for col in new_cols:
    if col in df.columns:
        print(f"  ✅ {col}")

print("\n[DS5 Feature]")
for col in ds5_feature_cols:
    if col in df.columns:
        non_null = df[col].notna().sum()
        print(f"  ✅ {col}: {non_null:,}개 값")

print("\n===== 최종 데이터 정보 =====")
print(f"  총 행: {len(df):,}")
print(f"  총 컬럼: {len(df.columns)}")
print(f"  DS5 매칭률: {df['주중_오전_avg'].notna().sum() / len(df) * 100:.1f}%")