"""0단계: 환경 확인. 패키지 import·버전 출력, pip freeze 저장. run_log.txt를 새로 시작한다."""
import os
import subprocess
import sys
import warnings

sys.path.insert(0, os.path.dirname(__file__))
from common import LOG_PATH, OUT_DIR, XGB_PATH, LGB_PATH  # noqa: E402

# 전체 파이프라인의 첫 스크립트이므로 로그를 초기화
open(LOG_PATH, 'w', encoding='utf-8').close()
from common import setup_logging  # noqa: E402

setup_logging('00_check_env')

print(f'Python: {sys.version.split()[0]}  ({sys.executable})')
for name in ['pandas', 'numpy', 'pyarrow', 'xgboost', 'lightgbm', 'shap', 'sklearn']:
    mod = __import__(name)
    print(f'  {name:<12} {mod.__version__}')

# 모델 로드 시 버전 경고가 나오는지 확인 (숨기지 않고 그대로 출력)
import lightgbm as lgb  # noqa: E402
import xgboost as xgb  # noqa: E402

with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter('always')
    booster = xgb.Booster()
    booster.load_model(XGB_PATH)
    lgb_booster = lgb.Booster(model_file=LGB_PATH)
print(f'XGBoost 모델 로드 OK (특성 {booster.num_features()}개), 저장 버전: 3.2.0 (json 메타데이터)')
print(f'LightGBM 모델 로드 OK (특성 {lgb_booster.num_feature()}개, 트리 {lgb_booster.num_trees()}개)')
if caught:
    for w in caught:
        print(f'[모델 로드 경고] {w.category.__name__}: {w.message}')
else:
    print('모델 로드 경고: 없음')

freeze = subprocess.run([sys.executable, '-m', 'pip', 'freeze'], capture_output=True, text=True).stdout
with open(os.path.join(OUT_DIR, 'requirements_used.txt'), 'w', encoding='utf-8') as f:
    f.write(freeze)
print(f'[저장] output/requirements_used.txt ({len(freeze.splitlines())}개 패키지)')
