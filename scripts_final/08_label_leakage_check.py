"""추가 점검: 정답(과포화_위험_여부)과 입력 변수의 관계로 데이터 누수 정황을 확인. 라벨은 바꾸지 않음.
결과는 output/label_check.md (비전문가용 설명 포함)."""
import os
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.tree import DecisionTreeClassifier, export_text

sys.path.insert(0, os.path.dirname(__file__))
from common import DATA_PATH, OUT_DIR, SEED, TARGET, TEST_START, WORK_DIR, setup_logging  # noqa: E402

setup_logging('08_label_leakage_check')

COLS = ['상권_코드', '서비스_업종_코드', '기준_년분기_코드', TARGET, '폐업_점포_수', '폐업_률_x', '폐업_률_y',
        '전년_동기_대비_폐업_증감률', '점포당_평균_매출', '개업_율_x', '점포_수_x']
df = pd.read_parquet(DATA_PATH, columns=COLS)
df['q'] = pd.to_numeric(df['기준_년분기_코드'], errors='coerce').astype(int)
df[TARGET] = pd.to_numeric(df[TARGET], errors='coerce').fillna(0).astype(int)
df = df.sort_values(['상권_코드', '서비스_업종_코드', 'q']).reset_index(drop=True)

# 1) 전년_동기_대비_폐업_증감률 계산식 역추적: (이번 분기 폐업 수 − 4분기 전 폐업 수) / (4분기 전 폐업 수 + 1)
lag4 = df.groupby(['상권_코드', '서비스_업종_코드'])['폐업_점포_수'].shift(4)
recon = (df['폐업_점포_수'] - lag4) / (lag4 + 1)
m = df['전년_동기_대비_폐업_증감률'].notna() & recon.notna()
match = (np.abs(df.loc[m, '전년_동기_대비_폐업_증감률'] - recon[m]) < 1e-6).mean()
print(f'[1] 전년_동기_대비_폐업_증감률 = (이번 분기 폐업 수 − 작년 같은 분기 폐업 수) / (작년 같은 분기 폐업 수 + 1)')
print(f'    재계산 값과 일치하는 행 비율: {match:.2%} ({int(m.sum()):,}행 비교)')

# 2) 2024년에서 변수 하나만으로 정답을 얼마나 맞히는지 (ROC-AUC, 0.5 = 무작위)
t = df[df['q'] >= TEST_START]
pred = pd.read_parquet(os.path.join(WORK_DIR, 'pred_2024.parquet'))
y = t[TARGET].to_numpy()
single = {
    '폐업_률_x (이번 분기, 업종 단위, 모델 입력 아님)': t['폐업_률_x'],
    '폐업_점포_수 (이번 분기, 모델 입력 아님)': t['폐업_점포_수'],
    '전년_동기_대비_폐업_증감률 (모델 입력)': t['전년_동기_대비_폐업_증감률'].fillna(0),
    '점포당_평균_매출 (모델 입력, 낮을수록 위험으로 뒤집음)': -t['점포당_평균_매출'],
    '폐업_률_y (모델 입력, 상권 단위)': t['폐업_률_y'],
}
print('\n[2] 2024년, 변수 하나만으로 정답 맞히기 (ROC-AUC)')
auc_rows = []
for k, v in single.items():
    a = roc_auc_score(y, v.to_numpy())
    auc_rows.append((k, a))
    print(f'    {k:<46} {a:.3f}')
print(f'    {"참고: 우리 모델 (앙상블)":<46} {0.9089:.3f}')

# 3) 정답과 이번 분기 폐업률의 관계
zero = t['폐업_률_x'] == 0
print('\n[3] 이번 분기 폐업_률_x = 0 인 블록 중 정답=1 비율:', f'{t.loc[zero, TARGET].mean():.2%} ({int(zero.sum()):,}블록)')
print('    정답=1 블록 중 폐업_률_x > 0 비율:', f'{(t.loc[t[TARGET] == 1, "폐업_률_x"] > 0).mean():.2%}')

