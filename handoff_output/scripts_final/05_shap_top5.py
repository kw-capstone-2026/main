"""6단계: XGBoost TreeExplainer로 SHAP 계산 → 행마다 |SHAP| 상위 5개 (long 형식). 한글 표시명 초안 생성."""
import os
import sys
import time

import numpy as np
import pandas as pd
import shap
from xgboost import XGBClassifier

sys.path.insert(0, os.path.dirname(__file__))
from common import DEMO_QUARTER, WORK_DIR, XGB_PATH, load_feature_cols, save_csv, setup_logging  # noqa: E402

CHUNK = 10_000
TOP_K = 5
Q1_Q3_TIME_LIMIT_SEC = 600  # Q4 소요시간으로 Q1~Q3 예상시간이 이 값을 넘으면 생략

# 한글 표시명 초안 (20자 이내, 사람이 검토 후 수정할 것)
# '상권 ~'으로 시작하는 변수는 같은 상권 안 모든 업종이 같은 값 (상권 단위 값)
FEATURE_LABELS = {
    '당월_매출_금액': '이번 분기 매출액',
    '당월_매출_건수': '이번 분기 결제 건수',
    '점포_수_y': '상권 업종당 평균 점포 수',
    '유사_업종_점포_수_y': '상권 평균 유사업종 점포 수',
    '개업_율_y': '상권 평균 개업률',
    '폐업_률_y': '상권 평균 폐업률',
    '프랜차이즈_점포_수_y': '상권 평균 프랜차이즈 점포 수',
    '프랜차이즈점포비율(%)': '상권 프랜차이즈 점포 비율',
    '개인점포비율(%)': '상권 개인 가게 비율',
    '상권_전체점포_수': '상권 전체 점포 수',
    '상권 내부 업종 점유율(%)': '상권 평균 업종 점유율',
    '운영_영업_개월_평균': '상권 가게 평균 영업기간',
    '폐업_영업_개월_평균': '상권 폐업 가게 평균 영업기간',
    '유효_수요_전환율': '유동인구 대비 실제 결제 비율',
    '점포당_평균_매출': '가게당 평균 매출',
    '전년_동기_대비_폐업_증감률': '작년 같은 분기보다 폐업이 늘어난 정도',
    '소득_구간_코드': '주변 주민 소득 수준',
    '상권_업종_적합도': '상권과 업종의 어울림 정도',
    '총_아파트_세대수': '주변 아파트 세대 수',
    '아파트_평균_시가': '주변 아파트 평균 시세',
    '총_직장_인구_수': '주변 직장인 수',
    '남성_직장_인구_수': '주변 남성 직장인 수',
    '여성_직장_인구_수': '주변 여성 직장인 수',
    '직장인구_100명당_점포수': '직장인 100명당 점포 수',
    '아파트_100세대당_점포수': '아파트 100세대당 점포 수',
    '유사업종_점포비율': '상권 유사업종 점포 비중',
    '직장인구_100명당_유사업종수': '직장인 100명당 유사업종 수',
    '점포당_매출_밀도': '가게당 매출 밀도',
    '직장인구_1인당_매출': '직장인 1명당 매출',
    '아파트세대당_매출': '아파트 1세대당 매출',
    '집객시설_수': '주변 집객시설 수',
    '집객시설_밀도': '주변 집객시설 밀집도',
}

setup_logging('05_shap_top5')
np.random.seed(42)

feature_cols = load_feature_cols()
assert set(FEATURE_LABELS) == set(feature_cols)
for k, v in FEATURE_LABELS.items():
    if len(v) > 20:
        print(f'[주의] 표시명 20자 초과({len(v)}자, 공백 포함): {k} → {v}')

df = pd.read_parquet(os.path.join(WORK_DIR, 'test_2024.parquet'))
X = pd.read_parquet(os.path.join(WORK_DIR, 'X_2024.parquet'))
model = XGBClassifier()
model.load_model(XGB_PATH)
explainer = shap.TreeExplainer(model)
# shap 0.54는 expected_value를 첫 계산 이후에 채우므로 한 행을 먼저 계산한 뒤 읽는다
explainer.shap_values(X.iloc[:1])
base_value = float(np.ravel(explainer.expected_value)[0])
print(f'SHAP 기준값(expected_value, log-odds): {base_value:.4f}')


def compute_shap(idx, tag):
    out = np.empty((len(idx), len(feature_cols)), dtype=np.float32)
    t0 = time.time()
    for s in range(0, len(idx), CHUNK):
        part = X.iloc[idx[s:s + CHUNK]]
        out[s:s + len(part)] = explainer.shap_values(part)
        print(f'  [{tag}] {min(s + CHUNK, len(idx)):,}/{len(idx):,}행 ({time.time() - t0:.1f}초)')
    # 검증: 기준값 + SHAP 합 = XGBoost log-odds (원래 마진)
    margin = model.get_booster().inplace_predict(X.iloc[idx], predict_type='margin')
    err = np.abs(out.sum(1) + base_value - margin).max()
    print(f'  [{tag}] 가법성 검증: |기준값+ΣSHAP − log-odds| 최대 {err:.2e}')
    if err > 1e-3:
        sys.exit(f'[중단] SHAP 가법성 오차가 큼 ({err:.2e})')
    return out, time.time() - t0


