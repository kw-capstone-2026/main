import pandas as pd

# 인코딩 추가!
df = pd.read_csv('250_LOCAL_RESD_20260301.csv', encoding='cp949')
# 또는
# df = pd.read_csv('250_LOCAL_RESD_20260301.csv', encoding='euc-kr')

# 기본 정보
print("=== 데이터 기본 정보 ===")
print(f"행 수: {len(df):,}")
print(f"컬럼 수: {len(df.columns)}")

# 컬럼 리스트
print("\n=== 컬럼 리스트 ===")
print(df.columns.tolist())

# 상위 5행
print("\n=== 상위 5행 ===")
print(df.head())

# 데이터 타입
print("\n=== 데이터 타입 ===")
print(df.dtypes)

# 기본 통계
print("\n=== 기본 통계 ===")
print(df.describe())

# 결측치
print("\n=== 결측치 ===")
print(df.isnull().sum())

# 고유 격자 수
print("\n=== 고유 격자 수 ===")
for col in df.columns:
    if 'grid' in col.lower() or '격자' in col.lower():
        print(f"{col}: {df[col].nunique():,}개")