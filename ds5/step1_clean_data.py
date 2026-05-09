"""
Step 1: 생활인구 데이터 정제
- "*" 문자를 NaN 또는 0으로 변환
- 문자열 숫자를 float으로 변환
- 필요한 컬럼만 추출
"""

import pandas as pd
import numpy as np
from pathlib import Path


def clean_population_value(value):
    """
    생활인구 값 정제
    
    "*" → 0 (3명 이하 마스킹)
    숫자 문자열 → float
    """
    if pd.isna(value):
        return 0.0
    
    if value == '*':
        return 0.0  # 또는 np.nan
    
    try:
        return float(value)
    except:
        return 0.0


def clean_daily_file(input_path, output_dir=None):
    """
    일별 CSV 파일 정제
    
    Parameters:
    -----------
    input_path : str or Path
        입력 CSV 파일 경로
    output_dir : str or Path, optional
        출력 디렉토리 (기본: 입력 파일과 같은 폴더)
    
    Returns:
    --------
    DataFrame : 정제된 데이터
    """
    input_path = Path(input_path)
    
    if output_dir is None:
        output_dir = input_path.parent / 'cleaned'
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n처리 중: {input_path.name}")
    
    # 1. CSV 로드
    try:
        df = pd.read_csv(input_path, encoding='cp949')
    except UnicodeDecodeError:
        df = pd.read_csv(input_path, encoding='euc-kr')
    
    print(f"  원본: {len(df):,}행 × {len(df.columns)}컬럼")
    
    # 2. 필요한 컬럼만 선택
    essential_cols = ['일자', '시간', '행정동코드', '250M격자', '생활인구합계']
    
    df_clean = df[essential_cols].copy()
    
    # 3. 컬럼명 영문으로 변경 (처리 편의)
    df_clean.columns = ['date', 'hour', 'admin_code', 'grid_id', 'population']
    
    # 4. 생활인구 정제
    original_count = len(df_clean)
    df_clean['population'] = df_clean['population'].apply(clean_population_value)
    
    # 5. 통계
    zero_count = (df_clean['population'] == 0).sum()
    zero_pct = zero_count / len(df_clean) * 100
    
    print(f"  정제 완료: {len(df_clean):,}행")
    print(f"  0값 (마스킹): {zero_count:,}개 ({zero_pct:.1f}%)")
    print(f"  평균 인구: {df_clean['population'].mean():.1f}명")
    print(f"  최대 인구: {df_clean['population'].max():.0f}명")
    
    # 6. 날짜 형식 변환
    df_clean['date'] = pd.to_datetime(df_clean['date'], format='%Y%m%d')
    df_clean['year'] = df_clean['date'].dt.year
    df_clean['month'] = df_clean['date'].dt.month
    df_clean['day'] = df_clean['date'].dt.day
    df_clean['weekday'] = df_clean['date'].dt.dayofweek  # 0=월, 6=일
    
    # 7. 주중/주말 구분
    df_clean['is_weekday'] = df_clean['weekday'] < 5
    df_clean['day_type'] = df_clean['is_weekday'].map({True: '주중', False: '주말'})
    
    # 8. 저장
    output_path = output_dir / f"{input_path.stem}_clean.parquet"
    df_clean.to_parquet(output_path, index=False)
    
    file_size = output_path.stat().st_size / 1024**2
    print(f"  저장: {output_path.name} ({file_size:.1f}MB)")
    
    return df_clean


def clean_month_files(month_dir, output_dir=None):
    """
    한 달치 모든 파일 정제
    
    Parameters:
    -----------
    month_dir : str or Path
        월별 CSV 파일들이 있는 디렉토리
    output_dir : str or Path, optional
        출력 디렉토리
    """
    month_dir = Path(month_dir)
    
    # CSV 파일 찾기
    csv_files = sorted(month_dir.glob('250_LOCAL_RESD_*.csv'))
    
    if not csv_files:
        print(f"❌ CSV 파일을 찾을 수 없습니다: {month_dir}")
        return []
    
    print(f"\n{'='*60}")
    print(f"월별 파일 정제: {month_dir.name}")
    print(f"파일 수: {len(csv_files)}개")
    print(f"{'='*60}")
    
    cleaned_files = []
    
    for csv_file in csv_files:
        try:
            df_clean = clean_daily_file(csv_file, output_dir)
            cleaned_files.append(df_clean)
        except Exception as e:
            print(f"  ❌ 실패: {csv_file.name}")
            print(f"     에러: {e}")
            continue
    
    print(f"\n✅ 완료: {len(cleaned_files)}/{len(csv_files)}개 파일 정제")
    
    return cleaned_files


def main():
    """메인 실행 함수"""
    
    print("\n" + "="*60)
    print("Step 1: 생활인구 데이터 정제")
    print("="*60)
    
    # 예시: 단일 파일 정제
    # input_file = '250_LOCAL_RESD_20260301.csv'
    # df = clean_daily_file(input_file)
    
    # 예시: 월별 폴더의 모든 파일 정제
    month_dir = Path.home() / 'Downloads' / '250_LOCAL_RESD_202603'
    output_dir = Path('data/cleaned')
    
    if month_dir.exists():
        cleaned_files = clean_month_files(month_dir, output_dir)
        
        if cleaned_files:
            # 통합 통계
            total_rows = sum(len(df) for df in cleaned_files)
            total_grids = len(set().union(*[set(df['grid_id'].unique()) 
                                            for df in cleaned_files]))
            
            print(f"\n{'='*60}")
            print("전체 통계:")
            print(f"  총 행 수: {total_rows:,}")
            print(f"  고유 격자: {total_grids:,}개")
            print(f"  일 수: {len(cleaned_files)}일")
            print(f"={'='*60}\n")
    else:
        print(f"\n⚠️ 디렉토리를 찾을 수 없습니다: {month_dir}")
        print("\n사용법:")
        print("1. 월별 zip 파일 압축 해제")
        print("2. month_dir 경로 수정")
        print("3. 스크립트 실행")


if __name__ == "__main__":
    main()