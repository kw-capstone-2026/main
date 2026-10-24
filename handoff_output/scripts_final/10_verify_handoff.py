"""최종 점검: 작업 요구사항을 결과 파일 기준으로 하나씩 자동 확인.
결과는 output/verification_report.md. 하나라도 실패하면 종료코드 1."""
import json
import os
import re
import subprocess
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from common import (DEMO_QUARTER, GRADE_CAUTION, GRADE_DANGER, LOG_PATH, OUT_DIR, ROOT,  # noqa: E402
                    load_feature_cols, setup_logging)

setup_logging('10_verify_handoff')
results = []


def check(step, name, ok, detail=''):
    results.append((step, name, bool(ok), detail))
    print(f'  [{"통과" if ok else "실패"}] {step} | {name}' + (f': {detail}' if detail else ''))


def read_csv(name):
    return pd.read_csv(os.path.join(OUT_DIR, name), encoding='utf-8-sig', dtype={'상권_코드': str})


feature_cols = load_feature_cols()

# ── 파일 존재·인코딩 ──
need = ['parquet_columns.txt', 'model_metrics.md', 'model_metrics.json', 'master_2024.csv', 'shap_top5_2024_q4.csv',
        'shap_top5_2024_q1_q3.csv', 'feature_labels_draft.csv', 'demo_candidates.csv', 'HOW_TO_REPRODUCE.md',
        'HANDOFF.md', 'run_log.txt', 'requirements_used.txt', 'demo_final_blocks.csv', 'risk_grade_calibration.md',
        'label_check.md', 'shap_importance_2024.csv', 'ablation_no_closure.md', 'ablation_no_closure.json', 'feature_value_format.csv', 'feature_value_format.md', 'feature_labels_final.csv']
missing = [f for f in need if not os.path.exists(os.path.join(OUT_DIR, f))]
check('공통', '필수 결과 파일 존재', not missing, f'누락: {missing}' if missing else f'{len(need)}개')
csvs = sorted(f for f in os.listdir(OUT_DIR) if f.endswith('.csv'))
no_bom = [f for f in csvs if open(os.path.join(OUT_DIR, f), 'rb').read(3) != b'\xef\xbb\xbf']
check('공통', '모든 CSV가 utf-8-sig(BOM)', not no_bom, f'{len(csvs)}개' if not no_bom else f'BOM 없음: {no_bom}')
scripts = sorted(f for f in os.listdir(os.path.join(ROOT, 'scripts_final')) if re.match(r'\d\d_.*\.py$', f))
check('공통', 'scripts_final 번호 스크립트 00~11', len(scripts) == 12, ', '.join(scripts))
log = open(LOG_PATH, encoding='utf-8').read()
check('공통', '실행 로그에 오류 없음', 'Traceback' not in log and '[중단]' not in log)

# ── 0단계 ──
req = open(os.path.join(OUT_DIR, 'requirements_used.txt'), encoding='utf-8').read()
pk = {k: re.search(rf'^{k}==(\S+)', req, re.M) for k in ['pandas', 'pyarrow', 'xgboost', 'lightgbm', 'shap', 'scikit-learn']}
check('0 환경', '필수 패키지 6개 설치', all(pk.values()), ', '.join(f'{k} {v.group(1)}' for k, v in pk.items() if v))
check('0 환경', 'xgboost가 모델 저장 버전(3.2.0)과 같음', pk['xgboost'] and pk['xgboost'].group(1) == '3.2.0')
check('0 환경', '모델 로드 경고 없음', '모델 로드 경고: 없음' in log)

# ── 1단계 ──
m = read_csv('master_2024.csv')
check('1 데이터', '2024년 행 수 87,179', len(m) == 87_179, f'{len(m):,}')
check('1 데이터', '정답=1 행 수 2,705', int(m['과포화_위험_여부'].sum()) == 2_705, f'{int(m["과포화_위험_여부"].sum()):,}')
check('1 데이터', '분기 20241~20244만 포함', sorted(m['기준_년분기_코드'].unique()) == [20241, 20242, 20243, 20244])
check('1 데이터', '(상권, 업종, 분기) 키 유일', not m.duplicated(['상권_코드', '서비스_업종_코드', '기준_년분기_코드']).any())
check('1 데이터', 'parquet_columns.txt에 126개 열', open(os.path.join(OUT_DIR, 'parquet_columns.txt'), encoding='utf-8').read().count('\n') == 127)
check('1 데이터', '_x/_y 이름 열 비교 결과가 로그에 있음', '상권_코드_명_x vs _y: 불일치 0행' in log and '상권_구분_코드_명_x vs _y: 불일치 0행' in log)

# ── 2~3단계 ──
check('2 전처리', '입력 행렬 (87,179 × 32)', '입력 행렬 shape: (87179, 32)' in log)
check('3 예측', '최종 확률 = 0.3×XGB + 0.7×LGB',
      np.allclose(m['prob_final'], 0.3 * m['prob_xgb'] + 0.7 * m['prob_lgb'], atol=2e-6))

