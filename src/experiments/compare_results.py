"""
실험 결과 비교: Baseline vs Proposed
"""
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

print("=" * 60)
print("실험 3: 결과 비교 및 분석")
print("=" * 60)

# =========================================================
# 1. 결과 로드
# =========================================================
print("\n1. 실험 결과 로드...")

with open('results/baseline_results.json', 'r') as f:
    baseline = json.load(f)

with open('results/proposed_results.json', 'r') as f:
    proposed = json.load(f)

print("  ✅ Baseline 결과 로드")
print("  ✅ Proposed 결과 로드")

# =========================================================
# 2. 성능 비교
# =========================================================
print("\n" + "=" * 60)
print("2. 성능 비교")
print("=" * 60)

baseline_auc = baseline['metrics']['auc']
proposed_auc = proposed['metrics']['auc']
auc_improvement = proposed_auc - baseline_auc

baseline_acc = baseline['metrics']['accuracy']
proposed_acc = proposed['metrics']['accuracy']
acc_improvement = proposed_acc - baseline_acc

print(f"\n=== AUC Score ===")
print(f"  Baseline (DS5 제외):  {baseline_auc:.4f}")
print(f"  Proposed (DS5 포함):  {proposed_auc:.4f}")
print(f"  개선:                 {auc_improvement:+.4f} ({auc_improvement/baseline_auc*100:+.2f}%)")

print(f"\n=== Accuracy ===")
print(f"  Baseline (DS5 제외):  {baseline_acc:.4f}")
print(f"  Proposed (DS5 포함):  {proposed_acc:.4f}")
print(f"  개선:                 {acc_improvement:+.4f} ({acc_improvement/baseline_acc*100:+.2f}%)")

# =========================================================
# 3. Feature Importance 비교
# =========================================================
print("\n" + "=" * 60)
print("3. Feature Importance 비교")
print("=" * 60)

baseline_fi = pd.DataFrame(baseline['feature_importance'])
proposed_fi = pd.DataFrame(proposed['feature_importance'])

print("\n=== Top 10 Features (Baseline) ===")
for idx, row in baseline_fi.head(10).iterrows():
    print(f"  {idx+1:2d}. {row['feature']:30s} {row['importance']:.6f}")

print("\n=== Top 10 Features (Proposed) ===")
ds5_features = proposed.get('ds5_features', [])
for idx, row in proposed_fi.head(10).iterrows():
    is_ds5 = row['feature'] in ds5_features
    marker = "🆕" if is_ds5 else "  "
    print(f"{marker} {idx+1:2d}. {row['feature']:30s} {row['importance']:.6f}")

# DS5 feature 순위
print("\n=== DS5 Feature 상세 (Proposed 모델) ===")
ds5_fi = proposed_fi[proposed_fi['feature'].isin(ds5_features)]
for idx, row in ds5_fi.iterrows():
    rank = proposed_fi[proposed_fi['feature'] == row['feature']].index[0] + 1
    print(f"  #{rank:2d}. {row['feature']:30s} {row['importance']:.6f}")

# =========================================================
# 4. 혼동행렬 비교
# =========================================================
print("\n" + "=" * 60)
print("4. 혼동행렬 비교")
print("=" * 60)

baseline_cm = baseline['confusion_matrix']
proposed_cm = proposed['confusion_matrix']

print("\n=== Baseline ===")
print("           예측:정상  예측:과포화")
print(f"실제:정상      {baseline_cm[0][0]:6d}    {baseline_cm[0][1]:6d}")
print(f"실제:과포화    {baseline_cm[1][0]:6d}    {baseline_cm[1][1]:6d}")

print("\n=== Proposed ===")
print("           예측:정상  예측:과포화")
print(f"실제:정상      {proposed_cm[0][0]:6d}    {proposed_cm[0][1]:6d}")
print(f"실제:과포화    {proposed_cm[1][0]:6d}    {proposed_cm[1][1]:6d}")

# =========================================================
# 5. 결과 요약
# =========================================================
print("\n" + "=" * 60)
print("5. 실험 결과 요약")
print("=" * 60)

