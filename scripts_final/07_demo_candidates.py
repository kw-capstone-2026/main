"""5단계 후속: 20244 기준 시연용 후보 고·중·저 각 10개 → output/demo_candidates.csv (사람이 최종 선택)."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from common import DEMO_QUARTER, GRADE_CAUTION, GRADE_DANGER, OUT_DIR, save_csv, setup_logging  # noqa: E402

# ── 후보 선정 기준 (바꾸려면 여기만 수정) ──
TIER_HIGH = GRADE_DANGER   # 고위험: 위험 등급 (≥75)
TIER_LOW = GRADE_CAUTION   # 저위험: 안전 등급 (<50), 그 사이는 중간(주의)
MIN_STORES = 5          # 점포_수_y ≥ 5 (지시) 이고 점포_수_x ≥ 5 (이 블록의 실제 점포 수)
N_PER_TIER = 10
# 같은 업종을 고·중·저 상권에서 비교하는 시연 시나리오 ("카페를 차린다면 어디?")
SCENARIO_INDUSTRY = '커피-음료'
N_SCENARIO = 5
# 최종 시연 블록 3개 (2026-10-20 선정, 같은 업종 시나리오에서 고름)
# 선정 이유: 누구나 아는 카페 상권, 등급별 정답과 일치(위험=1, 안전=0), 주의는 4개 분기 내내 주의 구간,
# 동네 이미지(경리단길 쇠퇴·연남동 경쟁·성수 성장)와 모델 결과가 맞아 설명이 자연스러움
DEMO_FINAL = [
    ('위험', '3110084', 'CS100010'),  # 경리단길북측 · 커피-음료
    ('주의', '3120104', 'CS100010'),  # 연남동(홍대) · 커피-음료
    ('안전', '3120052', 'CS100010'),  # 성수역 · 커피-음료
]
MAX_PER_INDUSTRY = 2    # 한 등급 안에서 같은 업종 최대 개수
# 이름 알아보기 쉬움 점수: 대표 지명 2점, '역'·'시장' 포함 1점
FAMOUS = ['강남', '홍대', '명동', '신촌', '이태원', '건대', '성수', '잠실', '여의도', '종로', '압구정', '가로수길',
          '연남', '망원', '익선', '북촌', '삼청', '동대문', '남대문', '광장시장', '경리단', '서촌', '을지로', '인사동',
          '합정', '상수', '신림', '노량진', '왕십리', '혜화', '대학로', '용산', '청담', '선릉', '역삼', '사당',
          '영등포', '문래', '통인시장', '경동시장', '관광특구', '서울대입구', '고속터미널', '신사', '청량리']

setup_logging('07_demo_candidates')

m = pd.read_csv(os.path.join(OUT_DIR, 'master_2024.csv'), encoding='utf-8-sig', dtype={'상권_코드': str})
shap = pd.read_csv(os.path.join(OUT_DIR, 'shap_top5_2024_q4.csv'), encoding='utf-8-sig')
d = m[m['기준_년분기_코드'] == DEMO_QUARTER].copy()
print(f'20244 전체 {len(d):,}행')
d = d[(d['점포_수_y'] >= MIN_STORES) & (d['점포_수_x'] >= MIN_STORES)]
print(f'점포 수 필터(점포_수_y ≥ {MIN_STORES} 그리고 점포_수_x ≥ {MIN_STORES}) 후 {len(d):,}행')

d['name_score'] = d['상권명'].apply(lambda s: 2 if any(k in s for k in FAMOUS) else (1 if ('역' in s or '시장' in s) else 0))
d['tier'] = pd.cut(d['risk_score'], [-1, TIER_LOW - 1, TIER_HIGH - 1, 100], labels=['저위험', '중간', '고위험']).astype(str)
print('등급별 후보 풀:', d['tier'].value_counts().to_dict())

top = shap.pivot(index='row_id', columns='rank', values='feature')
top.columns = [f'shap_top{c}' for c in top.columns]
lab = shap.pivot(index='row_id', columns='rank', values='label_draft')
d = d.join(top, on='row_id').assign(shap_top5_labels=d['row_id'].map(lab.apply(' / '.join, axis=1)))


def pick(pool, n):
    """상권_구분을 돌아가며 하나씩 고르고, 같은 상권은 1번, 같은 업종은 MAX_PER_INDUSTRY번까지만."""
    queues = {k: g for k, g in pool.groupby('상권_구분', sort=False)}
    order = sorted(queues, key=lambda k: -len(queues[k]))
    chosen, used_area, ind_cnt = [], set(), {}
    pos = {k: 0 for k in order}
    while len(chosen) < n and any(pos[k] < len(queues[k]) for k in order):
        for k in order:
            g = queues[k]
            while pos[k] < len(g):
                r = g.iloc[pos[k]]
                pos[k] += 1
                if r['상권_코드'] in used_area or ind_cnt.get(r['업종명'], 0) >= MAX_PER_INDUSTRY:
                    continue
                chosen.append(r)
                used_area.add(r['상권_코드'])
                ind_cnt[r['업종명']] = ind_cnt.get(r['업종명'], 0) + 1
                break
            if len(chosen) >= n:
                break
    return pd.DataFrame(chosen)


tiers = []
for tier, sort_cols, asc in [
    ('고위험', ['answer_pref', 'name_score', 'risk_score'], [False, False, False]),
    ('중간', ['name_score', 'mid_dist'], [False, True]),
    ('저위험', ['answer_pref', 'name_score', 'risk_score'], [False, False, True]),
]:
    pool = d[d['tier'] == tier].copy()
    # 고위험은 정답=1 우선, 저위험은 정답=0 우선
    pool['answer_pref'] = (pool['과포화_위험_여부'] == 1) if tier == '고위험' else (pool['과포화_위험_여부'] == 0)
    pool['mid_dist'] = (pool['risk_score'] - (TIER_HIGH + TIER_LOW) / 2).abs()
    pool = pool.sort_values(sort_cols, ascending=asc, kind='stable')
    sel = pick(pool, N_PER_TIER).sort_values(['name_score'], ascending=False, kind='stable')
    tiers.append(sel)

out = pd.concat(tiers, ignore_index=True)
out['정답_일치'] = out.apply(lambda r: ('O' if r['과포화_위험_여부'] == 1 else 'X') if r['tier'] == '고위험'
                          else ('O' if r['과포화_위험_여부'] == 0 else 'X') if r['tier'] == '저위험' else '-', axis=1)
out['이름_알아보기_점수'] = out['name_score']
out.insert(0, '후보_순번', out.groupby('tier').cumcount() + 1)
cols = ['tier', '후보_순번', '상권명', '업종명', 'risk_score', 'risk_grade', 'prob_final', '과포화_위험_여부', '정답_일치',
        '상권_구분', '점포_수_x', '점포_수_y', '이름_알아보기_점수', 'shap_top1', 'shap_top2', 'shap_top3', 'shap_top4',
        'shap_top5', 'shap_top5_labels', '상권_코드', '서비스_업종_코드', 'row_id', 'lat', 'lon']
out = out[cols]
save_csv(out, 'demo_candidates.csv')
pd.set_option('display.width', 250)
for t, g in out.groupby('tier', sort=False):
    print(f'\n[{t}]  상권구분 {g["상권_구분"].value_counts().to_dict()}  정답일치 {g["정답_일치"].value_counts().to_dict()}')
    print(g[['후보_순번', '상권명', '업종명', 'risk_score', '과포화_위험_여부', '정답_일치', '상권_구분', '점포_수_x', 'shap_top1']]
          .to_string(index=False))
print(f'\n[요약] 후보 {len(out)}개 (고위험 {sum(out.tier == "고위험")}, 중간 {sum(out.tier == "중간")}, 저위험 {sum(out.tier == "저위험")})')

# ── 같은 업종 시나리오: 한 업종을 고·중·저 상권에서 비교 ──
sc = d[d['업종명'] == SCENARIO_INDUSTRY].copy()
sc['answer_pref'] = np.where(sc['tier'] == '고위험', sc['과포화_위험_여부'] == 1,
                             np.where(sc['tier'] == '저위험', sc['과포화_위험_여부'] == 0, True))
sc['mid_dist'] = (sc['risk_score'] - (TIER_HIGH + TIER_LOW) / 2).abs()
sc['low_dist'] = (sc['risk_score'] - 15).abs()  # 저위험은 0점보다 10~20점대가 화면에서 자연스러움
parts = []
for tier, key, asc in [('고위험', 'risk_score', False), ('중간', 'mid_dist', True), ('저위험', 'low_dist', True)]:
    g = sc[sc['tier'] == tier].sort_values(['answer_pref', 'name_score', key], ascending=[False, False, asc], kind='stable')
    parts.append(g.head(N_SCENARIO))
scen = pd.concat(parts, ignore_index=True)
scen['정답_일치'] = np.where(scen['tier'] == '고위험', np.where(scen['과포화_위험_여부'] == 1, 'O', 'X'),
                         np.where(scen['tier'] == '저위험', np.where(scen['과포화_위험_여부'] == 0, 'O', 'X'), '-'))
scen['이름_알아보기_점수'] = scen['name_score']
scen.insert(0, '후보_순번', scen.groupby('tier').cumcount() + 1)
scen = scen[cols]
save_csv(scen, 'demo_scenario_same_industry.csv')
print(f'\n[같은 업종 시나리오: {SCENARIO_INDUSTRY}]')
for t, g in scen.groupby('tier', sort=False):
    print(f'  [{t}] ' + ' | '.join(f'{r.상권명}({r.risk_score}, 정답{r.과포화_위험_여부})' for r in g.itertuples()))

# ── 최종 시연 블록 3개: 4개 분기 점수 추이 + 위험 이유 Top5(값 포함) ──
trend = m.pivot_table(index=['상권_코드', '서비스_업종_코드'], columns='기준_년분기_코드', values='risk_score')
rows = []
for role, area, ind in DEMO_FINAL:
    r = m[(m['기준_년분기_코드'] == DEMO_QUARTER) & (m['상권_코드'] == area) & (m['서비스_업종_코드'] == ind)]
    assert len(r) == 1, (area, ind)
    r = r.iloc[0]
    assert r['risk_grade'] == role, f'{r["상권명"]}: 등급 {r["risk_grade"]} ≠ 의도 {role}'
    top = shap[shap['row_id'] == r['row_id']].sort_values('rank')
    rows.append({
        '역할': role, '상권명': r['상권명'], '업종명': r['업종명'], '상권_구분': r['상권_구분'],
        'risk_score': r['risk_score'], 'risk_grade': r['risk_grade'], '과포화_위험_여부': r['과포화_위험_여부'],
        '점수_추이_2024Q1~Q4': ' → '.join(str(int(v)) for v in trend.loc[(area, ind)].to_numpy()),
        '점포_수_x': r['점포_수_x'], '폐업_률_x': r['폐업_률_x'], '개업_율_x': r['개업_율_x'],
        **{f'이유{k}': f'{t.label_draft} ({"위험↑" if t.shap_value > 0 else "위험↓"} {t.shap_value:+.2f}, 값 {t.feature_value:,.2f})'
           for k, t in enumerate(top.itertuples(), 1)},
        '상권_코드': area, '서비스_업종_코드': ind, 'row_id': r['row_id'], 'lat': r['lat'], 'lon': r['lon'],
    })
final = pd.DataFrame(rows)
save_csv(final, 'demo_final_blocks.csv')
print('\n[최종 시연 블록]')
for _, r in final.iterrows():
    print(f'  {r["역할"]}: {r["상권명"]} · {r["업종명"]}  {r["risk_score"]}점 (정답 {r["과포화_위험_여부"]}, '
          f'추이 {r["점수_추이_2024Q1~Q4"]})  1위 이유: {r["이유1"]}')
