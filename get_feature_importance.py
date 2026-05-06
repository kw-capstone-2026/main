import pandas as pd
import numpy as np
from dotenv import load_dotenv
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
from xgboost import XGBClassifier
import sys, os

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_acquisition import PublicDataAPI
from src.spatial_processor import SpatialProcessor
from src.feature_merger import FeatureMerger

SHP_PATH = "data/(도로명주소)기초구역_서울/TL_KODIS_BAS_11_202604.shp"
EXCLUDE_COLS = ['BAS_ID','상가업소번호','상호명','인허가일자','폐업일자',
                'open_date','close_date','end_date','lat','lon','geometry',
                'is_closed','survival_months','open_year']

print("데이터 로드 중...")
api = PublicDataAPI()
sp = SpatialProcessor(bas_shp_path=SHP_PATH)
fm = FeatureMerger()

stores_json = api.get_store_info_hybrid()
df_stores_raw = pd.DataFrame(stores_json['body']['items'])
sales_raw = api.get_seoul_commercial_sales("20241")
pop_raw = api.get_seoul_commercial_pop("20241")

gdf = sp.create_point_geometry(df_stores_raw, lat_col='lat', lng_col='lon')
gdf_mapped = sp.assign_bas_id(gdf)
df = fm.calculate_survival_duration(gdf_mapped)

df_sales = pd.DataFrame(sales_raw) if sales_raw else pd.DataFrame()
df_pop = pd.DataFrame(pop_raw) if pop_raw else pd.DataFrame()

master = fm.create_master_table(df_stores=df, df_sales=df_sales, df_pop=df_pop,
                                 use_real_data=True, use_competition=True,
                                 use_residential=True, use_sales=True)

features = [c for c in master.columns if c not in EXCLUDE_COLS]
for col in features:
    master[col] = pd.to_numeric(master[col], errors='coerce').fillna(0)
master['is_closed'] = master['is_closed'].astype(int)

X = master[features]
y = master['is_closed']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

ratio = float(np.sum(y_train==0)) / max(int(np.sum(y_train==1)), 1)
model = XGBClassifier(n_estimators=200, max_depth=4, learning_rate=0.05,
                      reg_lambda=5, scale_pos_weight=ratio, random_state=42,
                      use_label_encoder=False, eval_metric='auc')
model.fit(X_train, y_train)

importance = model.feature_importances_
fi = pd.DataFrame({'피처': features, '중요도': importance})
fi = fi.sort_values('중요도', ascending=False).reset_index(drop=True)
fi['순위'] = fi.index + 1

print("\n=== 피처 중요도 순위 ===")
print(fi.to_string(index=False))
fi.to_csv("experiments/feature_importance.csv", index=False, encoding='utf-8-sig')
print("\nexperiments/feature_importance.csv 저장 완료!")
