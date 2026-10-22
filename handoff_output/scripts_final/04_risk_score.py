"""5단계: 위험지수(0~100) 계산, 분포 확인, 위험등급 부여와 등급 기준 검증.

등급 기준(common.py의 GRADE_DANGER/GRADE_CAUTION)은 신용평가 등급표 방식으로 정함:
- 2024 Q1~Q3(기준 설정 구간)에서 5점 구간별 실제 위험률 ÷ 평균 위험률(=lift)을 계산
- 주의 시작 = lift가 1(평균)을 넘기 시작하는 점수, 위험 시작 = lift가 5배 이상이 되는 점수
- 2024 Q4(시연 분기)는 기준 설정에 쓰지 않고 검증에만 사용
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from common import (DEMO_QUARTER, GRADE_CAUTION, GRADE_DANGER, OUT_DIR, TARGET, WORK_DIR,  # noqa: E402
                    save_csv, setup_logging)

P_CLIP = (0.0001, 0.9999)
OFFSET, FACTOR = 50, 15
BAND = 5                  # 기준 설정용 점수 구간 폭
LIFT_CAUTION = 1.0        # 평균보다 위험해지는 지점
LIFT_DANGER = 5.0         # 평균의 5배 이상 위험해지는 지점
GRADES = ['위험', '주의', '안전']

setup_logging('04_risk_score')


def to_risk_score(p):
    p = np.clip(p, *P_CLIP)
    log_odds = np.log(p / (1 - p))
    return np.rint(np.clip(OFFSET + FACTOR * log_odds, 0, 100)).astype(int)


def to_grade(score, danger=GRADE_DANGER, caution=GRADE_CAUTION):
    return np.where(score >= danger, '위험', np.where(score >= caution, '주의', '안전'))


def wilson(k, n, z=1.96):
    """비율의 95% 신뢰구간 (Wilson)."""
    if n == 0:
        return np.nan, np.nan
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return c - h, c + h


df = pd.read_parquet(os.path.join(WORK_DIR, 'test_2024.parquet'))
pred = pd.read_parquet(os.path.join(WORK_DIR, 'pred_2024.parquet'))
pred['risk_score'] = to_risk_score(pred['prob_final'].to_numpy())
pred['risk_grade'] = to_grade(pred['risk_score'].to_numpy())
pred = pred.drop(columns=['risk_grade_draft'], errors='ignore')
s = pred['risk_score']
y = df[TARGET].astype(int)
q = df['기준_년분기_코드']

print('위험지수 분포 (2024년 전체)')
qs = s.quantile([.10, .25, .50, .75, .90, .95])
print(f'  최소 {s.min()}  ' + '  '.join(f'p{int(k * 100)} {v:.0f}' for k, v in qs.items()) + f'  최대 {s.max()}  평균 {s.mean():.1f}')
bins = pd.cut(s.clip(upper=99), [0, 20, 40, 60, 80, 100], right=False, labels=['0~20', '20~40', '40~60', '60~80', '80~100'])
for k, v in bins.value_counts().sort_index().items():
    print(f'  {k:>7}: {v:>6,}개 ({v / len(s):.1%})  실제 위험 비율 {y[bins == k].mean():.1%}')
print(f'  0점 {int((s == 0).sum()):,}개, 100점 {int((s == 100).sum()):,}개')

# ── 1) 기준 설정: Q1~Q3 5점 구간별 lift ──
band = (s.clip(upper=99) // BAND * BAND).astype(int)
rows = []
for period, mask in [('Q1~Q3 (기준 설정)', q < DEMO_QUARTER), ('Q4 (검증)', q == DEMO_QUARTER)]:
    base = y[mask].mean()
    g = y[mask].groupby(band[mask]).agg(['size', 'sum'])
    for lo, r in g.iterrows():
        rows.append({'period': period, 'score_from': lo, 'score_to': lo + BAND - 1, 'n_blocks': int(r['size']),
                     'n_actual_risk': int(r['sum']), 'actual_risk_rate_pct': round(100 * r['sum'] / r['size'], 2),
                     'lift_vs_avg': round(r['sum'] / r['size'] / base, 2)})
cal = pd.DataFrame(rows)
save_csv(cal, 'risk_grade_calibration.csv')

c = cal[cal['period'].str.startswith('Q1')].set_index('score_from')['lift_vs_avg']
# 그 점수 이상 모든 구간이 기준 lift 이상인 최저 점수 (한 번 넘었다 떨어지는 구간은 제외)
derive = lambda t: int(min(lo for lo in c.index if (c.loc[lo:] >= t).all()))
d_caution, d_danger = derive(LIFT_CAUTION), derive(LIFT_DANGER)
print(f'\n[기준 설정] Q1~Q3 데이터로 계산한 기준: 주의 ≥ {d_caution}점 (lift ≥ {LIFT_CAUTION}), 위험 ≥ {d_danger}점 (lift ≥ {LIFT_DANGER})')
print(f'            확정 상수(common.py): 주의 ≥ {GRADE_CAUTION}, 위험 ≥ {GRADE_DANGER} → '
      + ('일치' if (d_caution, d_danger) == (GRADE_CAUTION, GRADE_DANGER) else '불일치(확인 필요)'))
print('  Q1~Q3 구간별 lift:', ', '.join(f'{lo}~{lo + BAND - 1}:{v}' for lo, v in c.items()))

# ── 2) 검증: 등급별 실제 위험률 (Q4) ──


def grade_table(danger, caution, mask):
    g = pd.Series(to_grade(s[mask].to_numpy(), danger, caution), index=s[mask].index)
    yy, base = y[mask], y[mask].mean()
    out = []
    for lab in GRADES:
        m = g == lab
        k, n = int(yy[m].sum()), int(m.sum())
        lo, hi = wilson(k, n)
        out.append({'grade': lab, 'share_pct': 100 * n / len(g), 'n_blocks': n, 'actual_risk_rate_pct': 100 * k / max(n, 1),
                    'ci95_low_pct': 100 * lo, 'ci95_high_pct': 100 * hi, 'lift_vs_avg': k / max(n, 1) / base,
                    'capture_pct': 100 * k / yy.sum()})
    return pd.DataFrame(out)


q4 = (q == DEMO_QUARTER).to_numpy()
final = grade_table(GRADE_DANGER, GRADE_CAUTION, q4)
print(f'\n[검증] 확정 기준 (위험 ≥{GRADE_DANGER} / 주의 ≥{GRADE_CAUTION}), 2024 Q4, 평균 위험률 {y[q4].mean():.2%}')
for r in final.itertuples():
    print(f'  {r.grade}: 블록 {r.share_pct:5.1f}% ({r.n_blocks:,}개) | 실제 위험률 {r.actual_risk_rate_pct:5.1f}% '
          f'(95% CI {r.ci95_low_pct:.1f}~{r.ci95_high_pct:.1f}) | 평균의 {r.lift_vs_avg:.1f}배 | 실제 위험 중 {r.capture_pct:.1f}% 포함')
mono = final['actual_risk_rate_pct'].is_monotonic_decreasing
sep = final.loc[0, 'ci95_low_pct'] > final.loc[1, 'ci95_high_pct'] and final.loc[1, 'ci95_low_pct'] > final.loc[2, 'ci95_high_pct']
print(f'  등급 순서대로 실제 위험률이 감소: {mono} / 등급 간 95% 신뢰구간이 겹치지 않음: {sep}')
if not mono:
    sys.exit('[중단] 등급별 실제 위험률이 순서대로 나오지 않음')

print('\n[비교] 다른 기준안 (2024 Q4)')
compare = []
for tag, dg, ct in [('확정 75/50', 75, 50), ('임시 시안 70/40', 70, 40), ('70/50', 70, 50), ('80/50', 80, 50)]:
    t = grade_table(dg, ct, q4).set_index('grade')
    compare.append({'기준': tag, **{f'{k}_비율%': round(t.loc[k, 'share_pct'], 1) for k in GRADES},
                    **{f'{k}_실제위험률%': round(t.loc[k, 'actual_risk_rate_pct'], 1) for k in GRADES},
                    '위험_lift': round(t.loc['위험', 'lift_vs_avg'], 1), '주의이상_포착%': round(100 - t.loc['안전', 'capture_pct'], 1)})
    print('  ' + ' | '.join(f'{k} {v}' for k, v in compare[-1].items()))

# ── 3) 근거 문서 ──
cq = cal[cal['period'].str.startswith('Q1')]
cv = cal[cal['period'].str.startswith('Q4')].set_index('score_from')
md = [
    '# 위험등급 기준과 근거', '',
    f'**확정 기준: 안전 0~{GRADE_CAUTION - 1}점 / 주의 {GRADE_CAUTION}~{GRADE_DANGER - 1}점 / 위험 {GRADE_DANGER}~100점**', '',
    '## 어떻게 정했나 (신용평가 등급표와 같은 방식)', '',
    '1. 2024년 1~3분기(기준 설정 구간)의 블록을 위험지수 5점 단위로 나누고, 구간마다 **실제 과포화 비율이 평균의 몇 배인지(lift)** 계산함.',
    f'2. **주의 시작 = 실제 위험률이 평균을 넘기 시작하는 점수 → {d_caution}점.** 이 점수는 모델이 위험/안전을 가르는 경계(확률 약 0.5)와도 같음.',
    f'3. **위험 시작 = 실제 위험률이 평균의 5배 이상이 되는 점수 → {d_danger}점.** 70~74점 구간 {c.get(70, np.nan)}배에서 75~79점 구간 {c.get(75, np.nan)}배로 크게 뛰는 지점임.',
    '4. 2024년 4분기(시연 분기)는 기준을 정할 때 쓰지 않고, **처음 보는 분기로 검증만** 함.', '',
    '위험지수는 신용점수처럼 log-odds를 점수로 바꾼 것이라(점수 = 50 + 15 × log-odds), 약 10.4점 오를 때마다 위험 배율(odds)이 2배가 됨.', '',
    '## 검증 결과 (2024년 4분기, 21,664블록)', '',
    '| 등급 | 점수 | 블록 비율 | 실제 과포화 비율 (95% 신뢰구간) | 평균 대비 | 실제 과포화 중 포함 비율 |',
    '|---|---|---:|---:|---:|---:|',
    *[f'| {r.grade} | {rng} | {r.share_pct:.1f}% | {r.actual_risk_rate_pct:.1f}% ({r.ci95_low_pct:.1f}~{r.ci95_high_pct:.1f}) | {r.lift_vs_avg:.1f}배 | {r.capture_pct:.1f}% |'
      for r, rng in zip(final.itertuples(), [f'{GRADE_DANGER}~100', f'{GRADE_CAUTION}~{GRADE_DANGER - 1}', f'0~{GRADE_CAUTION - 1}'])],
    '',
    f'- 등급이 높을수록 실제 과포화 비율이 높음 (순서 유지: {"예" if mono else "아니오"}), 등급 사이 95% 신뢰구간이 겹치지 않음: {"예" if sep else "아니오"}',
    f'- 평균 과포화 비율(4분기): {y[q4].mean():.1%}', '',
    '## 다른 기준안과 비교 (2024년 4분기)', '',
    '| 기준 | 위험 | 주의 | 안전 | 위험 등급 실제 과포화 비율 | 위험 등급 평균 대비 | 주의 이상이 잡은 실제 과포화 |',
    '|---|---:|---:|---:|---:|---:|---:|',
    *[f'| {r["기준"]} | {r["위험_비율%"]}% | {r["주의_비율%"]}% | {r["안전_비율%"]}% | {r["위험_실제위험률%"]}% | {r["위험_lift"]}배 | {r["주의이상_포착%"]}% |' for r in compare],
    '',
    '## 5점 구간별 실제 과포화 비율', '',
    '| 점수 | Q1~Q3 블록 수 | Q1~Q3 실제 비율 | Q1~Q3 평균 대비 | Q4 실제 비율 | Q4 평균 대비 |', '|---|---:|---:|---:|---:|---:|',
    *[f'| {r.score_from}~{r.score_to} | {r.n_blocks:,} | {r.actual_risk_rate_pct:.1f}% | {r.lift_vs_avg:.2f} | '
      f'{cv.loc[r.score_from, "actual_risk_rate_pct"] if r.score_from in cv.index else "-"}% | {cv.loc[r.score_from, "lift_vs_avg"] if r.score_from in cv.index else "-"} |'
      for r in cq.itertuples()],
    '',
    '## 참고한 사례',
    '',
    '- 3단계 신호등 방식: 이채은·최인수, 「자본 체급과 경쟁 밀도 기반 카페 생존 분석 및 폐업 예측 모형 - 서울특별시를 중심으로」, 한국경영공학회지 31(2), 2026: 녹색·황색·적색 신호등형 폐업 조기경보 제안 (구간 기준값은 원문 확인 필요)',
    '- 서울시 우리마을가게 상권분석서비스 "상권신호등": 신규 창업 위험도를 색깔 단계(주의·의심·위험·고위험)로 표시',
    '- 신용평가 점수표: 점수를 log-odds로 만들고(Points to Double the Odds), 등급별 실제 부도율이 순서대로 커지는지로 등급표를 검증함',
    '- 방법론(공공데이터 + XGBoost + SHAP): 장호준·이기환·이희상, 「공공데이터와 설명가능한 AI 기법을 활용한 자영업 상권 분석과 장기 생존 예측」, 대한산업공학회지 50(3), 173-188, 2024',
]
with open(os.path.join(OUT_DIR, 'risk_grade_calibration.md'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(md) + '\n')
print('[저장] output/risk_grade_calibration.md')

print('\n분기별 평균 위험지수:', pred.groupby(q)['risk_score'].mean().round(1).to_dict())
pred.to_parquet(os.path.join(WORK_DIR, 'pred_2024.parquet'), index=False)
print(f'[요약] 위험지수 {len(s):,}행, 중앙값 {s.median():.0f}, 등급(위험≥{GRADE_DANGER}/주의≥{GRADE_CAUTION}) 비율 '
      + str(pred['risk_grade'].value_counts(normalize=True).round(3).to_dict()))
