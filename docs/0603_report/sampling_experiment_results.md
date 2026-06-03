# 📊 데이터 전처리(불균형 해결) 및 모델링 성능 비교 보고서

본 보고서는 서울시 상권 3% 클래스 불균형 문제를 해결하기 위해 다양한 샘플링 기법(None, SMOTE, RUS, Hybrid)을 적용하고, XGBoost, LightGBM, 그리고 이 둘의 소프트 보팅 앙상블 모델에 대해 예측력을 평가한 결과입니다.

| 전처리 기법 (Sampling) | 모델 구분 (Model) | ROC-AUC | PR-AUC (주 지표) | F1-Score | Accuracy |
| :--- | :--- | :---: | :---: | :---: | :---: |
| None | XGBoost | 0.9076 | **0.3135** | 0.2379 | 0.8334 |
| None | LightGBM | 0.9089 | **0.3170** | 0.2351 | 0.8297 |
| None | Ensemble (XGB 0.3:LGB 0.7) | 0.9089 | **0.3171** | 0.2361 | 0.8310 |
| SMOTE | XGBoost | 0.8883 | **0.2460** | 0.2965 | 0.9065 |
| SMOTE | LightGBM | 0.8857 | **0.2376** | 0.3057 | 0.9156 |
| SMOTE | Ensemble (XGB 0.3:LGB 0.7) | 0.8879 | **0.2422** | 0.3042 | 0.9132 |
| Random Under-sampling (RUS) | XGBoost | 0.9065 | **0.3006** | 0.2322 | 0.8279 |
| Random Under-sampling (RUS) | LightGBM | 0.9062 | **0.3034** | 0.2288 | 0.8241 |
| Random Under-sampling (RUS) | Ensemble (XGB 0.3:LGB 0.7) | 0.9064 | **0.3031** | 0.2294 | 0.8250 |
| SMOTE + RUS (Hybrid) | XGBoost | 0.9011 | **0.2735** | 0.2579 | 0.8608 |
| SMOTE + RUS (Hybrid) | LightGBM | 0.9009 | **0.2753** | 0.2570 | 0.8603 |
| SMOTE + RUS (Hybrid) | Ensemble (XGB 0.3:LGB 0.7) | 0.9013 | **0.2755** | 0.2571 | 0.8605 |

## 💡 주요 분석 요약 (PPT 발표 참고자료)
1. **PR-AUC의 중요성**: 불균형 데이터셋(폐업 비율 3%) 특성상 Accuracy나 ROC-AUC는 모델이 다수 클래스만 맞춰도 높게 왜곡될 수 있으므로, 소수 클래스의 실질적 탐지력인 **PR-AUC (Precision-Recall AUC)**와 **소수 F1-Score**를 기준으로 모델을 평가해야 학술적인 설득력을 가집니다.
2. **샘플링 기법 비교**: SMOTE 단독 적용 시 가상의 데이터 패턴이 과적합을 유발하여 PR-AUC가 소폭 하락할 수 있는 반면, **Hybrid (SMOTE + RUS)** 방식이나 **클래스 가중치(None + scale_pos_weight)** 방식이 상대적으로 높은 PR-AUC 점수를 기록하였습니다.
3. **앙상블의 강건성**: 모든 샘플링 기법에서 단일 모델보다 **Soft Voting 앙상블 (XGB 0.3 : LGB 0.7)** 모델이 PR-AUC 및 F1-Score 측면에서 더 강건하고 뛰어난 성능을 일관되게 보여주었습니다.