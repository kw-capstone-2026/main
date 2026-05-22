#!/bin/bash

# DS5 효과 검증 실험 전체 실행

echo "======================================================================"
echo "DS5 효과 검증 실험"
echo "======================================================================"
echo ""
echo "실험 구성:"
echo "  1단계: 데이터 준비 (2023-2024 기간 추출)"
echo "  2단계: 모델 학습"
echo "    2A: Baseline (DS5 제외)"
echo "    2B: Proposed (DS5 포함)"
echo "  3단계: 결과 비교 및 분석"
echo ""
echo "======================================================================"
echo ""

# 환경 확인
if [[ "$CONDA_DEFAULT_ENV" != "ds5" ]]; then
    echo "⚠️  ds5 환경이 활성화되지 않았습니다."
    echo "   다음 명령어를 실행하세요:"
    echo "   conda activate ds5"
    echo ""
    exit 1
fi

echo "✅ 환경: $CONDA_DEFAULT_ENV"
echo ""

# 폴더 생성
mkdir -p src/experiments
mkdir -p results
mkdir -p data

echo "======================================================================"
echo "1단계: 데이터 준비"
echo "======================================================================"
echo ""

python src/experiments/prepare_ds5_period.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ 데이터 준비 실패"
    exit 1
fi

echo ""
echo "======================================================================"
echo "2A단계: Baseline 모델 학습 (DS5 제외)"
echo "======================================================================"
echo ""

python src/experiments/train_baseline_model.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Baseline 모델 학습 실패"
    exit 1
fi

echo ""
echo "======================================================================"
echo "2B단계: Proposed 모델 학습 (DS5 포함)"
echo "======================================================================"
echo ""

python src/experiments/train_proposed_model.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Proposed 모델 학습 실패"
    exit 1
fi

echo ""
echo "======================================================================"
echo "3단계: 결과 비교 및 분석"
echo "======================================================================"
echo ""

python src/experiments/compare_results.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ 결과 비교 실패"
    exit 1
fi

echo ""
echo "======================================================================"
echo "실험 완료!"
echo "======================================================================"
echo ""
echo "결과 확인:"
echo "  cat results/comparison_report.md"
echo ""
echo "생성된 파일:"
echo "  📊 results/comparison_report.md         (보고서)"
echo "  📊 results/comparison_summary.json      (요약)"
echo "  📊 results/baseline_results.json        (Baseline 상세)"
echo "  📊 results/proposed_results.json        (Proposed 상세)"
echo "  💾 results/baseline_model.pkl           (Baseline 모델)"
echo "  💾 results/proposed_model.pkl           (Proposed 모델)"
echo ""