# 4) 얕은 결정트리(깊이 3)로 정답 규칙 추정: 2019~2023 학습 → 2024 평가
feat = ['폐업_률_x', '폐업_점포_수', '점포당_평균_매출', '개업_율_x', '점포_수_x']
tr = df[df['q'] < TEST_START]
tree = DecisionTreeClassifier(max_depth=3, random_state=SEED).fit(tr[feat].fillna(0), tr[TARGET])
tree_auc = roc_auc_score(y, tree.predict_proba(t[feat].fillna(0))[:, 1])
rules = export_text(tree, feature_names=feat, decimals=1)
print(f'\n[4] 깊이 3 결정트리 (이번 분기 폐업률·매출 등 5개 변수) 2024년 ROC-AUC: {tree_auc:.3f}')
print(rules)

md = f"""# 정답(라벨)과 데이터 누수 점검

> 라벨은 바꾸지 않았음. 파케이에 있는 `과포화_위험_여부`를 그대로 쓰고, 입력 변수와의 관계만 측정함.
> 라벨을 만든 코드는 저장소에서 찾지 못했음. 아래는 데이터로 추정한 결과이고 확정이 아님.

## 한 줄 요약

정답은 **"이번 분기에 그 업종 가게가 많이 문 닫았고(폐업률), 가게당 매출이 낮은 곳"** 과 거의 같음. 그런데 모델의 1위 변수 `전년_동기_대비_폐업_증감률`이 **이번 분기 폐업 수**로 계산돼 있어서, 모델이 "미래를 예측"했다기보다 **"이번 분기 상태를 진단"** 한 것에 가까움. 교수님이 데이터 누수를 물으면 이 점을 솔직하게 설명해야 함.

## 근거

1. `전년_동기_대비_폐업_증감률` = (이번 분기 폐업 점포 수 − 작년 같은 분기 폐업 점포 수) ÷ (작년 같은 분기 폐업 점포 수 + 1) 임. 재계산 값과 **{match:.1%}** 일치함 → 이번 분기 폐업 정보가 입력에 들어 있음.
2. 2024년에서 변수 하나만으로 정답을 맞힌 정도 (ROC-AUC, 0.5 = 찍기, 1.0 = 완벽):

| 변수 | ROC-AUC |
|---|---:|
""" + '\n'.join(f'| {k} | {a:.3f} |' for k, a in auc_rows) + f"""
| 참고: 우리 모델 (앙상블) | 0.909 |

3. 이번 분기 폐업률(`폐업_률_x`)이 0인 블록 {int(zero.sum()):,}개 중 정답=1은 **{t.loc[zero, TARGET].mean():.1%}**. 정답=1 블록의 **{(t.loc[t[TARGET] == 1, '폐업_률_x'] > 0).mean():.1%}**는 이번 분기 폐업이 있었음.
4. 이번 분기 폐업률·매출 등 5개 변수로 만든 아주 단순한 규칙(깊이 3 결정트리)이 2024년에서 ROC-AUC **{tree_auc:.3f}** 를 냄 (우리 모델 0.909보다 높음). 규칙:

```
{rules}```

## 발표·시연에서 어떻게 말할지 (제안)

- "폐업 예측"보다 **"상권 과포화 위험 진단"** 이라고 부르는 것이 정확함.
- "2019~2023년으로 학습한 모델이 처음 보는 2024년에서도 진단 성능(ROC-AUC 0.909)을 유지함"은 사실이므로 말해도 됨.
- "다음 분기 폐업을 미리 맞힌다"는 표현은 쓰지 말 것 (현재 검증되지 않음).
- 확실히 하려면: 라벨 정의를 만든 팀원에게 확인하거나, 이번 분기 입력으로 **다음 분기** 정답을 맞히는 실험을 추가해야 함 (모델 재학습 필요, 이번 작업 범위 밖).
"""
with open(os.path.join(OUT_DIR, 'label_check.md'), 'w', encoding='utf-8') as f:
    f.write(md)
print('[저장] output/label_check.md')
print(f'[요약] 증감률 계산식 일치 {match:.1%}, 폐업_률_x 단독 AUC {auc_rows[0][1]:.3f}, 단순 규칙 AUC {tree_auc:.3f}')
