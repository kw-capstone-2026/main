# 처음부터 다시 만드는 방법

`output/`의 모든 결과물은 아래 순서로 스크립트를 실행하면 같은 값으로 다시 만들어짐 (2회 실행 후 파일 해시 동일 확인함).

## 1. 준비물 (저장소 안에 있음, 읽기만 함)

- `data/parquet_datas/final_merged_commercial_data_v5.parquet`
- `ml-server/xgb_model.json`, `ml-server/lgb_model.txt`, `ml-server/feature_cols.json`

## 2. 가상환경 (저장소 밖, 전역 환경 사용 안 함)

```powershell
# 프로젝트 루트(E:\capstone\kw-capstone-2026)에서
python -m venv E:\capstone\.venv_final        # Python 3.13.14 사용
E:\capstone\.venv_final\Scripts\python.exe -m pip install --upgrade pip
E:\capstone\.venv_final\Scripts\python.exe -m pip install -r output\requirements_used.txt
```

- xgboost는 모델 저장 버전과 같은 3.2.0으로 맞춤 (`xgb_model.json` 안의 version = 3.2.0)
- `environment.yml`(conda `capstone`, Python 3.10)은 이 PC에 환경이 만들어져 있지 않아 사용하지 않음

## 3. 실행 순서

```powershell
$PY = "E:\capstone\.venv_final\Scripts\python.exe"
& $PY scripts_final\00_check_env.py        # 버전 확인, requirements_used.txt, run_log.txt 새로 시작
& $PY scripts_final\01_load_and_inspect.py # 2024년 필터, 구조 검증 (기대 행 수와 다르면 중단)
& $PY scripts_final\02_predict.py          # XGB·LGB 확률, 앙상블
& $PY scripts_final\03_validate.py         # 성능 검증 (기준 벗어나면 원인 점검 출력 후 중단)
& $PY scripts_final\04_risk_score.py       # 위험지수·등급, 등급 근거(risk_grade_calibration.md)
& $PY scripts_final\05_shap_top5.py        # SHAP Top5, 표시명 초안
& $PY scripts_final\06_build_master.py     # master_2024.csv
& $PY scripts_final\07_demo_candidates.py  # 확정 시연 블록 3개 + 예비 후보 30개 + 같은 업종 시나리오 15개
& $PY scripts_final\08_label_leakage_check.py  # 정답·누수 점검 → label_check.md (라벨은 바꾸지 않음)
& $PY scripts_final\09_ablation_no_closure.py  # 폐업 변수를 뺀 비교 재학습 → ablation_no_closure.md (약 1~2분, 시연 결과는 안 바뀜)
& $PY scripts_final\10_verify_handoff.py  # 작업 요구사항 자동 점검 → verification_report.md
```

- 전체 소요 시간: 약 3분 (SHAP, 비교 재학습 포함)
- 각 스크립트는 앞 스크립트가 `output/_intermediate/`에 남긴 중간 파일을 읽으므로 순서대로 실행해야 함
- 실행 로그는 화면과 `output/run_log.txt`에 같이 남음 (00번이 로그를 새로 시작함)
- 실패 시 종료코드 1과 `[중단]` 메시지가 출력됨

## 4. 바꾸기 쉬운 설정 (스크립트 맨 위 상수)

| 무엇 | 파일 | 상수 |
|---|---|---|
| 위험등급 기준 (확정 75/50) | `common.py` | `GRADE_DANGER`, `GRADE_CAUTION` (04·07이 함께 씀) |
| 시연 후보 점포 수 필터·후보 수 | `07_demo_candidates.py` | `MIN_STORES`, `N_PER_TIER`, `FAMOUS` |
| 확정 시연 블록 3개 | `07_demo_candidates.py` | `DEMO_FINAL` |
| 같은 업종 시나리오의 업종 | `07_demo_candidates.py` | `SCENARIO_INDUSTRY`, `N_SCENARIO` |
| 한글 표시명 초안 | `05_shap_top5.py` | `FEATURE_LABELS` |
| 앙상블 가중치, 대상 분기 | `common.py` | `W_XGB`, `W_LGB`, `DEMO_QUARTER` |

등급 기준을 바꾸면 `04` → `06` → `07` 순서로 다시 실행해야 함. 04는 1~3분기 데이터로 계산한 기준이 상수와 다르면 "불일치"를 출력함.
