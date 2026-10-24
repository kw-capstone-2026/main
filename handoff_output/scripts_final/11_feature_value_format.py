"""화면 표시 기준: SHAP featureValue를 변수별로 어떤 단위·자릿수로 보여줄지 정리.
output/feature_value_format.csv (변수 32개 기준표), output/feature_value_format.md (설명 + 참고용 예시 코드)
예시 값은 2024년 4분기 실제 데이터(시연 3블록 우선)에서 뽑고, 아래 fmt()로 변환해 규칙과 일치하는지 확인함."""
import math
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from common import OUT_DIR, load_feature_cols, save_csv, setup_logging  # noqa: E402

setup_logging('11_feature_value_format')

# 표시 형식 종류
#   won: 원 단위 금액 / count: 정수 개수 / avg: 소수 1자리 개수(상권 평균) / pct: 이미 % 단위
#   share: 0~1 비율 → ×100 % / per100: 100명(세대)당 개수 / density: 점포 100개당 개수
#   months: 개월 / code: 소득 구간 / yoy: 작년 대비 증감 지표 / index: 단위 없는 지표
SPEC = {
    '당월_매출_금액': ('won', '', '이번 분기(3개월) 매출 합계', ''),
    '당월_매출_건수': ('count', '건', '이번 분기 결제 건수', ''),
    '점포_수_y': ('avg', '개', '상권 안 업종당 평균 점포 수 (상권 단위 값)', ''),
    '유사_업종_점포_수_y': ('avg', '개', '상권 평균 유사업종 점포 수 (상권 단위 값)', ''),
    '개업_율_y': ('pct', '%', '상권 평균 개업률 (이미 % 단위, 100을 곱하지 않음)', ''),
    '폐업_률_y': ('pct', '%', '상권 평균 폐업률 (이미 % 단위, 100을 곱하지 않음)', ''),
    '프랜차이즈_점포_수_y': ('avg', '개', '상권 평균 프랜차이즈 점포 수 (상권 단위 값)', ''),
    '프랜차이즈점포비율(%)': ('pct', '%', '상권 프랜차이즈 점포 비율 (이미 % 단위)', ''),
    '개인점포비율(%)': ('pct', '%', '상권 개인 점포 비율 (이미 % 단위)', ''),
    '상권_전체점포_수': ('count', '개', '상권 안 전체 점포 수', ''),
    '상권 내부 업종 점유율(%)': ('pct', '%', '유사업종 점포 수 ÷ 상권 전체 점포 수 × 100 (유사업종_점포비율과 같은 값)', ''),
    '운영_영업_개월_평균': ('months', '개월', '상권 영업 중 점포의 평균 영업 기간', ''),
    '폐업_영업_개월_평균': ('months', '개월', '상권 폐업 점포의 평균 영업 기간', ''),
    '유효_수요_전환율': ('index', '', '단위 없는 지표 (계산식 미확인, 숫자만 표시)', ''),
    '점포당_평균_매출': ('won', '', '점포 1곳당 이번 분기 평균 매출', ''),
    '전년_동기_대비_폐업_증감률': ('yoy', '', '(이번 분기 폐업 수 − 작년 같은 분기 폐업 수) ÷ (작년 같은 분기 폐업 수 + 1). 양수 = 증가, 음수 = 감소',
                         '0은 "0.0"으로 표시, 변화 없음이라는 뜻 (작년 자료가 없는 일부 블록도 0으로 채워져 있음)'),
    '소득_구간_코드': ('code', '구간', '상권 주민 소득 구간 (숫자가 클수록 소득이 높음, 최대 10)', '0은 "자료 없음"'),
    '상권_업종_적합도': ('share', '%', '상권 주민 지출 중 이 업종 관련 소비 비중 (예: 커피-음료는 여가·문화 지출 비율)', '0은 "해당 소비 항목 없음"'),
    '총_아파트_세대수': ('count', '세대', '상권 주변 아파트 세대 수', '0은 "아파트 없음"'),
    '아파트_평균_시가': ('won', '', '상권 주변 아파트 평균 시세', '0은 "아파트 없음"'),
    '총_직장_인구_수': ('count', '명', '상권 주변 직장인 수', ''),
    '남성_직장_인구_수': ('count', '명', '상권 주변 남성 직장인 수', ''),
    '여성_직장_인구_수': ('count', '명', '상권 주변 여성 직장인 수', ''),
    '직장인구_100명당_점포수': ('per100', '개', '직장인 100명당 이 업종 평균 점포 수', ''),
    '아파트_100세대당_점포수': ('per100', '개', '아파트 100세대당 이 업종 평균 점포 수', '0은 "아파트 없음"'),
    '유사업종_점포비율': ('pct', '%', '유사업종 점포 수 ÷ 상권 전체 점포 수 × 100', ''),
    '직장인구_100명당_유사업종수': ('per100', '개', '직장인 100명당 유사업종 점포 수', ''),
    '점포당_매출_밀도': ('won', '', '이번 분기 매출 ÷ 상권 업종당 평균 점포 수', ''),
    '직장인구_1인당_매출': ('won', '', '이번 분기 매출 ÷ 주변 직장인 수', ''),
    '아파트세대당_매출': ('won', '', '이번 분기 매출 ÷ 주변 아파트 세대 수', '0은 "아파트 없음"'),
    '집객시설_수': ('count', '개', '상권 주변 집객시설(학교·병원·관공서 등) 수', ''),
    '집객시설_밀도': ('density', '개', '집객시설 수 ÷ (상권 전체 점포 수 + 1). 화면에는 "점포 100개당 N개"로 표시', ''),
}
RULES = {
    'won': '1억 이상: 소수 1자리 "억 원" / 1만 이상: 반올림 "만 원"(천 단위 쉼표) / 1만 미만: "원"',
    'count': '1만 이상이고 단위가 "건"이면 소수 1자리 "만 건" / 그 외: 정수 + 천 단위 쉼표 + 단위',
    'avg': '소수 1자리 + "개"',
    'pct': '소수 1자리 + "%" (100을 곱하지 않음)',
    'share': '× 100 후 소수 1자리 + "%"',
    'per100': '소수 2자리 + "개"',
    'density': '× 100 후 소수 1자리, "점포 100개당 N개"',
    'months': '정수 + "개월"',
    'code': '정수 + "구간"',
    'yoy': '소수 2자리, 끝자리 0은 한 자리까지만 남김. 감소는 − 기호 (3.0 / 0.45 / −0.67)',
    'index': '소수 1자리, 단위 없음 (1만 이상은 천 단위 쉼표)',
}
ZERO_MISSING = {'소득_구간_코드': '자료 없음', '상권_업종_적합도': '해당 소비 항목 없음', '총_아파트_세대수': '아파트 없음',
                '아파트_평균_시가': '아파트 없음', '아파트_100세대당_점포수': '아파트 없음', '아파트세대당_매출': '아파트 없음'}


