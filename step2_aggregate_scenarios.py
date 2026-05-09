"""
Step 2: 시간대별 시나리오 집계
- 주중 오전/점심/저녁/야간
- 주말 주간/야간
- 격자별 평균 계산
"""

import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm


def aggregate_scenarios_daily(df):
    """
    하루치 데이터에서 시나리오별 집계
    
    Parameters:
    -----------
    df : DataFrame
        정제된 일별 데이터 (clean_data.py 출력)
    
    Returns:
    --------
    DataFrame : 시나리오별 격자 평균
    """
    
    # 시나리오 정의
    scenarios = {
        '주중_오전': (df['is_weekday'] == True) & (df['hour'].between(7, 9)),
        '주중_점심': (df['is_weekday'] == True) & (df['hour'].between(11, 14)),
        '주중_저녁': (df['is_weekday'] == True) & (df['hour'].between(18, 21)),
        '주중_야간': (df['is_weekday'] == True) & (df['hour'].between(21, 23)),
        '주말_주간': (df['is_weekday'] == False) & (df['hour'].between(10, 18)),
        '주말_야간': (df['is_weekday'] == False) & (df['hour'].between(18, 23)),
    }
    
    # 각 시나리오별 격자 평균
    results = {}
    
    for scenario_name, condition in scenarios.items():
        scenario_data = df[condition].copy()
        
        if len(scenario_data) == 0:
            # 해당 시나리오 데이터 없음 (예: 주말만 있는 데이터)
            continue
        
        # 격자별 평균
        grid_avg = scenario_data.groupby('grid_id').agg({
            'population': ['mean', 'std', 'count']
        }).reset_index()
        
        grid_avg.columns = ['grid_id', f'{scenario_name}_avg', 
                           f'{scenario_name}_std', f'{scenario_name}_count']
        
        results[scenario_name] = grid_avg
    
    return results


def aggregate_scenarios_monthly(cleaned_files):
    """
    한 달치 파일들을 통합하여 월별 시나리오 집계
    
    Parameters:
    -----------
    cleaned_files : list of DataFrame
        정제된 일별 데이터 리스트
    
    Returns:
    --------
    DataFrame : 월별 시나리오별 격자 평균
    """
    
    print("\n시나리오별 집계 중...")
    
    # 모든 일별 데이터 통합
    df_month = pd.concat(cleaned_files, ignore_index=True)
    
    print(f"총 데이터: {len(df_month):,}행")
    print(f"기간: {df_month['date'].min()} ~ {df_month['date'].max()}")
    print(f"격자 수: {df_month['grid_id'].nunique():,}개")
    
    # 시나리오 정의
    scenarios = {
        '주중_오전': (df_month['is_weekday'] == True) & (df_month['hour'].between(7, 9)),
        '주중_점심': (df_month['is_weekday'] == True) & (df_month['hour'].between(11, 14)),
        '주중_저녁': (df_month['is_weekday'] == True) & (df_month['hour'].between(18, 21)),
        '주중_야간': (df_month['is_weekday'] == True) & (df_month['hour'].between(21, 23)),
        '주말_주간': (df_month['is_weekday'] == False) & (df_month['hour'].between(10, 18)),
        '주말_야간': (df_month['is_weekday'] == False) & (df_month['hour'].between(18, 23)),
    }
    
    # 각 시나리오별 집계
    scenario_results = {}
    
    for scenario_name, condition in tqdm(scenarios.items(), desc="시나리오 처리"):
        scenario_data = df_month[condition].copy()
        
        if len(scenario_data) == 0:
            print(f"  ⚠️ {scenario_name}: 데이터 없음")
            continue
        
        # 격자별 평균
        grid_avg = scenario_data.groupby('grid_id').agg({
            'population': ['mean', 'std', 'max', 'count']
        }).reset_index()
        
        grid_avg.columns = ['grid_id', 
                           f'{scenario_name}_avg',
                           f'{scenario_name}_std',
                           f'{scenario_name}_max',
                           f'{scenario_name}_count']
        
        scenario_results[scenario_name] = grid_avg
        
        # 통계 출력
        avg_pop = grid_avg[f'{scenario_name}_avg'].mean()
        print(f"  {scenario_name}: 평균 {avg_pop:,.0f}명")
    
    # 모든 시나리오 병합
    print("\n시나리오 병합 중...")
    
    if not scenario_results:
        print("❌ 시나리오 데이터가 없습니다!")
        return None
    
    # 첫 번째 시나리오를 베이스로
    final = list(scenario_results.values())[0]
    
    # 나머지 시나리오 조인
    for scenario_name, data in list(scenario_results.items())[1:]:
        final = final.merge(data, on='grid_id', how='outer')
    
    # 년월 정보 추가
    year_month = df_month['date'].dt.to_period('M').iloc[0]
    final['year_month'] = str(year_month)
    final['year'] = df_month['year'].iloc[0]
    final['month'] = df_month['month'].iloc[0]
    
    # 결측치를 0으로 (해당 시나리오에 데이터 없는 격자)
    final = final.fillna(0)
    
    print(f"✅ 최종: {len(final):,}개 격자")
    
    return final


