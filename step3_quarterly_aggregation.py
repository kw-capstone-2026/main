"""
Step 3: 월별 시나리오 → 분기별 집계
- 3개월 데이터를 분기별로 통합
- 2023Q1 = 2023-01, 02, 03 평균
"""

import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm


def get_quarter_from_month(year, month):
    """
    년월 → 년분기 변환
    
    예: 2023, 1 → "2023Q1"
    """
    quarter = (month - 1) // 3 + 1
    return f"{year}Q{quarter}"


def aggregate_to_quarters(scenarios_dir, output_dir=None):
    """
    월별 시나리오 파일들을 분기별로 집계
    
    Parameters:
    -----------
    scenarios_dir : str or Path
        월별 시나리오 파일들이 있는 디렉토리
    output_dir : str or Path, optional
        출력 디렉토리
    
    Returns:
    --------
    dict : 분기별 DataFrame {년분기: DataFrame}
    """
    
    scenarios_dir = Path(scenarios_dir)
    
    if output_dir is None:
        output_dir = scenarios_dir.parent / 'quarterly'
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*60)
    print("Step 3: 월별 → 분기별 집계")
    print("="*60)
    
    # 월별 파일 찾기
    scenario_files = sorted(scenarios_dir.glob('scenarios_*.parquet'))
    
    if not scenario_files:
        print(f"❌ 시나리오 파일이 없습니다: {scenarios_dir}")
        return {}
    
    print(f"\n월별 파일 수: {len(scenario_files)}개")
    
    # 월별 데이터 로드 및 분기별 그룹화
    monthly_data = {}
    
    for file in tqdm(scenario_files, desc="파일 로드"):
        df = pd.read_parquet(file)
        year_month = df['year_month'].iloc[0]
        year = df['year'].iloc[0]
        month = df['month'].iloc[0]
        
        quarter = get_quarter_from_month(year, month)
        
        if quarter not in monthly_data:
            monthly_data[quarter] = []
        
        monthly_data[quarter].append(df)
        
    print(f"\n분기 수: {len(monthly_data)}개")
    for quarter in sorted(monthly_data.keys()):
        print(f"  {quarter}: {len(monthly_data[quarter])}개월")
    
    # 분기별 집계
    quarterly_data = {}
    
    print("\n분기별 집계 중...")
    
    for quarter in tqdm(sorted(monthly_data.keys()), desc="분기 처리"):
        months = monthly_data[quarter]
        
        # 해당 분기의 모든 월 데이터 통합
        df_quarter = pd.concat(months, ignore_index=True)
        
        # 격자별 평균 계산
        # 숫자 컬럼만 평균
        numeric_cols = df_quarter.select_dtypes(include=[np.number]).columns.tolist()
        numeric_cols.remove('year')
        numeric_cols.remove('month')
        
        agg_dict = {col: 'mean' for col in numeric_cols}
        
        df_agg = df_quarter.groupby('grid_id').agg(agg_dict).reset_index()
        
        # 분기 정보 추가
        df_agg['년분기'] = quarter
        df_agg['year'] = int(quarter[:4])
        df_agg['quarter'] = int(quarter[-1])
        
        quarterly_data[quarter] = df_agg
        
        # 통계
        grid_count = len(df_agg)
        avg_pop = df_agg[[col for col in df_agg.columns 
                         if '_avg' in col and ('주중' in col or '주말' in col)]].mean().mean()
        
        print(f"  {quarter}: {grid_count:,}개 격자, 평균 {avg_pop:,.0f}명")
    
    return quarterly_data


def save_quarterly_data(quarterly_data, output_dir):
    """
    분기별 데이터 저장
    
    Parameters:
    -----------
    quarterly_data : dict
        {년분기: DataFrame}
    output_dir : str or Path
        출력 디렉토리
    """
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n분기별 파일 저장 중...")
    
    saved_files = []
    
    for quarter, df in tqdm(quarterly_data.items(), desc="파일 저장"):
        output_path = output_dir / f'quarterly_{quarter}.parquet'
        df.to_parquet(output_path, index=False)
        
        file_size = output_path.stat().st_size / 1024**2
        saved_files.append((quarter, output_path, file_size))
    
    # 통합 파일도 저장
    print("\n통합 파일 생성 중...")
    df_all = pd.concat(quarterly_data.values(), ignore_index=True)
    
    output_all = output_dir / 'grid_quarterly_all.parquet'
    df_all.to_parquet(output_all, index=False)
    
    file_size_all = output_all.stat().st_size / 1024**2
    
    print("\n💾 저장 완료:")
    for quarter, path, size in saved_files:
        print(f"  {quarter}: {path.name} ({size:.1f}MB)")
    
    print(f"\n  통합: {output_all.name} ({file_size_all:.1f}MB)")
    
    return output_all


def generate_summary_report(quarterly_data):
    """
    분기별 요약 리포트 생성
    """
    
    print("\n" + "="*60)
    print("분기별 집계 요약")
    print("="*60)
    
    for quarter in sorted(quarterly_data.keys()):
        df = quarterly_data[quarter]
        
        print(f"\n{quarter}:")
        print(f"  격자 수: {len(df):,}개")
        
        # 시나리오별 평균
        scenario_cols = [col for col in df.columns 
                        if '_avg' in col and ('주중' in col or '주말' in col)]
        
        for col in sorted(scenario_cols):
            avg = df[col].mean()
            std = df[col].std()
            max_val = df[col].max()
            print(f"    {col:25s}: 평균 {avg:8,.0f}명 (σ={std:6,.0f}, max={max_val:8,.0f})")
    
    # 전체 통계
    print("\n" + "="*60)
    print("전체 통계:")
    print("="*60)
    
    df_all = pd.concat(quarterly_data.values(), ignore_index=True)
    
    print(f"총 행 수: {len(df_all):,}")
    print(f"고유 격자: {df_all['grid_id'].nunique():,}개")
    print(f"분기 수: {df_all['년분기'].nunique()}개")
    print(f"기간: {df_all['년분기'].min()} ~ {df_all['년분기'].max()}")
    
    # 컬럼별 통계
    print("\n주요 컬럼 통계:")
    scenario_cols = [col for col in df_all.columns 
                    if '_avg' in col and ('주중' in col or '주말' in col)]
    
    for col in sorted(scenario_cols):
        stats = df_all[col].describe()
        print(f"\n  {col}:")
        print(f"    평균: {stats['mean']:,.0f}명")
        print(f"    중앙값: {stats['50%']:,.0f}명")
        print(f"    최대: {stats['max']:,.0f}명")
        print(f"    표준편차: {stats['std']:,.0f}")


def main():
    """메인 실행 함수"""
    
    scenarios_dir = Path('data/scenarios')
    output_dir = Path('data/quarterly')
    
    if not scenarios_dir.exists():
        print(f"❌ 시나리오 디렉토리가 없습니다: {scenarios_dir}")
        print("먼저 step2_aggregate_scenarios.py를 실행하세요!")
        return
    
    # 분기별 집계
    quarterly_data = aggregate_to_quarters(scenarios_dir, output_dir)
    
    if not quarterly_data:
        print("❌ 집계 실패!")
        return
    
    # 저장
    output_file = save_quarterly_data(quarterly_data, output_dir)
    
    # 요약 리포트
    generate_summary_report(quarterly_data)
    
    print("\n" + "="*60)
    print("✅ Step 3 완료!")
    print("="*60)
    print(f"\n최종 산출물: {output_file}")
    print("\n다음 단계:")
    print("  → Step 4: 블록 변환 (격자 → 블록)")


if __name__ == "__main__":
    main()