def _round(x):
    """JS Math.round와 같게 0.5는 올림."""
    return math.floor(x + 0.5)


def fmt(name, v):
    """참고용 예시 JS 코드(formatFeatureValue)와 같은 규칙. 예시 값 검증용."""
    kind, unit = SPEC[name][0], SPEC[name][1]
    if v is None or pd.isna(v):
        return '-'
    if v == 0 and name in ZERO_MISSING:
        return ZERO_MISSING[name]
    if kind == 'won':
        if abs(v) >= 1e8:
            return f'{v / 1e8:.1f}억 원'
        if abs(v) >= 1e4:
            return f'{_round(v / 1e4):,}만 원'
        return f'{_round(v):,}원'
    if kind == 'count':
        if unit == '건' and v >= 1e4:
            return f'{v / 1e4:.1f}만 건'
        return f'{_round(v):,}{unit}'
    if kind == 'avg':
        return f'{v:.1f}개'
    if kind == 'pct':
        return f'{v:.1f}%'
    if kind == 'share':
        return f'{v * 100:.1f}%'
    if kind == 'per100':
        return f'{v:.2f}개'
    if kind == 'density':
        return f'점포 100개당 {v * 100:.1f}개'
    if kind == 'months':
        return f'{_round(v)}개월'
    if kind == 'code':
        return f'{int(v)}구간'
    if kind == 'yoy':
        t = f'{abs(v):.2f}'
        t = t[:-1] if t.endswith('0') else t
        return ('−' if v < 0 else '') + t
    t = f'{v:,.1f}'
    return t[:-2] if abs(v) >= 1e4 and t.endswith('.0') else (t if abs(v) >= 1e4 else f'{v:.1f}')


feature_cols = load_feature_cols()
assert set(SPEC) == set(feature_cols)
labels = pd.read_csv(os.path.join(OUT_DIR, 'feature_labels_draft.csv'), encoding='utf-8-sig').set_index('name')['label']
final_path = os.path.join(OUT_DIR, 'feature_labels_final.csv')  # 팀 확정 표시명 (백엔드 database/feature_labels_final.csv와 같은 파일)
if os.path.exists(final_path):  # 확정 표시명이 있으면 그것을 씀
    labels = pd.read_csv(final_path, encoding='utf-8-sig').set_index('name')['label']
