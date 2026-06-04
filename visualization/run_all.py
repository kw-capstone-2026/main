"""전체 파이프라인 한 번에 실행.

  python run_all.py

순서: step1(모델) → step2(집계) → step3(차트)
"""
import step1_model
import step2_aggregate
import step3_plots

if __name__ == "__main__":
    print("[1/3] 전처리 + 모델 학습 ...")
    step1_model.main()
    print("\n[2/3] 진단 집계 ...")
    step2_aggregate.main()
    print("\n[3/3] 차트 생성 ...")
    step3_plots.main()
    print("\n완료. output/charts/ 를 확인하세요.")
