"""1단계: 파케이 로드, 구조 확인, 2024년 필터, 이름 열 중복(_x/_y) 비교, 키 유일성 확인."""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from common import DATA_PATH, OUT_DIR, TARGET, TEST_START, WORK_DIR, load_feature_cols, setup_logging  # noqa: E402

setup_logging('01_load_and_inspect')

EXPECTED_ROWS = 87_179
EXPECTED_POS = 2_705
TOLERANCE = 0.01  # 기대값 대비 ±1% 넘게 다르면 멈춤

REQUIRED = ['상권_코드', '상권_코드_명_x', '상권_구분_코드_명_x', '서비스_업종_코드',
            '서비스_업종_코드_명_x', 'lat', 'lon', '기준_년분기_코드', TARGET]
# master_2024.csv에 같이 넣을 참고 열
EXTRA = ['폐업_률_y', '개업_율_y', '점포_수_y', '상권 내부 업종 점유율(%)', '운영_영업_개월_평균',
         '점포_수_x', '폐업_률_x', '개업_율_x']  # _y는 상권 단위 값, _x는 상권×업종 단위 값

df = pd.read_parquet(DATA_PATH)
print(f'전체 데이터: {df.shape[0]:,}행 × {df.shape[1]}열')

with open(os.path.join(OUT_DIR, 'parquet_columns.txt'), 'w', encoding='utf-8') as f:
    f.write(f'# {os.path.basename(DATA_PATH)}  shape={df.shape}\n')
    for i, (c, t) in enumerate(df.dtypes.items()):
        f.write(f'{i:3d}\t{c}\t{t}\n')
print(f'[저장] output/parquet_columns.txt ({df.shape[1]}개 열)')
print('dtype 요약:', df.dtypes.astype(str).value_counts().to_dict())

# ── 필수 열 확인 ──
missing = [c for c in REQUIRED + EXTRA + load_feature_cols() if c not in df.columns]
if missing:
    for c in missing:
        stem = c.split('_')[0]
        print(f'[누락] {c} → 비슷한 열: {[x for x in df.columns if stem in x][:10]}')
    sys.exit('[중단] 필수 열이 없음')
print('필수 열·참고 열·모델 변수 32개 모두 존재함')

# ── 2024년 필터 ──
df['기준_년분기_코드'] = pd.to_numeric(df['기준_년분기_코드'], errors='coerce')
print('분기 분포(전체):', df['기준_년분기_코드'].value_counts().sort_index().to_dict())
test = df[df['기준_년분기_코드'] >= TEST_START].copy()
y = pd.to_numeric(test[TARGET], errors='coerce').fillna(0).astype(int)
n, pos = len(test), int(y.sum())
print(f'2024년(>= {TEST_START}) 행 수: {n:,} (기대 {EXPECTED_ROWS:,})')
print(f'정답=1 행 수: {pos:,} ({pos / n:.2%}) (기대 {EXPECTED_POS:,})')
print('분기별 행 수:', test['기준_년분기_코드'].value_counts().sort_index().to_dict())
if abs(n - EXPECTED_ROWS) / EXPECTED_ROWS > TOLERANCE or abs(pos - EXPECTED_POS) / EXPECTED_POS > TOLERANCE:
    sys.exit('[중단] 행 수 또는 정답 수가 기대값과 크게 다름')

# ── _x / _y 이름 열 비교 ──
print('\n[_x / _y 열 비교 (2024년 구간)]')
pairs = sorted({c[:-2] for c in test.columns if c.endswith('_x') and c[:-2] + '_y' in test.columns})
for stem in pairs:
    a, b = test[stem + '_x'], test[stem + '_y']
    both_na = a.isna() & b.isna()
    eq = (a.astype(str) == b.astype(str)) | both_na
    print(f'  {stem}_x vs _y: 불일치 {int((~eq).sum()):,}행 / 결측 x={int(a.isna().sum())}, y={int(b.isna().sum())}')
    if (~eq).any() and stem in ('상권_코드_명', '상권_구분_코드_명', '서비스_업종_코드_명'):
        print('    예시:', test.loc[~eq, [stem + '_x', stem + '_y']].head(3).values.tolist())

# ── 키 유일성 ──
key = ['상권_코드', '서비스_업종_코드', '기준_년분기_코드']
dup = test.duplicated(key, keep=False)
print(f'\n키 {key} 중복 행 수: {int(dup.sum()):,}')
if dup.any():
    print('  중복 키 조합 수:', int(test[dup].drop_duplicates(key).shape[0]))
    print(test.loc[dup, key + ['상권_코드_명_x', '서비스_업종_코드_명_x', '점포_수_y']]
          .sort_values(key).head(10).to_string())
    print('  (지시대로 삭제하지 않고 그대로 유지함)')

# ── 주요 열의 dtype·값 범위 (단위 확인용) ──
print('\n[주요 열 값 범위 (2024년)]  ※ 폐업률·개업률 최대가 100이면 % 단위')
for c in ['폐업_률_x', '폐업_률_y', '개업_율_x', '개업_율_y', '점포_수_x', '점포_수_y', '상권 내부 업종 점유율(%)',
          '운영_영업_개월_평균', '전년_동기_대비_폐업_증감률', '점포당_평균_매출', 'lat', 'lon']:
    s = pd.to_numeric(test[c], errors='coerce')
    print(f'  {c:<26} dtype={str(test[c].dtype):<8} 최소 {s.min():>14,.2f}  중앙 {s.median():>14,.2f}  최대 {s.max():>16,.2f}  결측 {int(s.isna().sum())}')

# _y 계열이 상권 단위 값인지 확인 (같은 상권·분기 안에서 업종이 달라도 값이 같은지)
print('\n[상권 단위 값 여부] 같은 (상권, 분기) 안에서 값이 하나뿐인 비율')
grp = test.groupby(['상권_코드', '기준_년분기_코드'])
for c in ['점포_수_y', '폐업_률_y', '개업_율_y', '상권 내부 업종 점유율(%)', '운영_영업_개월_평균', 'lat', '점포_수_x', '폐업_률_x']:
    print(f'  {c:<26} {(grp[c].nunique(dropna=False) == 1).mean():.1%}')

# ── 결측 현황 (참고) ──
print('\n필수 열 결측 수:', {c: int(test[c].isna().sum()) for c in REQUIRED if test[c].isna().any()} or '없음')

keep = list(dict.fromkeys(REQUIRED + EXTRA + load_feature_cols()))
test = test[keep].reset_index(drop=True)
test.to_parquet(os.path.join(WORK_DIR, 'test_2024.parquet'), index=False)
print(f'\n[요약] 2024년 {n:,}행, 정답=1 {pos:,}행 ({pos / n:.2%}), 키 중복 {int(dup.sum())}행')
