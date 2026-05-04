"""
simulation/backtest.py
-----------------------
담당: 팀원 C (시뮬레이션 파트)

목적: 과거 20년치 인허가/폐업 데이터를 활용하여
      특정 시점을 기준으로 학습 데이터와 검증 데이터를 분리하고,
      생존 기간 예측의 타당성을 백테스팅(Backtesting)으로 검증합니다.

검증 논리:
    1. TRAIN: 특정 연도(cutoff_year) 이전에 개업한 점포의 실제 생존 데이터로 학습
    2. TEST: cutoff_year 이후에 예측한 생존 기간 vs 실제 폐업 시점 비교
    3. Metric: C-index (Concordance Index), 생존 곡선 시각화
"""

import pandas as pd


def temporal_split(df: pd.DataFrame, cutoff_year: int):
    """
    cutoff_year를 기준으로 훈련/검증 데이터를 시간 순서대로 분리합니다.

    Args:
        df (pd.DataFrame): 점포별 개업일, 폐업일, 피처 컬럼이 포함된 데이터
        cutoff_year (int): 학습/검증 분리 기준 연도 (예: 2015)

    Returns:
        train_df, test_df (pd.DataFrame, pd.DataFrame)
    """
    # TODO: 개업일 컬럼을 기준으로 cutoff_year 이전/이후로 분리
    raise NotImplementedError("temporal_split() 구현 필요")


def run_backtest(df: pd.DataFrame, cutoff_year: int):
    """백테스팅 전체 파이프라인을 실행합니다."""
    train_df, test_df = temporal_split(df, cutoff_year)
    # TODO: 모델 학습 → 예측 → 검증 지표 계산
    raise NotImplementedError("run_backtest() 구현 필요")