summary = f"""
실험 기간: 2023-2024 (DS5 기간)

[모델 비교]
1. Baseline (DS5 제외)
   - Feature: {baseline['num_features']}개
   - AUC: {baseline_auc:.4f}
   - Accuracy: {baseline_acc:.4f}

2. Proposed (DS5 포함)
   - Feature: {proposed['num_features']}개 (DS5 {len(ds5_features)}개 추가)
   - AUC: {proposed_auc:.4f}
   - Accuracy: {proposed_acc:.4f}

[DS5 효과]
- AUC 개선: {auc_improvement:+.4f} ({auc_improvement/baseline_auc*100:+.2f}%)
- Accuracy 개선: {acc_improvement:+.4f} ({acc_improvement/baseline_acc*100:+.2f}%)

[결론]
"""

if auc_improvement > 0:
    summary += f"✅ DS5 생활인구 데이터 추가로 성능 향상\n"
    summary += f"   AUC가 {auc_improvement:.4f}p 증가하여 {proposed_auc:.4f} 달성\n"
else:
    summary += f"⚠️ DS5 추가로 인한 성능 변화 미미\n"

print(summary)

# =========================================================
# 6. 보고서 저장
# =========================================================
print("\n6. 보고서 저장...")

# Markdown 보고서
report = f"""# DS5 효과 검증 실험 결과

## 실험 개요

- **기간**: 2023-2024 (DS5 기간)
- **데이터**: Train {baseline['train_size']:,}행, Test {baseline['test_size']:,}행
- **목적**: DS5 생활인구 데이터의 모델 성능 개선 효과 검증

---

## 모델 비교

### Baseline (DS5 제외)

- Feature 수: {baseline['num_features']}개
- AUC: **{baseline_auc:.4f}**
- Accuracy: **{baseline_acc:.4f}**

### Proposed (DS5 포함)

- Feature 수: {proposed['num_features']}개 (DS5 {len(ds5_features)}개 추가)
- AUC: **{proposed_auc:.4f}**
- Accuracy: **{proposed_acc:.4f}**

---

## DS5 효과

| 지표 | Baseline | Proposed | 개선 | 개선율 |
|------|----------|----------|------|--------|
| AUC | {baseline_auc:.4f} | {proposed_auc:.4f} | {auc_improvement:+.4f} | {auc_improvement/baseline_auc*100:+.2f}% |
| Accuracy | {baseline_acc:.4f} | {proposed_acc:.4f} | {acc_improvement:+.4f} | {acc_improvement/baseline_acc*100:+.2f}% |

---

## DS5 Feature 중요도

| 순위 | Feature | Importance |
|------|---------|------------|
"""

for idx, row in ds5_fi.iterrows():
    rank = proposed_fi[proposed_fi['feature'] == row['feature']].index[0] + 1
    report += f"| #{rank} | {row['feature']} | {row['importance']:.6f} |\n"

report += f"""
---

## 결론

{summary.strip()}

---

## 파일 위치

- Baseline 결과: `results/baseline_results.json`
- Proposed 결과: `results/proposed_results.json`
- Baseline 모델: `results/baseline_model.pkl`
- Proposed 모델: `results/proposed_model.pkl`
- Feature Importance: `results/*_feature_importance.csv`
"""

with open('results/comparison_report.md', 'w', encoding='utf-8') as f:
    f.write(report)

print("  ✅ results/comparison_report.md 저장 완료")

# JSON 요약
comparison = {
    'experiment_period': '2023-2024',
    'baseline': {
        'model': 'Baseline (DS5 제외)',
        'num_features': baseline['num_features'],
        'auc': baseline_auc,
        'accuracy': baseline_acc
    },
    'proposed': {
        'model': 'Proposed (DS5 포함)',
        'num_features': proposed['num_features'],
        'ds5_features': len(ds5_features),
        'auc': proposed_auc,
        'accuracy': proposed_acc
    },
    'improvement': {
        'auc': float(auc_improvement),
        'auc_percent': float(auc_improvement/baseline_auc*100),
        'accuracy': float(acc_improvement),
        'accuracy_percent': float(acc_improvement/baseline_acc*100)
    }
}

with open('results/comparison_summary.json', 'w', encoding='utf-8') as f:
    json.dump(comparison, f, indent=2, ensure_ascii=False)

print("  ✅ results/comparison_summary.json 저장 완료")

# =========================================================
# 7. 완료
# =========================================================
print("\n" + "=" * 60)
print("실험 완료!")
print("=" * 60)
print(f"\n결과 파일:")
print(f"  📊 results/comparison_report.md")
print(f"  📊 results/comparison_summary.json")
print(f"  📊 results/baseline_results.json")
print(f"  📊 results/proposed_results.json")
print(f"\n보고서:")
print(f"  cat results/comparison_report.md")
