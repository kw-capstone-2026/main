# DS5: 서울시 생활인구 격자 데이터 처리 파이프라인

> 서울 스타트업 입지 분석 플랫폼 - 생활인구 데이터 모듈

## 📊 프로젝트 개요

서울시 250m×250m 격자 단위 생활인구 데이터를 **시간대별 시나리오**로 집계하여 분기별 데이터로 변환하는 자동화 파이프라인입니다.

## 👥 팀원 빠른 시작

```bash
# 1. 클론
git clone https://github.com/your-team/ds5-population-pipeline.git
cd ds5-population-pipeline

# 2. 환경 설정
conda create -n ds5 python=3.10
conda activate ds5
pip install -r requirements.txt

# 3. 데이터 확인
python check_final_data.py

# 4. 사용 시작!
python
>>> import pandas as pd
>>> ds5 = pd.read_parquet('data/quarterly/grid_quarterly_all.parquet')
```

## 📦 최종 데이터

- **파일**: `data/quarterly/grid_quarterly_all.parquet` (25MB)
- **행 수**: 120,546행
- **격자**: 8,893개
- **분기**: 14개 (2023Q1 ~ 2026Q2)
- **컬럼**: 33개

## 🎯 시간대별 시나리오

- 주중_오전 (07-09시)
- 주중_점심 (11-14시)
- 주중_저녁 (18-21시)
- 주중_야간 (21-23시)
- 주말_주간 (10-18시)
- 주말_야간 (18-23시)

## 📁 프로젝트 구조
ds5-population-pipeline/
├── README.md
├── requirements.txt
├── step1_clean_data.py
├── step2_aggregate_scenarios.py
├── step3_quarterly_aggregation.py
├── step4_full_pipeline.py
├── check_final_data.py
└── data/
└── quarterly/
└── grid_quarterly_all.parquet (25MB)

## 🚀 다음 단계

1. ✅ DS5 격자 데이터 생성 완료
2. ⏭️ 블록-격자 Spatial Join
3. ⏭️ DS2 상권분석 데이터와 조인
4. ⏭️ XGBoost 학습