def top_k_long(sv, idx):
    order = np.argsort(-np.abs(sv), axis=1, kind='stable')[:, :TOP_K]
    rows = np.repeat(np.arange(len(idx)), TOP_K)
    cols = order.ravel()
    meta = df.iloc[idx].reset_index().rename(columns={'index': 'row_id'})
    long = pd.DataFrame({
        'row_id': meta['row_id'].to_numpy()[rows],
        '기준_년분기_코드': meta['기준_년분기_코드'].to_numpy()[rows],
        '상권_코드': meta['상권_코드'].to_numpy()[rows],
        '서비스_업종_코드': meta['서비스_업종_코드'].to_numpy()[rows],
        '상권명': meta['상권_코드_명_x'].to_numpy()[rows],
        '업종명': meta['서비스_업종_코드_명_x'].to_numpy()[rows],
        'rank': np.tile(np.arange(1, TOP_K + 1), len(idx)),
        'feature': np.array(feature_cols)[cols],
        'label_draft': [FEATURE_LABELS[feature_cols[c]] for c in cols],
        'shap_value': np.round(sv[rows, cols], 6),
        'feature_value': X.to_numpy()[np.asarray(idx)[rows], cols],
    })
    return long


q = df['기준_년분기_코드'].to_numpy()
idx_q4 = np.flatnonzero(q == DEMO_QUARTER)
sv_q4, sec_q4 = compute_shap(idx_q4, '20244')
long_q4 = top_k_long(sv_q4, idx_q4)
save_csv(long_q4, 'shap_top5_2024_q4.csv')
assert len(long_q4) == len(idx_q4) * TOP_K

all_sv, all_idx = [sv_q4], [idx_q4]
idx_rest = np.flatnonzero(q < DEMO_QUARTER)
est = sec_q4 * len(idx_rest) / max(len(idx_q4), 1)
print(f'Q4 소요 {sec_q4:.0f}초 → Q1~Q3({len(idx_rest):,}행) 예상 {est:.0f}초')
if est <= Q1_Q3_TIME_LIMIT_SEC:
    sv_rest, _ = compute_shap(idx_rest, '20241~20243')
    save_csv(top_k_long(sv_rest, idx_rest), 'shap_top5_2024_q1_q3.csv')
    all_sv.append(sv_rest)
    all_idx.append(idx_rest)
else:
    print(f'[생략] Q1~Q3 SHAP: 예상 시간이 {Q1_Q3_TIME_LIMIT_SEC}초 초과')

sv_all = np.vstack(all_sv)
mean_abs = pd.Series(np.abs(sv_all).mean(0), index=feature_cols).sort_values(ascending=False)
scope = '2024년 전체' if len(all_sv) > 1 else '20244'
share = mean_abs / mean_abs.sum()
gain = pd.Series(model.get_booster().get_score(importance_type='total_gain')).reindex(feature_cols).fillna(0)
gain_share = gain / gain.sum()
rank1 = long_q4.loc[long_q4['rank'] == 1, 'feature'].value_counts(normalize=True)
in_top5 = long_q4['feature'].value_counts() / len(idx_q4)
print(f'\n★ 평균 |SHAP| 상위 10개 ({scope}, {len(sv_all):,}행, XGBoost log-odds 기준)')
print(f'  {"순위":<4}{"변수":<28}{"평균|SHAP|":>11}{"SHAP 비중":>10}{"XGB gain 비중":>14}{"Q4 1위 비율":>12}{"Q4 Top5 포함":>13}')
for i, (k, v) in enumerate(mean_abs.head(10).items(), 1):
    print(f'  {i:<4}{k:<28}{v:>11.4f}{share[k]:>10.1%}{gain_share[k]:>14.1%}{rank1.get(k, 0):>12.1%}{in_top5.get(k, 0):>13.1%}')
top = mean_abs.index[0]
print(f'★ 1위 변수 "{top}"의 비중: SHAP 기준 {share[top]:.1%}, XGBoost gain 기준 {gain_share[top]:.1%}, '
      f'20244 블록의 {rank1.get(top, 0):.1%}에서 위험 이유 1위')
imp = pd.DataFrame({
    'rank': range(1, len(mean_abs) + 1), 'feature': mean_abs.index,
    'label_draft': [FEATURE_LABELS[k] for k in mean_abs.index],
    'mean_abs_shap': mean_abs.round(4).to_numpy(), 'shap_share_pct': (share * 100).round(1).to_numpy(),
    'xgb_gain_share_pct': (gain_share[mean_abs.index] * 100).round(1).to_numpy(),
    'q4_rank1_pct': [round(rank1.get(k, 0) * 100, 1) for k in mean_abs.index],
    'q4_in_top5_pct': [round(in_top5.get(k, 0) * 100, 1) for k in mean_abs.index],
})
save_csv(imp, 'shap_importance_2024.csv')

labels = pd.DataFrame({'name': feature_cols, 'label': [FEATURE_LABELS[c] for c in feature_cols],
                       'status': '초안(검토 필요)'})
save_csv(labels, 'feature_labels_draft.csv')
print(f'[요약] SHAP Top5 20244: {len(idx_q4):,}행 → {len(long_q4):,}줄, 기준값 {base_value:.4f}')
