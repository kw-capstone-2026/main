# 데이터 시각화 파이프라인

소상공인 생존·폐업 위험도 예측 캡스톤 — 데이터 시각화 파트.
서울시 상권분석 데이터(2019Q1–2024Q4)의 불균형을 진단하고, 문헌 근거에 따라
처리한 전/후를 발표용 차트 13종으로 생성합니다.
추가로 **공간 분석·생존 분석·시계열 파생 피처** 3개 주제, 차트 5종을 더 생성합니다.

## 구성

### 기존 파이프라인 (불균형 진단 + 모델 성능)

| 파일 | 역할 |
| --- | --- |
| `config.py` | 경로·타겟·피처·출처 문구 등 모든 설정 |
| `viz_style.py` | 차트 공통 스타일(한글 폰트·팔레트·헬퍼) |
| `step1_model.py` | 전처리 + XGBoost(Baseline/비용민감) 학습 + 지표 |
| `step2_aggregate.py` | 진단용 기술통계 집계 |
| `step3_plots.py` | 차트 13종 생성 |
| `run_all.py` | 위 3단계를 한 번에 실행 |

### 추가 파이프라인 (공간·생존·시계열)

| 파일 | 역할 |
| --- | --- |
| `step4_extra_agg.py` | 공간·생존·시계열 파생 피처 집계 |
| `step5_extra_plots.py` | 추가 차트 5종(14~18) 생성 |
| `run_extra.py` | step4 + step5 한 번에 실행 |

## 사용법

```bash
pip install -r requirements.txt

# 데이터 경로를 config.py 의 DATA_PATH 에 맞춘 뒤

# 기존 파이프라인 (차트 01~13)
python run_all.py

# 추가 파이프라인 (차트 14~18) — run_all.py 실행 후
python run_extra.py
```

산출물:
- `output/charts/01~13_*.png` — 불균형 진단·모델 성능 차트
- `output/charts/14~18_*.png` — 공간·생존·시계열 추가 차트
- `output/artifacts/` — 중간 산출물(model_out.json, agg.json, extra_agg.json, curves.npz)

## 데이터 흐름

```
step1_model.py      → artifacts/model_out.json, curves.npz   (모델 지표·곡선)
step2_aggregate.py  → artifacts/agg.json                     (진단용 기술통계)
step3_plots.py      → 위 셋을 읽어 charts/01~13_*.png 생성

step4_extra_agg.py  → artifacts/extra_agg.json               (공간·생존·파생 피처)
step5_extra_plots.py→ extra_agg.json 을 읽어 charts/14~18_*.png 생성
```

## 차트 매핑 (함수 ↔ PNG ↔ 데이터 출처)

### 기존 차트 (01~13)

`step3_plots.py` 안의 함수 하나가 PNG 하나를 만듭니다.

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

### 추가 차트 (14~18)

`step5_extra_plots.py` 안의 함수 하나가 PNG 하나를 만듭니다.

| step5_extra_plots.py 함수 | 생성 PNG | 분석 주제 |
| --- | --- | --- |
| `c14_geo_risk` | 14_geo_risk | 공간 분석 — 상권별 폐업 발생률 산점도 |
| `c15_km_industry` | 15_km_industry | 생존 분석 — 업종별 Kaplan-Meier 생존 곡선 |
| `c16_km_segment` | 16_km_segment | 생존 분석 — 상권 유형별 Kaplan-Meier 생존 곡선 |
| `c17_ts_violin` | 17_ts_violin | 시계열 피처 — QoQ·YoY 변화율 분포 비교 |
| `c18_ts_corr` | 18_ts_corr | 시계열 피처 — 파생 변수 vs 원본 변수 상관계수 |

> 특정 차트만 다시 그리려면 해당 `c##` 함수만 호출하면 됩니다.
> 집계 수치를 바꾸려면 `step4_extra_agg.py` 를, 차트 모양만 바꾸려면 `step5_extra_plots.py` 를 수정하세요.

## 주요 설계 결정

### 기존 파이프라인
- **타겟**: 분기 폐업 발생 여부(`폐업_점포_수 > 0`, 양성 약 23%).
- **누수 방지**: 폐업에서 직접 파생된 변수(폐업률·폐업점포수·폐업영업개월 등)는 피처 제외.
- **시계열 분할**: 최근 4개 분기(2024)를 테스트셋으로 분리해 미래 정보 누수 차단.
- **불균형 대응**: 비용민감 학습(`scale_pos_weight`) + 임계값 조정 + PR 기반 평가.

### 추가 파이프라인
- **공간 분석**: 상권 고유 식별자를 탐색(없으면 소수점 3자리 좌표로 근사)해 상권별 폐업률을 좌표계에 매핑.
- **생존 분석**: 패널 데이터를 (상권, 업종) 단위로 집약해 첫 폐업 분기 또는 마지막 관측 분기의 `운영_영업_개월_평균`을 생존 시간으로 사용. Kaplan-Meier 추정기 수동 구현(외부 라이브러리 의존 없음).
- **시계열 파생 피처**: (상권, 업종) 패널 내 전분기 대비(QoQ) 및 전년 동기 대비(YoY) 변화율을 계산. 이상치(5–95th percentile) 제거 후 폐업 발생 그룹과 비교.

## 한글 폰트

`viz_style.py` 가 Noto Sans CJK KR → NanumGothic → AppleGothic → Malgun Gothic
순으로 탐색합니다. 환경에 맞는 폰트 경로를 `_FONT_CANDIDATES` 맨 앞에 추가하면 됩니다.
