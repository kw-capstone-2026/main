# 데이터 불균형 시각화 파이프라인

소상공인 생존·폐업 위험도 예측 캡스톤 — 데이터 시각화 파트.
서울시 상권분석 데이터(2019Q1–2024Q4)의 불균형을 진단하고, 문헌 근거에 따라
처리한 전/후를 발표용 차트 13종으로 생성합니다.

## 구성

| 파일 | 역할 |
| --- | --- |
| `config.py` | 경로·타겟·피처·출처 문구 등 모든 설정 |
| `viz_style.py` | 차트 공통 스타일(한글 폰트·팔레트·헬퍼) |
| `step1_model.py` | 전처리 + XGBoost(Baseline/비용민감) 학습 + 지표 |
| `step2_aggregate.py` | 진단용 기술통계 집계 |
| `step3_plots.py` | 차트 13종 생성 |
| `run_all.py` | 위 3단계를 한 번에 실행 |

## 사용법

```bash
pip install -r requirements.txt

# 데이터 경로를 config.py 의 DATA_PATH 에 맞춘 뒤
python run_all.py
```

산출물:
- `output/charts/01~13_*.png` — 발표용 고해상도 차트
- `output/artifacts/` — 중간 산출물(model_out.json, agg.json, curves.npz)

## 데이터 흐름

`step1`·`step2`는 차트를 직접 그리지 않고, 차트가 읽을 데이터(중간 산출물)를 만듭니다.

```
step1_model.py      → artifacts/model_out.json, curves.npz   (모델 지표·곡선)
step2_aggregate.py  → artifacts/agg.json                     (진단용 기술통계)
step3_plots.py      → 위 셋을 읽어 charts/01~13_*.png 생성
```

## 차트 매핑 (함수 ↔ PNG ↔ 데이터 출처)

`step3_plots.py` 안의 함수 하나가 PNG 하나를 만듭니다. 특정 차트만 다시 뽑으려면
해당 함수만 수정/호출하면 됩니다. (`main()` 이 c01~c13 을 순서대로 호출)

| step3_plots.py 함수 | 생성 PNG | 데이터 출처 |
| --- | --- | --- |
| `c01_target` | 01_target_imbalance | agg (step2) |
| `c02_zero` | 02_zero_inflation | agg |
| `c03_industry_skew` | 03_industry_skew | agg |
| `c04_lorenz` | 04_industry_lorenz | agg |
| `c05_segment` | 05_segment_risk | agg |
| `c06_timeseries` | 06_timeseries_covid | agg |
| `c07_industry_posrate` | 07_industry_posrate | agg |
| `c08_methods` | 08_methods_evidence | 문헌 카드(데이터 무관) |
| `c09_accuracy_trap` | 09_accuracy_trap | model (step1) |
| `c10_roc_pr` | 10_roc_pr_curves | model + curves.npz |
| `c11_threshold` | 11_threshold_sweep | model |
| `c12_confusion` | 12_confusion_before_after | model |
| `c13_importance` | 13_feature_importance | model |

> 진단 차트(01~07)는 `step2`의 `agg.json`, 모델 성능 차트(09~13)는 `step1`의
> `model_out.json`·`curves.npz` 에서 나옵니다. 숫자 자체(예: 임계값·재현율)를
> 바꾸려면 `step1_model.py` 를, 차트 모양만 바꾸려면 해당 `c##` 함수를 수정하세요.

## 주요 설계 결정

- **타겟**: 분기 폐업 발생 여부(`폐업_점포_수 > 0`, 양성 약 23%).
- **누수 방지**: 폐업에서 직접 파생된 변수(폐업률·폐업점포수·폐업영업개월 등)는 피처 제외.
- **시계열 분할**: 최근 4개 분기(2024)를 테스트셋으로 분리해 미래 정보 누수 차단.
- **불균형 대응**: 비용민감 학습(`scale_pos_weight`) + 임계값 조정 + PR 기반 평가.

## 한글 폰트

`viz_style.py` 가 Noto Sans CJK KR → NanumGothic → AppleGothic → Malgun Gothic
순으로 탐색합니다. 환경에 맞는 폰트 경로를 `_FONT_CANDIDATES` 맨 앞에 추가하면 됩니다.