shap = pd.read_csv(os.path.join(OUT_DIR, 'shap_top5_2024_q4.csv'), encoding='utf-8-sig')
DEMO = ['경리단길북측', '연남동(홍대)', '성수역']
demo = shap[(shap['업종명'] == '커피-음료') & shap['상권명'].isin(DEMO)]
counts = shap['feature'].value_counts()

rows = []
for name in feature_cols:
    kind, unit, meaning, zero_note = SPEC[name]
    ex = demo[demo['feature'] == name]
    if ex.empty:
        ex = shap[shap['feature'] == name]
    if ex.empty:  # 4분기 Top5에 한 번도 안 나온 변수는 예시 생략
        raw, where = None, ''
    else:
        e = ex.iloc[0]
        raw, where = float(e['feature_value']), f'{e["상권명"]} · {e["업종명"]}'
    rows.append({
        'name': name, 'label': labels.get(name, ''), '형식': kind, '단위': unit or ('원' if kind == 'won' else ''),
        '의미': meaning, '표시_규칙': RULES[kind], '0일_때': zero_note,
        '예시_원래값': '' if raw is None else (f'{raw:.6g}' if abs(raw) < 1e6 else f'{raw:.0f}'),
        '예시_화면표시': '' if raw is None else fmt(name, raw), '예시_블록': where,
        '4분기_Top5_등장_횟수': int(counts.get(name, 0)),
    })
table = pd.DataFrame(rows)
save_csv(table, 'feature_value_format.csv')

# 포스터에 이미 쓴 표기와 같은지 확인
poster = {('경리단길북측', '점포당_평균_매출'): '852만 원', ('경리단길북측', '당월_매출_금액'): '1.7억 원',
          ('연남동(홍대)', '점포당_평균_매출'): '3,949만 원', ('연남동(홍대)', '당월_매출_건수'): '86.9만 건',
          ('성수역', '당월_매출_금액'): '28.5억 원', ('성수역', '점포당_평균_매출'): '5,000만 원',
          ('경리단길북측', '전년_동기_대비_폐업_증감률'): '3.0', ('연남동(홍대)', '전년_동기_대비_폐업_증감률'): '0.45',
          ('성수역', '전년_동기_대비_폐업_증감률'): '−0.67'}
ok = True
for (area, name), want in poster.items():
    v = float(demo[(demo['상권명'] == area) & (demo['feature'] == name)]['feature_value'].iloc[0])
    got = fmt(name, v)
    ok &= got == want
    print(f'  포스터 표기 확인 {area} {name}: {got} (포스터 {want}) {"OK" if got == want else "다름"}')
print('[확인] 포스터 표기와 규칙 일치' if ok else '[확인] 포스터 표기와 다른 항목 있음')

# 시연 3블록 화면 미리보기
preview = []
for area in DEMO:
    g = demo[demo['상권명'] == area].sort_values('rank')
    preview.append(f'**{area} · 커피-음료**\n')
    preview += [f'{int(r["rank"])}. {labels.get(r["feature"], r["feature"])}: {fmt(r["feature"], r["feature_value"])} '
                f'({"▲ 위험을 올림" if r["shap_value"] > 0 else "▼ 위험을 낮춤"} {r["shap_value"]:+.2f})' for _, r in g.iterrows()]
    preview.append('')

JS = """// [참고용 예시] featureValue 표시 규칙을 코드로 옮겨 본 것. 실제 프론트 코드 구조에 맞게 고쳐서 사용
const FORMAT = {
""" + '\n'.join(f"  '{n}': ['{SPEC[n][0]}', '{SPEC[n][1]}']," for n in feature_cols) + """
};
const ZERO_MISSING = {
""" + '\n'.join(f"  '{k}': '{v}'," for k, v in ZERO_MISSING.items()) + """
};

export function formatFeatureValue(name, v) {
  if (v === null || v === undefined || Number.isNaN(Number(v))) return '-';
  v = Number(v);
  if (v === 0 && ZERO_MISSING[name]) return ZERO_MISSING[name];
  const [kind, unit] = FORMAT[name] || ['index', ''];
  const comma = (x) => Math.round(x).toLocaleString('ko-KR');
  switch (kind) {
    case 'won':
      if (Math.abs(v) >= 1e8) return `${(v / 1e8).toFixed(1)}억 원`;
      if (Math.abs(v) >= 1e4) return `${comma(v / 1e4)}만 원`;
      return `${comma(v)}원`;
    case 'count':
      if (unit === '건' && v >= 1e4) return `${(v / 1e4).toFixed(1)}만 건`;
      return `${comma(v)}${unit}`;
    case 'avg': return `${v.toFixed(1)}개`;
    case 'pct': return `${v.toFixed(1)}%`;
    case 'share': return `${(v * 100).toFixed(1)}%`;
    case 'per100': return `${v.toFixed(2)}개`;
    case 'density': return `점포 100개당 ${(v * 100).toFixed(1)}개`;
    case 'months': return `${Math.round(v)}개월`;
    case 'code': return `${Math.trunc(v)}구간`;
    case 'yoy': {
      let t = Math.abs(v).toFixed(2);
      if (t.endsWith('0')) t = t.slice(0, -1);
      return (v < 0 ? '−' : '') + t;
    }
    default: return Math.abs(v) >= 1e4 ? v.toLocaleString('ko-KR', { maximumFractionDigits: 1 }) : v.toFixed(1);
  }
}
"""