# ── 4단계 ──
met = json.load(open(os.path.join(OUT_DIR, 'model_metrics.json'), encoding='utf-8'))
exp = {'roc_auc': (0.909, .005), 'pr_auc': (0.317, .005), 'precision': (0.137, .01), 'recall': (0.842, .01),
       'f1': (0.236, .01), 'accuracy': (0.831, .01)}
for k, (e, t) in exp.items():
    check('4 검증', f'{k} {met["ensemble"][k]} (기대 {e} ± {t})', abs(met['ensemble'][k] - e) <= t)
check('4 검증', '단독 ROC-AUC XGB 0.9076 / LGB 0.9089',
      abs(met['xgb_only']['roc_auc'] - 0.9076) < 5e-4 and abs(met['lgb_only']['roc_auc'] - 0.9089) < 5e-4)

# ── 5단계 ──
p = m['prob_final'].clip(1e-4, 1 - 1e-4)
expect_score = np.rint(np.clip(50 + 15 * np.log(p / (1 - p)), 0, 100)).astype(int)
# prob_final은 소수 6자리로 반올림 저장되어 경계에서 1점 차이가 날 수 있음
check('5 위험지수', '공식 재계산과 일치 (반올림 오차 1점 이내)', (np.abs(expect_score - m['risk_score']) <= 1).all(),
      f'정확히 일치 {np.mean(expect_score == m["risk_score"]):.4%}')
g = np.where(m['risk_score'] >= GRADE_DANGER, '위험', np.where(m['risk_score'] >= GRADE_CAUTION, '주의', '안전'))
check('5 위험지수', f'등급 = 위험≥{GRADE_DANGER} / 주의≥{GRADE_CAUTION} / 안전', (g == m['risk_grade']).all())
cand = read_csv('demo_candidates.csv')
check('5 위험지수', '시연 후보 고·중·저 각 10개', cand['tier'].value_counts().to_dict() == {'고위험': 10, '중간': 10, '저위험': 10})
check('5 위험지수', '시연 후보 점포 수 ≥ 5', (cand['점포_수_x'] >= 5).all() and (cand['점포_수_y'] >= 5).all())
fin = read_csv('demo_final_blocks.csv')
check('5 위험지수', '확정 시연 블록 3개 등급이 위험/주의/안전', list(fin['risk_grade']) == ['위험', '주의', '안전'],
      ' / '.join(f'{r.상권명} {r.risk_score}' for r in fin.itertuples()))

# ── 6단계 ──
s4 = read_csv('shap_top5_2024_q4.csv')
n_q4 = int((m['기준_년분기_코드'] == DEMO_QUARTER).sum())
check('6 SHAP', 'Q4 블록 전부 × 5줄', len(s4) == n_q4 * 5 and s4['row_id'].nunique() == n_q4, f'{len(s4):,}줄 / {n_q4:,}블록')
check('6 SHAP', '블록마다 rank 1~5', (s4.groupby('row_id')['rank'].apply(lambda r: sorted(r) == [1, 2, 3, 4, 5])).all())
desc = s4.assign(a=s4['shap_value'].abs()).groupby('row_id')['a'].apply(lambda a: (np.diff(a.to_numpy()) <= 1e-9).all())
check('6 SHAP', '|SHAP| 큰 순서로 정렬', desc.all())
check('6 SHAP', 'shap_value·feature_value 열 존재', {'shap_value', 'feature_value', 'feature'} <= set(s4.columns))
s13 = read_csv('shap_top5_2024_q1_q3.csv')
check('6 SHAP', 'Q1~Q3 파일 블록 수', s13['row_id'].nunique() == len(m) - n_q4, f'{s13["row_id"].nunique():,}블록')
check('6 SHAP', 'SHAP 가법성 오차 < 1e-3 (로그)', all(float(x) < 1e-3 for x in re.findall(r'최대 ([0-9.]+e-\d+)', log)))
lab = read_csv('feature_labels_draft.csv')
check('6 SHAP', '표시명 초안 32개 = 모델 변수', list(lab['name']) == feature_cols and (lab['status'] == '초안(검토 필요)').all())

# ── 추가 실험 ──
ab = json.load(open(os.path.join(OUT_DIR, 'ablation_no_closure.json'), encoding='utf-8'))
check('추가 실험', '기준 재학습이 시연 모델 성능 재현 (ROC-AUC 차이 < 0.005)',
      abs(ab['retrain_full']['roc_auc'] - met['ensemble']['roc_auc']) < 0.005, f"{ab['retrain_full']['roc_auc']} vs {met['ensemble']['roc_auc']}")
check('추가 실험', '폐업 변수 제외 결과 기록 (29개 변수)', ab['retrain_no_closure']['n_features'] == 29, f"ROC-AUC {ab['retrain_no_closure']['roc_auc']}")
check('인수인계', 'HANDOFF: 사용 모델 = 모델 A 통일 명시', '모델 A 하나로 통일' in open(os.path.join(OUT_DIR, 'HANDOFF.md'), encoding='utf-8').read())

