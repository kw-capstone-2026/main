"""추가 분석 실행 스크립트 — step4 + step5.

step1~3 (팀원 파이프라인) 이 먼저 실행되어 있어야 합니다.
실행: python run_extra.py
"""
import step4_extra_agg
import step5_extra_plots

print("=" * 55)
print("STEP 4: 집계 (공간·생존·시계열 파생 피처)")
print("=" * 55)
step4_extra_agg.main()

print()
print("=" * 55)
print("STEP 5: 차트 생성 (14~18)")
print("=" * 55)
step5_extra_plots.main()
