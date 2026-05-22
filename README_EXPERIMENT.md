# DS5 효과 검증 실험

## 📋 실험 목적

DS5 생활인구 데이터가 상권 과포화 예측 모델의 성능에 미치는 영향을 검증합니다.

---

## 🎯 실험 설계

### 실험 기간
- **2023-2024** (DS5 데이터 기간)
- 총 2년, 8분기
- Train: 2023 / Test: 2024

### 비교 모델

1. **Baseline (DS5 제외)**
   - 기본 Feature만 사용
   - 매출, 점포수, 폐업률 등

2. **Proposed (DS5 포함)**
   - 기본 Feature + DS5 10개 추가
   - 시간대별 유동인구, 주야간비율, 인구 변화 추세 등

---

## 📁 파일 구조

```
src/experiments/
├── prepare_ds5_period.py       # 1단계: 데이터 준비
├── train_baseline_model.py     # 2A: Baseline 학습
├── train_proposed_model.py     # 2B: Proposed 학습
└── compare_results.py          # 3: 결과 비교

data/
├── ds5_period_data.parquet     # DS5 기간 전체 데이터
├── ds5_period_train.parquet    # Train (2023)
└── ds5_period_test.parquet     # Test (2024)

results/
├── comparison_report.md        # 📊 최종 보고서
├── comparison_summary.json     # 📊 결과 요약
├── baseline_results.json       # Baseline 상세 결과
├── proposed_results.json       # Proposed 상세 결과
├── baseline_model.pkl          # Baseline 모델
├── proposed_model.pkl          # Proposed 모델
├── baseline_feature_importance.csv
└── proposed_feature_importance.csv
```

---

## 🚀 실행 방법

### 방법 1: 한 번에 실행 (추천)

```bash
# ds5 환경 활성화
conda activate ds5

# 전체 실험 실행
bash run_experiment.sh
```

### 방법 2: 단계별 실행

```bash
conda activate ds5

# 1단계: 데이터 준비
python src/experiments/prepare_ds5_period.py

# 2A단계: Baseline 학습
python src/experiments/train_baseline_model.py

# 2B단계: Proposed 학습
python src/experiments/train_proposed_model.py

# 3단계: 결과 비교
python src/experiments/compare_results.py
```

---

## 📊 결과 확인

### 보고서 보기

```bash
cat results/comparison_report.md
```

### JSON 결과

```bash
cat results/comparison_summary.json
```

---

## 🔍 예상 결과

```json
{
  "improvement": {
    "auc": 0.0050,
    "auc_percent": 0.51,
    "accuracy": 0.0020,
    "accuracy_percent": 0.20
  }
}
```

---

## 📈 평가 지표

1. **AUC Score**
   - 주요 지표
   - 클래스 불균형에 robust

2. **Accuracy**
   - 전체 정확도

3. **Feature Importance**
   - DS5 변수의 중요도
   - Top 10 진입 여부

4. **Confusion Matrix**
   - False Positive/Negative 비교

---

## 💡 해석 가이드

### DS5 효과가 크면:
- AUC 개선 > 0.5%p
- DS5 변수가 Top 10에 진입
- 시간대별 패턴이 중요 변수로 확인

### DS5 효과가 작으면:
- AUC 개선 < 0.5%p
- DS5 매칭률 낮음 (12.7%)
- 데이터 부족

---

## 🔄 재실행

```bash
# 결과 폴더 삭제
rm -rf results/*

# 다시 실행
bash run_experiment.sh
```

---

## 📝 Git 커밋

```bash
git add src/experiments/
git add results/
git add run_experiment.sh
git add README_EXPERIMENT.md

git commit -m "Add DS5 효과 검증 실험: Baseline vs Proposed 비교"
git push origin ds5-integration
```

---

## 🎓 결론 작성 예시

```
본 연구에서는 DS5 생활인구 데이터의 효과를 검증하기 위해
2023-2024 기간 데이터를 사용하여 비교 실험을 수행했다.

Baseline 모델(DS5 제외)은 AUC 0.9850을 달성했으며,
Proposed 모델(DS5 포함)은 AUC 0.9900으로 0.5%p 향상되었다.

DS5 생활인구 변수 중 '주중_점심_avg'가 가장 높은 중요도를
보였으며(Top 5), 이는 상권 활성도 예측에 시간대별 유동인구
패턴이 유의미한 정보를 제공함을 시사한다.
```

---

## ❓ 문제 해결

### 데이터 파일 없음
```bash
# feature_merger.py 먼저 실행
python src/feature_merger.py
```

### 환경 에러
```bash
conda activate ds5
pip install xgboost scikit-learn pandas --break-system-packages
```

### 결과 파일 확인
```bash
ls -lh results/
```

---

**실험을 시작하세요!** 🚀

```bash
conda activate ds5
bash run_experiment.sh
```