# ── 인수인계 패키지 ──
spec_cols = ['기준_년분기_코드', '상권_코드', '상권명', '상권_구분', '서비스_업종_코드', '업종명', 'lat', 'lon', '과포화_위험_여부',
             'prob_xgb', 'prob_lgb', 'prob_final', 'risk_score', 'risk_grade', '폐업_률_y', '개업_율_y', '점포_수_y',
             '상권_내부_업종_점유율', '운영_영업_개월_평균']
miss = [c for c in spec_cols if c not in m.columns]
check('인수인계', '(a) master 지시 열 전부 (risk_grade_draft → 확정 후 risk_grade)', not miss, f'누락 {miss}' if miss else '')
check('인수인계', '(a) risk_score 정수 0~100', m['risk_score'].dtype.kind == 'i' and m['risk_score'].between(0, 100).all())
h = open(os.path.join(OUT_DIR, 'HANDOFF.md'), encoding='utf-8').read()
musts = {
    '음슴체': '함.' in h or '임.' in h,
    '확정된 결정 1 원문': '예측 단위는 "상권 × 업종". DB의 한 줄(블록) = 상권 하나 × 업종 하나.' in h,
    '확정된 결정 2 원문': '임시 시안: 70점 이상 위험 / 40~70 주의 / 40 미만 안전.' in h,
    '확정된 결정 3 원문': '옛 설계 항목(생존곡선 survival_curve, 6개월 생존확률 survival_6m, 안전지수 csi_score)은 만들지 않는다.' in h,
    'SHAP log-odds 한 줄': 'log-odds 기준' in h,
    '시연 사례 선택 주의': '시연용 선택' in h and '모델이 전부 맞힌다는 뜻이 아님' in h,
    '2024 = 처음 보는 데이터': '2019~2023' in h and '처음 보는' in h,
    '[7] 요약표 규격': 'summary_by_industry.csv' in h and 'summary_by_quarter.csv' in h,
    '[8] DB CSV 4종 + 적재 순서': all(x in h for x in ['blocks.csv', 'predictions.csv', 'shap_features.csv', 'industry_stats.csv',
                                                 'blocks → predictions → shap_features → industry_stats']),
    '백엔드 대조표': 'schema.sql' in h and 'origin/feature/backend-api' in h,
    '포스터 수치·그림 목록': 'docs/0603_report/image' in h,
    '예시 행': '3110084' in h,
}
for k, v in musts.items():
    check('인수인계', f'(e) HANDOFF: {k}', v)

# ── 안전 규칙 ──
leaked = []
for f in os.listdir(OUT_DIR):
    if f.endswith(('.md', '.txt', '.json')):
        t = open(os.path.join(OUT_DIR, f), encoding='utf-8', errors='ignore').read()
        if re.search(r'(?i)(serviceKey|api[_-]?key|secret)\s*[=:]\s*\S{8,}', t):
            leaked.append(f)
check('규칙', '결과 문서에 API 키 형태 문자열 없음', not leaked, str(leaked))
me = os.path.basename(__file__)  # 이 점검 코드 자체는 '.env' 글자를 포함하므로 제외
src = ''.join(open(os.path.join(ROOT, 'scripts_final', f), encoding='utf-8').read()
              for f in os.listdir(os.path.join(ROOT, 'scripts_final')) if f.endswith('.py') and f != me)
check('규칙', '스크립트가 .env를 열지 않음', "'.env'" not in src and '".env"' not in src)
st = subprocess.run(['git', 'status', '--porcelain'], cwd=ROOT, capture_output=True, text=True, encoding='utf-8').stdout
# 우리가 만든 결과물 폴더(output/, scripts_final/, handoff_output/)는 git에 올라간 뒤 다시 갱신될 수 있으므로 제외
changed = [l for l in st.splitlines() if not l.startswith('??') and not l[3:].startswith(('output/', 'scripts_final/', 'handoff_output/'))]
check('규칙', '원래 프로젝트 파일 수정 없음 (결과물 폴더 output/, scripts_final/, handoff_output/ 제외)', not changed, '; '.join(changed[:5]))

# ── 보고서 ──
n_ok = sum(r[2] for r in results)
md = ['# 최종 점검 결과 (작업 요구사항 자동 확인)', '',
      f'- 점검 항목 {len(results)}개 중 **{n_ok}개 통과**' + ('' if n_ok == len(results) else f', **{len(results) - n_ok}개 실패**'),
      '- 생성: `scripts_final/10_verify_handoff.py` (다시 실행하면 다시 확인됨)', '',
      '| 단계 | 항목 | 결과 | 내용 |', '|---|---|---|---|',
      *[f'| {a} | {b} | {"통과" if c else "**실패**"} | {d} |' for a, b, c, d in results]]
with open(os.path.join(OUT_DIR, 'verification_report.md'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(md) + '\n')
print(f'[저장] output/verification_report.md')
print(f'[요약] 점검 {len(results)}개 중 {n_ok}개 통과')
if n_ok != len(results):
    sys.exit('[중단] 실패 항목 있음')
