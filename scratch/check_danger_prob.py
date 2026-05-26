import pandas as pd
import numpy as np
from xgboost import XGBClassifier

data_path = 'data/parquet_datas/final_merged_commercial_data_v5.parquet'
df = pd.read_parquet(data_path)
df['기준_년분기_코드'] = pd.to_numeric(df['기준_년분기_코드'], errors='coerce')
target_col = '과포화_위험_여부'
feature_cols = [
    '당월_매출_금액', '당월_매출_건수', '점포_수_y', '유사_업종_점포_수_y',
    '개업_율_y', '폐업_률_y', '프랜차이즈_점포_수_y', '프랜차이즈점포비율(%)', '개인점포비율(%)',
    '상권_전체점포_수', '상권 내부 업종 점유율(%)', '운영_영업_개월_평균', '폐업_영업_개월_평균',
    '유효_수요_전환율', '점포당_평균_매출', '전년_동기_대비_폐업_증감률',
    '소득_구간_코드', '상권_업종_적합도', '총_아파트_세대수', '아파트_평균_시가',
    '총_직장_인구_수', '남성_직장_인구_수', '여성_직장_인구_수',
    '직장인구_100명당_점포수', '아파트_100세대당_점포수', '유사업종_점포비율',
    '직장인구_100명당_유사업종수', '점포당_매출_밀도', '직장인구_1인당_매출', '아파트세대당_매출',
    '집객시설_수', '집객시설_밀도'
]
feature_cols = [c for c in feature_cols if c in df.columns]

train_df = df[df['기준_년분기_코드'] < 20241].copy()
test_df = df[df['기준_년분기_코드'] >= 20241].copy()

for col in feature_cols + [target_col]:
    train_df[col] = pd.to_numeric(train_df[col], errors='coerce').fillna(0)
    test_df[col] = pd.to_numeric(test_df[col], errors='coerce').fillna(0)

X_train = train_df[feature_cols]
y_train = train_df[target_col].astype(int)
X_test = test_df[feature_cols]
y_test = test_df[target_col].astype(int)

ratio = float(np.sum(y_train == 0)) / np.sum(y_train == 1) if np.sum(y_train == 1) > 0 else 1.0

model = XGBClassifier(
    n_estimators=400, max_depth=4, learning_rate=0.03,
    subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
    gamma=0.2, reg_alpha=1, reg_lambda=15,
    scale_pos_weight=ratio, random_state=42, eval_metric='auc', n_jobs=-1
)
model.fit(X_train, y_train)

sample_size = min(500, len(X_test))
np.random.seed(42)
sample_indices = np.random.choice(X_test.index, size=sample_size, replace=False)
X_sample = X_test.loc[sample_indices]
y_sample = y_test.loc[sample_indices]

probs_sample = model.predict_proba(X_sample)[:, 1]
sample_analysis = X_sample.copy()
sample_analysis['actual'] = y_sample
sample_analysis['predicted_prob'] = probs_sample

danger_candidates = sample_analysis[(sample_analysis['actual'] == 1) & (sample_analysis['predicted_prob'] > 0.4)]
if danger_candidates.empty and not sample_analysis[sample_analysis['actual'] == 1].empty:
    danger_candidates = sample_analysis[sample_analysis['actual'] == 1].sort_values(by='predicted_prob', ascending=False).head(1)

if not danger_candidates.empty:
    idx = danger_candidates.index[0]
    print(f"Danger Prob: {danger_candidates.loc[idx, 'predicted_prob']:.4f}")
    print(f"Danger Prob Percent: {danger_candidates.loc[idx, 'predicted_prob']:.2%}")
