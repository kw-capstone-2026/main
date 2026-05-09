# DS5: 서울시 생활인구 격자 데이터 처리 파이프라인

> 서울 스타트업 입지 분석 플랫폼 - 생활인구 데이터 모듈

## 📊 개요

서울시 250m×250m 격자 단위 생활인구 데이터를 **시간대별 시나리오**로 집계하여 분기별 데이터로 변환하는 자동화 파이프라인

## 📦 데이터 정보
```
최종 파일
data/quarterly/grid_quarterly_all.parquet (25MB)

데이터 규모
격자 수: 8,893개 (250m×250m 서울 전역)
기간: 2023Q1 ~ 2026Q2 (14분기)
행 수: 120,546행
컬럼: 33개 (시나리오 6개 + 파생변수)
```

🚀 사용 방법
```bash
1️⃣ 리포지토리 클론
bashgit clone https://github.com/kw-capstone-2026/main.git
cd main
2️⃣ ds5-data 브랜치로 전환
bashgit checkout ds5-data
3️⃣ 환경 설정
bashconda create -n ds5 python=3.10
conda activate ds5
pip install -r requirements.txt
4️⃣ 데이터 사용 시작!
pythonimport pandas as pd

# 데이터 로드
df = pd.read_parquet('data/quarterly/grid_quarterly_all.parquet')

# 확인
print(f"격자: {df['grid_id'].nunique():,}개")
print(f"분기: {df['년분기'].nunique()}개")
print(f"기간: {df['년분기'].min()} ~ {df['년분기'].max()}")

# 샘플
print(df.head())
```

## 📦 최종 데이터

- **파일**: `data/quarterly/grid_quarterly_all.parquet` (25MB)
- **행 수**: 120,546행
- **격자**: 8,893개
- **분기**: 14개 (2023Q1 ~ 2026Q2)
- **컬럼**: 33개

## 주요 컬럼:
- grid_id: 격자 ID (예: "다사35005075")
- 년분기: 분기 (예: "2023Q1", "2024Q2")
- 주중_오전_avg: 주중 오전 평균 인구
- 주중_점심_avg: 주중 점심 평균 인구
- 주중_저녁_avg: 주중 저녁 평균 인구
- 주중_야간_avg: 주중 야간 평균 인구
- 주말_주간_avg: 주말 주간 평균 인구
- 주말_야간_avg: 주말 야간 평균 인구
+ 파생 변수들 (주중평균, 주말평균, 피크시나리오 등)
→ 업종별 맞춤 분석 가능! (카페는 오전, 식당은 점심/저녁, 술집은 야간)

## 📁 프로젝트 구조
ds5-data 브랜치/
├── README.md
├── requirements.txt
├── step1_clean_data.py              # 데이터 정제
├── step2_aggregate_scenarios.py     # 시나리오 집계
├── step3_quarterly_aggregation.py   # 분기별 변환
├── step4_full_pipeline.py           # 전체 자동화
└── data/
    └── quarterly/
        └── grid_quarterly_all.parquet (최종 데이터!)

## 🚀 다음 단계
1. ✅ DS5 격자 데이터 생성 완료
2. ⏭️ 블록-격자 Spatial Join
3. ⏭️ DS2 상권분석 데이터와 조인
4. ⏭️ XGBoost 학습