md = [
    '# SHAP 실제 값(featureValue) 화면 표시 기준', '',
    '`/api/v1/blocks/{blockId}/shap` 응답의 `featureValue`는 원본 숫자 그대로임 (예: 8523048.2).',
    '화면에는 변수(`name`)마다 아래 규칙으로 단위와 자릿수를 붙여 보여주면 됨. 32개 전체 기준은 `feature_value_format.csv`에 있음.', '',
    '## 표시 형식 9가지', '',
    '| 형식 | 규칙 | 예시 |', '|---|---|---|',
    '| 금액 | 1억 이상 "X.X억 원" / 1만 이상 "N만 원" / 그 외 "N원" | 170460964 → 1.7억 원, 8523048 → 852만 원 |',
    '| 개수 | 정수 + 쉼표 + 단위. 결제 건수가 1만 이상이면 "X.X만 건" | 7886 → 7,886개, 868657 → 86.9만 건 |',
    '| 상권 평균 개수 | 소수 1자리 + "개" | 5.61 → 5.6개 |',
    '| 이미 % 인 값 | 소수 1자리 + "%" (**100을 곱하지 않음**) | 3.0 → 3.0% |',
    '| 0~1 비율 | × 100 후 "%" | 0.117 → 11.7% |',
    '| 100명(세대)당 | 소수 2자리 + "개" | 0.047 → 0.05개 |',
    '| 집객시설 밀도 | × 100 후 "점포 100개당 N개" | 0.0606 → 점포 100개당 6.1개 |',
    '| 개월·구간 | 정수 + "개월" / "구간" | 109 → 109개월, 8 → 8구간 |',
    '| 작년 대비 폐업 증감 | 소수 2자리, 끝자리 0은 한 자리까지 (양수 = 증가, 음수 = 감소에 − 표시) | 3.0 → 3.0, 0.45 → 0.45, −0.67 → −0.67 |', '',
    '## 0일 때 주의', '',
    '- 소득 구간, 업종 적합도, 아파트 관련 변수 4개(세대 수, 시세, 100세대당 점포 수, 세대당 매출), 모두 6개 변수는 0이 "값이 0"이 아니라 **자료 없음**에 가까움. 아래 예시 코드는 이 경우 "자료 없음", "해당 소비 항목 없음", "아파트 없음"으로 표시함.',
    '- 작년 대비 폐업 증감은 0이면 "0.0"으로 표시되며 "변화 없음"이라는 뜻임 (작년 자료가 없는 일부 블록도 0으로 들어가 있음).',
    '- 그 외 변수의 0은 실제 0이므로 그대로 표시함 (`value || "-"` 대신 `value ?? "-"` 사용).', '',
    '## 시연 3블록 미리보기 (확정 표시명 + 표시 규칙 적용)', '',
    *preview,
    '## 참고용 예시 코드', '',
    '> **주의:** 아래 코드는 표시 규칙을 이해하기 쉽게 코드로 옮겨 본 예시임. 실제 프론트 코드를 보고 작성한 것이 아니므로, 파일 구조·변수명·스타일에 맞게 자유롭게 고쳐서 사용하면 됨. 규칙만 같으면 구현 방식은 상관없음.', '',
    '```javascript', JS.rstrip(), '```', '',
    '## 참고', '',
    '- `유효_수요_전환율`은 계산식을 확인하지 못해 단위 없이 숫자만 표시함.',
    '- `상권 내부 업종 점유율(%)`과 `유사업종_점포비율`은 데이터상 같은 값임 (둘 다 유사업종 점포 수 ÷ 상권 전체 점포 수 × 100).',
    '- 4분기 위험 이유 Top5에 자주 나오는 변수: ' + ', '.join(f'{labels.get(n, n)}({c:,}회)' for n, c in counts.head(6).items()),
]
with open(os.path.join(OUT_DIR, 'feature_value_format.md'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(md) + '\n')
print('[저장] output/feature_value_format.md')
print('\n'.join(preview))
print(f'[요약] 표시 기준 {len(table)}개 변수, 포스터 표기 일치 {ok}')
