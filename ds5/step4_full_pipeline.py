"""
Step 4: 전체 파이프라인 자동화
- Step 1-3을 순차적으로 실행
- 진행 상황 추적
- 에러 처리
"""

import pandas as pd
import numpy as np
from pathlib import Path
import time
from datetime import datetime
import sys

# Step 1-3 import
sys.path.append(str(Path(__file__).parent))
from step1_clean_data import clean_daily_file, clean_month_files
from step2_aggregate_scenarios import aggregate_scenarios_monthly, calculate_derived_features
from step3_quarterly_aggregation import aggregate_to_quarters, save_quarterly_data


class DS5Pipeline:
    """DS5 생활인구 데이터 처리 파이프라인"""
    
    def __init__(self, base_dir=None):
        """
        초기화
        
        Parameters:
        -----------
        base_dir : str or Path, optional
            기본 작업 디렉토리 (기본: 현재 디렉토리)
        """
        if base_dir is None:
            self.base_dir = Path.cwd()
        else:
            self.base_dir = Path(base_dir)
        
        # 디렉토리 구조
        self.dirs = {
            'raw': self.base_dir / 'data' / 'raw',
            'cleaned': self.base_dir / 'data' / 'cleaned',
            'scenarios': self.base_dir / 'data' / 'scenarios',
            'quarterly': self.base_dir / 'data' / 'quarterly',
            'logs': self.base_dir / 'logs'
        }
        
        # 디렉토리 생성
        for dir_path in self.dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # 로그 파일
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.log_file = self.dirs['logs'] / f'pipeline_{timestamp}.log'
        
        self.log(f"파이프라인 초기화: {self.base_dir}")
    
    def log(self, message):
        """로그 출력 및 파일 저장"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + '\n')
    
    def run_step1_clean(self, month_dirs):
        """
        Step 1: 데이터 정제
        
        Parameters:
        -----------
        month_dirs : list of Path
            월별 원본 데이터 디렉토리 목록
        """
        self.log("\n" + "="*60)
        self.log("Step 1: 데이터 정제 시작")
        self.log("="*60)
        
        start_time = time.time()
        
        all_cleaned = {}
        
        for month_dir in month_dirs:
            if not month_dir.exists():
                self.log(f"⚠️ 디렉토리 없음: {month_dir}")
                continue
            
            self.log(f"\n처리 중: {month_dir.name}")
            
            try:
                cleaned_files = clean_month_files(month_dir, self.dirs['cleaned'])
                
                if cleaned_files:
                    # 년월 추출
                    year = cleaned_files[0]['year'].iloc[0]
                    month = cleaned_files[0]['month'].iloc[0]
                    year_month = f"{year}-{month:02d}"
                    
                    all_cleaned[year_month] = cleaned_files
                    
                    self.log(f"✅ {year_month}: {len(cleaned_files)}개 파일 정제 완료")
                
            except Exception as e:
                self.log(f"❌ 실패: {month_dir.name}")
                self.log(f"   에러: {e}")
                continue
        
        elapsed = time.time() - start_time
        self.log(f"\nStep 1 완료: {len(all_cleaned)}개월 처리 (소요: {elapsed/60:.1f}분)")
        
        return all_cleaned
    
    def run_step2_scenarios(self, cleaned_data):
        """
        Step 2: 시간대별 시나리오 집계
        
        Parameters:
        -----------
        cleaned_data : dict
            {년월: [DataFrame 리스트]}
        """
        self.log("\n" + "="*60)
        self.log("Step 2: 시나리오 집계 시작")
        self.log("="*60)
        
        start_time = time.time()
        
        scenario_files = []
        
        for year_month, cleaned_files in cleaned_data.items():
            self.log(f"\n처리 중: {year_month}")
            
            try:
                # 월별 시나리오 집계
                df_scenarios = aggregate_scenarios_monthly(cleaned_files)
                
                if df_scenarios is None:
                    self.log(f"⚠️ {year_month}: 시나리오 데이터 없음")
                    continue
                
                # 파생 변수
                df_scenarios = calculate_derived_features(df_scenarios)
                
                # 저장
                output_path = self.dirs['scenarios'] / f'scenarios_{year_month}.parquet'
                df_scenarios.to_parquet(output_path, index=False)
                
                file_size = output_path.stat().st_size / 1024**2
                scenario_files.append(output_path)
                
                self.log(f"✅ {year_month}: {len(df_scenarios):,}개 격자 ({file_size:.1f}MB)")
                
            except Exception as e:
                self.log(f"❌ 실패: {year_month}")
                self.log(f"   에러: {e}")
                continue
        
        elapsed = time.time() - start_time
        self.log(f"\nStep 2 완료: {len(scenario_files)}개월 처리 (소요: {elapsed/60:.1f}분)")
        
        return scenario_files
    
    def run_step3_quarterly(self):
        """
        Step 3: 분기별 집계
        """
        self.log("\n" + "="*60)
        self.log("Step 3: 분기별 집계 시작")
        self.log("="*60)
        
        start_time = time.time()
        
        try:
            # 분기별 집계
            quarterly_data = aggregate_to_quarters(
                self.dirs['scenarios'],
                self.dirs['quarterly']
            )
            
            if not quarterly_data:
                self.log("❌ 분기별 집계 실패!")
                return None
            
            # 저장
            output_file = save_quarterly_data(quarterly_data, self.dirs['quarterly'])
            
            file_size = output_file.stat().st_size / 1024**2
            
            elapsed = time.time() - start_time
            self.log(f"\nStep 3 완료: {len(quarterly_data)}개 분기 (소요: {elapsed/60:.1f}분)")
            self.log(f"최종 파일: {output_file.name} ({file_size:.1f}MB)")
            
            return output_file
            
        except Exception as e:
            self.log(f"❌ Step 3 실패: {e}")
            return None
    
    def run_full_pipeline(self, month_dirs):
        """
        전체 파이프라인 실행
        
        Parameters:
        -----------
        month_dirs : list of Path
            월별 원본 데이터 디렉토리 목록
        """
        self.log("\n" + "="*80)
        self.log("DS5 생활인구 데이터 처리 파이프라인 시작")
        self.log("="*80)
        
        pipeline_start = time.time()
        
        # Step 1: 정제
        cleaned_data = self.run_step1_clean(month_dirs)
        
        if not cleaned_data:
            self.log("\n❌ Step 1 실패! 파이프라인 중단")
            return None
        
        # Step 2: 시나리오
        scenario_files = self.run_step2_scenarios(cleaned_data)
        
        if not scenario_files:
            self.log("\n❌ Step 2 실패! 파이프라인 중단")
            return None
        
        # Step 3: 분기별
        output_file = self.run_step3_quarterly()
        
        if output_file is None:
            self.log("\n❌ Step 3 실패! 파이프라인 중단")
            return None
        
        # 완료
        total_time = time.time() - pipeline_start
        
        self.log("\n" + "="*80)
        self.log("🎉 전체 파이프라인 완료!")
        self.log("="*80)
        self.log(f"총 소요 시간: {total_time/60:.1f}분")
        self.log(f"최종 산출물: {output_file}")
        self.log(f"로그 파일: {self.log_file}")
        
        return output_file


def main():
    """메인 실행 함수"""
    
    print("\n" + "="*80)
    print("DS5 생활인구 데이터 처리 파이프라인")
    print("="*80)
    
    # 파이프라인 초기화
    pipeline = DS5Pipeline()
    
    # 원본 데이터 디렉토리 설정
    # 사용자가 다운로드한 월별 폴더들
    downloads_dir = Path.home() / 'Downloads'
    
    # 2023-01 ~ 2026-04 전체 처리
    month_dirs = []
    
    print("\n📁 월별 디렉토리 검색 중...")
    print(f"검색 위치: {downloads_dir}")
    
    for year in range(2023, 2027):
        for month in range(1, 13):
            # 2026년은 4월까지만
            if year == 2026 and month > 4:
                break
            
            dir_name = f'250_LOCAL_RESD_{year}{month:02d}'
            month_dir = downloads_dir / dir_name
            
            if month_dir.exists():
                month_dirs.append(month_dir)
                print(f"  ✅ {year}-{month:02d}: {dir_name}")
            else:
                print(f"  ⚠️  {year}-{month:02d}: {dir_name} (없음)")
    
    print(f"\n총 {len(month_dirs)}개 디렉토리 발견")
    
    # 존재하는 디렉토리만 필터
    existing_dirs = [d for d in month_dirs if d.exists()]
    
    if not existing_dirs:
        print("\n❌ 처리할 디렉토리가 없습니다!")
        print("\n다운로드 및 압축 해제 필요:")
        print("1. https://data.seoul.go.kr/dataList/OA-22784/S/1/datasetView.do")
        print("2. 월별 zip 파일 다운로드")
        print("3. ~/Downloads/ 에 압축 해제")
        print("4. 이 스크립트 재실행")
        return
    
    print(f"\n처리할 디렉토리: {len(existing_dirs)}개")
    for d in existing_dirs:
        print(f"  - {d.name}")
    
    # 확인
    response = input("\n진행하시겠습니까? (y/n): ")
    if response.lower() != 'y':
        print("취소되었습니다.")
        return
    
    # 파이프라인 실행
    output_file = pipeline.run_full_pipeline(existing_dirs)
    
    if output_file:
        print("\n" + "="*80)
        print("다음 단계:")
        print("  1. 블록-격자 Spatial Join")
        print("  2. 격자 → 블록 변환")
        print("  3. DS2 상권분석 데이터와 조인")
        print("="*80)


if __name__ == "__main__":
    main()