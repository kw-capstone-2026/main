import numpy as np
import os
import sys
import io

# Windows 콘솔 인코딩 에러 방지
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8')

def calculate_scores():
    cases = [
        {"name": "고위험 점포 (Danger Store)", "prob": 0.9476, "log_odds": 2.8959},
        {"name": "저위험 점포 (Safe Store)", "prob": 0.1929, "log_odds": -1.4314},
        {"name": "평균 기준 점포 (Base Value)", "prob": 0.5038, "log_odds": 0.0152}
    ]
    
    report = []
    report.append("# 📊 위험 지수 (Risk Score) 산정 및 변환 공식 분석 보고서\n")
    report.append("본 문서는 머신러닝 모델의 출력 확률값($p$) 또는 log-odds를 직관적인 `0~100` 점수의 위험 지수로 변환하는 두 가지 통계적 스케일링 방법론을 비교한 결과입니다. (발표 장표용 공식 및 수치 제공)\n")
    
    report.append("## 1️⃣ 방법론 1: 선형 변환 공식 (Linear Scaling)")
    report.append("모델이 출력하는 폐업 확률값($p \\in [0, 1]$)을 직관적으로 100배 곱하여 `0~100` 점수로 변환하는 가장 단순한 매핑 방식입니다.")
    report.append("$$\\text{Score}_{\\text{linear}} = p \\times 100$$")
    report.append("\n**[선형 스케일 변환 결과]**")
    for case in cases:
        score_lin = case["prob"] * 100
        report.append(f"- **{case['name']}**:")
        report.append(f"  - 모델 예측 확률 ($p$): {case['prob']:.4f} ({case['prob']:.2%})")
        report.append(f"  - **최종 위험 지수 (점수)**: **{score_lin:.2f}점** (반올림 시 **{round(score_lin)}점**)")
    report.append("")
    
    report.append("## 2️⃣ 방법론 2: Log-odds 기반 신용평가 점수화 공식 (Logistic/Credit Scoring)")
    report.append("금융권(신용 평가 등)에서 사용하는 방식으로, 모델의 log-odds 값에 선형 보정 계수를 적용하여 점수화(Scorecard)합니다. 이 방식은 확률이 극단에 수렴하더라도 위험 수준의 차이를 정교하게 변별해 줍니다.")
    report.append("$$\\text{log\\_odds} = \\ln\\left(\\frac{p}{1-p}\\right)$$")
    report.append("$$\\text{Score}_{\\text{logistic}} = \\text{Offset} + \\text{Factor} \\times \\text{log\\_odds}$$")
    report.append("\n여기서 중간값인 $p = 50.38\\%(\\text{log\\_odds} = 0.0152)$일 때 **50점**을 부여하고, 배율 계수(Factor)를 15로 설정하여 위험 점수가 `0`에서 `100` 사이에 안착하도록 설계하였습니다.")
    report.append("$$\\text{Score}_{\\text{logistic}} = \\text{Clip}\\left(50 + 15 \\times \\text{log\\_odds}, \\, 0, \\, 100\\right)$$")
    report.append("\n**[Log-odds 기반 스케일 변환 결과]**")
    for case in cases:
        score_log = 50 + 15 * case["log_odds"]
        score_log_clipped = max(0.0, min(100.0, score_log))
        report.append(f"- **{case['name']}**:")
        report.append(f"  - 모델 Log-odds: {case['log_odds']:.4f}")
        report.append(f"  - 계산 값: 50 + 15 * ({case['log_odds']:.4f}) = {score_log:.2f}")
        report.append(f"  - **최종 위험 지수 (점수)**: **{score_log_clipped:.2f}점** (반올림 시 **{round(score_log_clipped)}점**)")
        
    report.append("\n## 💡 PPT 발표용 요약 및 학술적 근거 (Academic Justification)")
    report.append("1. **선형 매핑의 장단점**: 선형 매핑은 일반 사용자나 심사위원이 이해하기가 매우 쉽지만, 극도로 낮은/높은 위험 구간의 변별력을 압축시켜버리는 단점이 있습니다.")
    report.append("2. **Log-odds 신용 평가식의 장단점**: 금융 통계학적으로 널리 쓰이는 **Logistic Platt Scaling** 기반 점수화 식은, 극단값(예: 95% 이상 위험)에서의 미세한 리스크 요인 차이를 log-odds 공간에서 넓게 변별해 주기 때문에 학술적으로 훨씬 정밀하고 권위 있는 평가지표로 제시할 수 있습니다. (예: Danger Store의 94.76% 위험을 **93점**으로 매핑)")
    
    out_dir = 'docs/0603_report'
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, 'risk_score_results.md')
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(report))
        
    print(f"\n[Success] 위험 점수 산정 결과가 '{out_file}' 에 성공적으로 저장되었습니다.")
    
    print("=" * 60)
    print(" 🔢 [위험 지수 변환 공식 비교 결과 요약] ")
    print("=" * 60)
    for case in cases:
        score_lin = case["prob"] * 100
        score_log = max(0.0, min(100.0, 50 + 15 * case["log_odds"]))
        print(f"{case['name']}:")
        print(f"  - 예측 확률: {case['prob']:.2%}")
        print(f"  - 방법론 1 (선형 점수): {round(score_lin)}점")
        print(f"  - 방법론 2 (Log-odds 점수): {round(score_log)}점")
        print("-" * 60)

if __name__ == "__main__":
    calculate_scores()
