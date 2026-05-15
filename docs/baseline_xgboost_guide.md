# 과포화 예측 프로젝트: XGBoost 베이스라인 실행 가이드

이 문서는 팀원들이 프로젝트의 데이터 통합 과정을 이해하고, 베이스라인 모델을 직접 실행 및 검증하기 위한 가이드라인입니다.

---

## 1. 필독 참고 문서 (What to Read)

프로젝트의 배경과 기술적 상세 내용을 먼저 파악하세요.

1. **[진행 상황 리포트](progress_05_15.md):** 최신 데이터 전략(10년 단위 모델링)과 병합 내역 요약.
2. **[모델 기술 명세서](model_technical_details.md):** XGBoost의 하이퍼파라미터 설정 이유와 AUC 0.90 달성 근거.
3. **[데이터 통합 리포트](progress_05_14.md):** 초기 데이터 정제 및 결함 수정 내역.

---

## 2. 데이터 경로 (Data Location)

- **원본 데이터:** `data/parquet_datas/` (팀원 공유 원본 파케이 파일들)
- **통합 데이터:** `data/parquet_datas/final_merged_commercial_data.parquet` (학습에 사용되는 마스터 테이블)

---

## 3. 실행 순서 (What to Run)

터미널(Root 경로)에서 다음 순서대로 코드를 실행하여 분석을 진행합니다.

### 1단계: 데이터 통합 및 정제

팀원들이 준 개별 데이터셋을 하나의 마스터 테이블로 합칩니다.

```powershell
python src/feature_merger.py
```

- **결과:** 타입 교정 및 결측치가 처리된 통합 파케이 파일이 생성됨.

### 2단계: 베이스라인 모델 학습 및 평가

생성된 통합 데이터를 사용하여 AI 모델을 학습시키고 성능을 측정합니다.

```powershell
python src/models/train_baseline.py
```

- **결과:** 터미널에 **AUC Score, Accuracy, 피처 중요도**가 출력됨.

---

## 4. 확인해야 할 결과물 (What to Check)

모델 실행 후 생성되는 다음 파일들을 통해 성능을 비교하세요.

- **터미널 출력:** AUC 0.90 이상의 성능이 나오는지 확인.
- **피처 중요도 리포트:** `agenttest/baseline_feature_importance.csv` (어떤 변수가 예측에 핵심적인지 수치로 확인 가능)

---

## 5. 협업

본인이 가져온 **새로운 보조 데이터(예: 학교 거리 등)**를 테스트하고 싶다면?

1. `src/feature_merger.py`에서 해당 데이터를 병합 로직에 추가합니다.
2. `src/models/train_baseline.py`의 `feature_cols` 리스트에 새로운 변수 이름을 넣고 실행합니다.
3. 기존 베이스라인 점수(AUC 0.90)보다 성능이 올라가는지 확인합니다.
