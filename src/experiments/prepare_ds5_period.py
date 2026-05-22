"""
실험용 데이터 준비: DS5 기간 (2023-2024) 추출
"""
import pandas as pd
import numpy as np

print("=" * 60)
print("DS5 효과 검증 실험: 데이터 준비")
print("=" * 60)

# =========================================================
# 1. 데이터 로드
# =========================================================
print("\n1. 데이터 로드 중...")

df = pd.read_parquet('data/final_merged_commercial_data_with_ds5.parquet')

print(f"  전체 데이터: {len(df):,}행")
print(f"  기간: {df['기준_년분기_코드'].min()} ~ {df['기준_년분기_코드'].max()}")

# =========================================================
# 2. DS5 기간 추출 (2023-2024)
# =========================================================
print("\n2. DS5 기간 추출 (2023-2024)...")

df_ds5_period = df[df['기준_년분기_코드'] >= 20231].copy()

print(f"  DS5 기간 데이터: {len(df_ds5_period):,}행")
print(f"  기간: {df_ds5_period['기준_년분기_코드'].min()} ~ {df_ds5_period['기준_년분기_코드'].max()}")

# =========================================================
# 3. DS5 매칭 확인
# =========================================================
print("\n3. DS5 매칭 확인...")

ds5_matched = df_ds5_period['주중_오전_avg'].notna().sum()
ds5_null = df_ds5_period['주중_오전_avg'].isna().sum()

print(f"  DS5 있음: {ds5_matched:,}행 ({ds5_matched/len(df_ds5_period)*100:.1f}%)")
print(f"  DS5 없음: {ds5_null:,}행 ({ds5_null/len(df_ds5_period)*100:.1f}%)")

# =========================================================
# 4. 분기별 확인
# =========================================================
print("\n4. 분기별 데이터 분포...")

for quarter in sorted(df_ds5_period['기준_년분기_코드'].unique()):
    subset = df_ds5_period[df_ds5_period['기준_년분기_코드'] == quarter]
    ds5_count = subset['주중_오전_avg'].notna().sum()
    year = quarter // 10
    q = quarter % 10
    print(f"  {year}Q{q}: 총 {len(subset):,}행, DS5 {ds5_count:,}행")

# =========================================================
# 5. Train/Test 분할 확인
# =========================================================
print("\n5. Train/Test 분할 (2023 vs 2024)...")

train_df = df_ds5_period[df_ds5_period['기준_년분기_코드'] < 20241].copy()
test_df = df_ds5_period[df_ds5_period['기준_년분기_코드'] >= 20241].copy()

print(f"  Train (2023): {len(train_df):,}행")
print(f"    DS5 있음: {train_df['주중_오전_avg'].notna().sum():,}행")
print(f"  Test (2024): {len(test_df):,}행")
print(f"    DS5 있음: {test_df['주중_오전_avg'].notna().sum():,}행")

# =========================================================
# 6. 저장
# =========================================================
print("\n6. 데이터 저장...")

# DS5 기간 전체
df_ds5_period.to_parquet('data/ds5_period_data.parquet', index=False)
print(f"  ✅ data/ds5_period_data.parquet 저장 완료")

# Train/Test 분할
train_df.to_parquet('data/ds5_period_train.parquet', index=False)
test_df.to_parquet('data/ds5_period_test.parquet', index=False)
print(f"  ✅ data/ds5_period_train.parquet 저장 완료")
print(f"  ✅ data/ds5_period_test.parquet 저장 완료")

# =========================================================
# 7. 요약
# =========================================================
print("\n" + "=" * 60)
print("데이터 준비 완료!")
print("=" * 60)
print(f"\n실험 데이터:")
print(f"  기간: 2023-2024 (2년, 8분기)")
print(f"  총 데이터: {len(df_ds5_period):,}행")
print(f"  Train: {len(train_df):,}행 (2023)")
print(f"  Test: {len(test_df):,}행 (2024)")
print(f"  DS5 매칭률: {ds5_matched/len(df_ds5_period)*100:.1f}%")
print(f"\n다음 단계:")
print(f"  1. python src/experiments/train_baseline_model.py")
print(f"  2. python src/experiments/train_proposed_model.py")
print(f"  3. python src/experiments/compare_results.py")