def calculate_derived_features(df):
    """
    파생 변수 계산
    
    주중/주말 비율, 피크 시간대 등
    """
    
    print("\n파생 변수 계산 중...")
    
    # 주중 평균
    weekday_cols = [col for col in df.columns if '주중' in col and '_avg' in col]
    if weekday_cols:
        df['주중_평균'] = df[weekday_cols].mean(axis=1)
    
    # 주말 평균
    weekend_cols = [col for col in df.columns if '주말' in col and '_avg' in col]
    if weekend_cols:
        df['주말_평균'] = df[weekend_cols].mean(axis=1)
    
    # 주중/주말 비율
    if '주중_평균' in df.columns and '주말_평균' in df.columns:
        df['주말주중_비율'] = df['주말_평균'] / (df['주중_평균'] + 1)
    
    # 피크 시간대 찾기
    scenario_avg_cols = [col for col in df.columns if '_avg' in col 
                        and '주중' in col or '주말' in col]
    if scenario_avg_cols:
        df['피크_시나리오'] = df[scenario_avg_cols].idxmax(axis=1)
        df['피크_인구'] = df[scenario_avg_cols].max(axis=1)
    
    # 변동성 (표준편차 평균)
    std_cols = [col for col in df.columns if '_std' in col]
    if std_cols:
        df['변동성'] = df[std_cols].mean(axis=1)
    
    print("✅ 파생 변수 추가 완료")
    
    return df


def save_monthly_scenarios(df, output_path):
    """
    월별 시나리오 데이터 저장
    """
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_parquet(output_path, index=False)
    
    file_size = output_path.stat().st_size / 1024**2
    
    print(f"\n💾 저장: {output_path.name} ({file_size:.1f}MB)")
    
    return output_path


def main():
    """메인 실행 함수"""
    
    print("\n" + "="*60)
    print("Step 2: 시간대별 시나리오 집계")
    print("="*60)
    
    # 정제된 데이터 로드
    cleaned_dir = Path('data/cleaned')
    
    if not cleaned_dir.exists():
        print(f"❌ 정제된 데이터가 없습니다: {cleaned_dir}")
        print("먼저 step1_clean_data.py를 실행하세요!")
        return
    
    # 정제된 파일들 로드
    parquet_files = sorted(cleaned_dir.glob('*_clean.parquet'))
    
    if not parquet_files:
        print(f"❌ Parquet 파일이 없습니다: {cleaned_dir}")
        return
    
    print(f"\n파일 수: {len(parquet_files)}개")
    
    # 모든 파일 로드
    cleaned_files = []
    for file in tqdm(parquet_files, desc="파일 로드"):
        df = pd.read_parquet(file)
        cleaned_files.append(df)
    
    # 월별 시나리오 집계
    df_scenarios = aggregate_scenarios_monthly(cleaned_files)
    
    if df_scenarios is None:
        return
    
    # 파생 변수 계산
    df_scenarios = calculate_derived_features(df_scenarios)
    
    # 저장
    year_month = df_scenarios['year_month'].iloc[0]
    output_path = Path('data/scenarios') / f'scenarios_{year_month}.parquet'
    
    save_monthly_scenarios(df_scenarios, output_path)
    
    # 요약 출력
    print("\n" + "="*60)
    print("시나리오 집계 완료!")
    print("="*60)
    print(f"격자 수: {len(df_scenarios):,}개")
    print(f"년월: {year_month}")
    print(f"컬럼 수: {len(df_scenarios.columns)}")
    
    # 시나리오별 평균 출력
    print("\n시나리오별 평균 인구:")
    scenario_cols = [col for col in df_scenarios.columns if '_avg' in col 
                    and ('주중' in col or '주말' in col)]
    for col in scenario_cols:
        avg = df_scenarios[col].mean()
        print(f"  {col:20s}: {avg:10,.0f}명")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()