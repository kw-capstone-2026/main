# 코드 파일 위치 정리

> 브랜치: `feature/experiment-interaction-features`
> 작성자: 정현주 | 2026.05.04

---

## 전체 파일 구조

```
main/
├── main.py
├── experiment_logger.py
├── get_feature_importance.py
├── src/
│   ├── data_acquisition.py
│   ├── feature_merger.py
│   ├── spatial_processor.py
│   └── models/
│       └── baseline_xgboost.py
└── experiments/
    ├── experiment_log.csv
    └── reports/
        ├── EXP_000.md
        ├── EXP_001.md
        ├── EXP_002.md
        ├── EXP_003.md
        ├── EXP_004.md
        ├── EXP_005.md
        ├── EXP_006.md
        ├── EXP_007.md
        ├── EXP_008.md
        └── EXP_009.md
```

---

## 파일별 역할 정리

| 파일 | 역할 | 주요 내용 |
|---|---|---|
| `main.py` | 전체 실험 실행 | EXP_000~009 순서대로 실행, 결과 자동 기록 |
| `experiment_logger.py` | 실험 자동 기록 | CSV + 마크다운 보고서 자동 생성 |
| `get_feature_importance.py` | 피처 중요도 분석 | 변수별 폐업 예측 기여도 출력 |
| `src/data_acquisition.py` | API 데이터 수집 | DS1~DS5 서울시 공개 API 호출 |
| `src/feature_merger.py` | 피처 생성 및 조인 | 상권 실질 인터랙션 변수 추가 (핵심 파일) |
| `src/spatial_processor.py` | 공간 데이터 처리 | 위경도 변환, BAS_ID 공간 조인 |
| `src/models/baseline_xgboost.py` | 모델 학습/평가 | XGBoost 분류기 |
| `experiments/experiment_log.csv` | 실험 기록 | 전체 실험 AUC, ACC, 파라미터 한눈에 비교 |
| `experiments/reports/EXP_NNN.md` | 개별 실험 보고서 | 실험별 상세 기록 (자동 생성) |

---

## 상권 실질 인터랙션 변수 위치

**파일: `src/feature_merger.py`**

| 함수명 | 담당 변수 | 데이터 소스 |
|---|---|---|
| `extract_floating_pop_features()` | total_flpop, weekend_pop_ratio | DS2 - VwsmTrdarFlpopQq (유동인구) |
| `extract_residential_pop_features()` | resident_pop, worker_pop | DS2 - VwsmTrdarAresQq (배후인구) |
| `extract_competition_features()` | same_induty_cnt, avg_comp_survival | 점포 데이터 내부 계산 |
| `extract_sales_features()` | monthly_sales_real, sales_per_store | DS2 - VwsmTrdarSelngQq (매출) |
| `create_master_table()` | 위 변수 전체 통합 | 실험 플래그로 on/off 제어 |

---

## 실험별 코드 변경 내용

| 실험 | 변경 파일 | 변경 내용 |
|---|---|---|
| EXP_000 | `src/feature_merger.py` | 기존 코드 그대로 (가짜 계산값) |
| EXP_001 | `src/feature_merger.py` | `extract_floating_pop_features()` 적용 |
| EXP_002 | `src/feature_merger.py` | `extract_residential_pop_features()` 적용 |
| EXP_003 | `src/feature_merger.py` | `extract_competition_features()` 적용 |
| EXP_004 | `src/feature_merger.py` | `extract_sales_features()` 적용 |
| EXP_005 | `src/feature_merger.py` | 위 4개 전체 통합 |
| EXP_006 | `main.py` | n_estimators 100→200 |
| EXP_007 | `main.py` | max_depth 4→3 |
| EXP_008 | `main.py` | learning_rate 0.05→0.01, n_estimators 500 |
| EXP_009 | `main.py` | reg_lambda 5→15 |
