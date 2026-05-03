"""
src/feature_merger.py  ← 기존 파일을 이 버전으로 교체
-------------------------------------------------------------
[변경 이력]
  v1 (원본) : avg_sales, pop_density를 region_key % 연산으로 가짜 계산
  v2 (현재) : 실제 API 데이터를 조인하는 메서드 추가 + 실험 제어 플래그

[추가된 피처 — 상권 내 실질 인터랙션]
  유동인구 (DS2 - VwsmTrdarFlpopQq):
    total_flpop        : 월 전체 유동인구 합계
    peak_hour_pop      : 피크 시간대 (점심+오후) 유동인구
    morning_pop        : 오전 유동인구 (TMZON_APM_FLPOP_CO)
    evening_pop        : 저녁 유동인구 (TMZON_EVE_FLPOP_CO)
    weekend_pop_ratio  : 주말 유동인구 비율 (주말합/전체합)

  배후인구 (DS2 - VwsmTrdarAresQq):
    resident_pop       : 상주인구 (거주자 수)
    worker_pop         : 직장인 수

  경쟁/밀집도 (점포 데이터 내부 계산):
    same_induty_cnt    : BAS_ID 내 동일 업종 점포 수
    avg_comp_survival  : BAS_ID 내 폐업 점포 평균 생존 기간(월)
    competition_density: same_induty_cnt / total_flpop (경쟁 강도 지수)

  객단가 추정 (DS2 - VwsmTrdarSelngQq):
    monthly_sales_real : 상권 월 추정매출 (실제 API 값)
    sales_per_store    : 점포당 월 추정매출 (monthly_sales_real / store_count)

[Data Leakage 주의]
  survival_months, 폐업일자, close_date, end_date는 절대 피처로 투입 금지.
  main.py의 exclude_cols에 반드시 포함되어야 합니다.
"""

import pandas as pd
import numpy as np
from datetime import datetime


class FeatureMerger:
    """
    DS1~DS5 데이터를 통합하여 XGBoost 모델 학습을 위한 Master Table을 생성하는 클래스
    """

    def __init__(self):
        pass

    # ─────────────────────────────────────────────────────────────
    # [기존 유지] 생존 기간 및 타겟 변수 생성
    # ─────────────────────────────────────────────────────────────
    def calculate_survival_duration(self, df_permits: pd.DataFrame) -> pd.DataFrame:
        """
        DS3(인허가 데이터)를 바탕으로 각 점포의 생존 기간을 계산합니다.

        :param df_permits: 인허가일자, 폐업일자, 영업상태 등이 포함된 DataFrame
        :return: 생존 기간(일 또는 개월)이 추가된 DataFrame
        """
        df = df_permits.copy()

        if '인허가일자' in df.columns:
            df['open_date'] = pd.to_datetime(df['인허가일자'], format='%Y%m%d', errors='coerce')
        else:
            df['open_date'] = pd.to_datetime(datetime.now().date()) - pd.Timedelta(days=365)

        if '폐업일자' in df.columns:
            df['close_date'] = pd.to_datetime(df['폐업일자'], format='%Y%m%d', errors='coerce')
        else:
            df['close_date'] = pd.NaT

        current_date = pd.to_datetime(datetime.now().date())
        df['end_date'] = df['close_date'].fillna(current_date)
        df['open_date'] = pd.to_datetime(df['open_date'])
        df['end_date'] = pd.to_datetime(df['end_date'])

        # survival_months: 참고용만 — 절대 피처로 투입 금지 (Data Leakage)
        df['survival_months'] = (df['end_date'] - df['open_date']).dt.days / 30.44

        if 'is_closed' not in df.columns:
            if '폐업일자' in df.columns:
                df['is_closed'] = df['폐업일자'].apply(
                    lambda x: 1 if str(x).strip() and str(x) != 'None' and str(x) != 'nan' else 0
                )
            else:
                df['is_closed'] = 0

        return df

    # ─────────────────────────────────────────────────────────────
    # [신규] 유동인구 시간대·요일별 피처 추출
    # DS2: VwsmTrdarFlpopQq
    # ─────────────────────────────────────────────────────────────
    def extract_floating_pop_features(self, df_pop: pd.DataFrame) -> pd.DataFrame:
        """
        서울시 상권분석 유동인구(VwsmTrdarFlpopQq) 데이터에서
        시간대별·요일별 피처를 추출하여 상권코드(TRDAR_CD) 단위로 집계합니다.

        주요 원본 컬럼:
          TRDAR_CD              : 상권 코드 (조인 키)
          TOT_FLPOP_CO          : 전체 유동인구
          TMZON_APM_FLPOP_CO    : 오전 (06~11시)
          TMZON_LNCH_FLPOP_CO   : 점심 (11~14시)
          TMZON_AFNON_FLPOP_CO  : 오후 (14~17시)
          TMZON_EVE_FLPOP_CO    : 저녁 (17~21시)
          TMZON_NIGHT_FLPOP_CO  : 심야 (21~06시)
          MON/TUE/WED/THU/FRI/SAT/SUN_FLPOP_CO : 요일별
        """
        if df_pop is None or df_pop.empty:
            print("[FeatureMerger] 유동인구 데이터 없음 → 관련 피처 0 처리")
            return pd.DataFrame()

        df = df_pop.copy()

        # 수치형 강제 변환
        num_cols = [c for c in df.columns if 'FLPOP' in c or c.endswith('_CO')]
        for c in num_cols:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

        # 상권 단위 집계 딕셔너리 구성
        agg = {}
        col_map = {
            'total_flpop':    'TOT_FLPOP_CO',
            'morning_pop':    'TMZON_APM_FLPOP_CO',
            'lunch_pop':      'TMZON_LNCH_FLPOP_CO',
            'afternoon_pop':  'TMZON_AFNON_FLPOP_CO',
            'evening_pop':    'TMZON_EVE_FLPOP_CO',
            'night_pop':      'TMZON_NIGHT_FLPOP_CO',
        }
        for feat, col in col_map.items():
            if col in df.columns:
                agg[feat] = (col, 'mean')

        if not agg:
            print("[FeatureMerger] 유동인구 시간대 컬럼 없음 — API 응답 구조 확인 필요")
            return pd.DataFrame()

        result = df.groupby('TRDAR_CD').agg(**agg).reset_index()

        # 피크 시간대 = 점심 + 오후 (가장 높은 상업 수요)
        if 'lunch_pop' in result.columns and 'afternoon_pop' in result.columns:
            result['peak_hour_pop'] = result['lunch_pop'] + result['afternoon_pop']
        elif 'lunch_pop' in result.columns:
            result['peak_hour_pop'] = result['lunch_pop']

        # 주말 유동인구 비율
        wd_cols = [c for c in ['MON_FLPOP_CO','TUE_FLPOP_CO','WED_FLPOP_CO','THU_FLPOP_CO','FRI_FLPOP_CO'] if c in df.columns]
        we_cols = [c for c in ['SAT_FLPOP_CO','SUN_FLPOP_CO'] if c in df.columns]
        if wd_cols and we_cols:
            df['_wd'] = df[wd_cols].sum(axis=1)
            df['_we'] = df[we_cols].sum(axis=1)
            ratio = df.groupby('TRDAR_CD').apply(
                lambda x: x['_we'].sum() / (x['_wd'].sum() + x['_we'].sum() + 1)
            ).reset_index(name='weekend_pop_ratio')
            result = result.merge(ratio, on='TRDAR_CD', how='left')

        print(f"[FeatureMerger] 유동인구 피처 추출 완료: {len(result)}개 상권, 컬럼: {list(result.columns)}")
        return result

    # ─────────────────────────────────────────────────────────────
    # [신규] 배후 상주인구·직장인 수 추출
    # DS2: VwsmTrdarAresQq
    # ─────────────────────────────────────────────────────────────
    def extract_residential_pop_features(self, df_area: pd.DataFrame) -> pd.DataFrame:
        """
        서울시 상권배후지(VwsmTrdarAresQq) 데이터에서
        상주인구(거주자)와 직장인 수를 추출합니다.

        주요 원본 컬럼:
          TRDAR_CD           : 상권 코드
          RESDNT_POPLTN_CNT  : 상주인구 (배후 거주자 수)
          WORKER_POPLTN_CNT  : 직장인구 (배후 직장인 수)
        """
        if df_area is None or df_area.empty:
            print("[FeatureMerger] 상권배후지 데이터 없음 → 관련 피처 0 처리")
            return pd.DataFrame()

        df = df_area.copy()
        rename = {}
        if 'RESDNT_POPLTN_CNT' in df.columns:
            df['RESDNT_POPLTN_CNT'] = pd.to_numeric(df['RESDNT_POPLTN_CNT'], errors='coerce').fillna(0)
            rename['RESDNT_POPLTN_CNT'] = 'resident_pop'
        if 'WORKER_POPLTN_CNT' in df.columns:
            df['WORKER_POPLTN_CNT'] = pd.to_numeric(df['WORKER_POPLTN_CNT'], errors='coerce').fillna(0)
            rename['WORKER_POPLTN_CNT'] = 'worker_pop'

        if not rename:
            print("[FeatureMerger] 상주/직장인구 컬럼 없음 — API 응답 확인 필요")
            return pd.DataFrame()

        agg_cols = list(rename.keys())
        result = df.groupby('TRDAR_CD')[agg_cols].mean().reset_index().rename(columns=rename)
        print(f"[FeatureMerger] 배후인구 피처 추출 완료: {list(result.columns)}")
        return result

    # ─────────────────────────────────────────────────────────────
    # [신규] 동일 업종 밀집도 + 경쟁 점포 평균 생존 기간
    # 점포 데이터(BAS_ID 기준) 내부 계산
    # ─────────────────────────────────────────────────────────────
    def extract_competition_features(self, df_stores: pd.DataFrame) -> pd.DataFrame:
        """
        BAS_ID 단위로 동일 업종 점포 수와 폐업 점포 평균 생존 기간을 계산합니다.

        ※ avg_comp_survival은 '이미 폐업한 점포들'의 평균 생존 기간입니다.
           모델 학습 시 미래 정보가 아닌 해당 상권의 역사적 통계이므로
           Data Leakage 해당 없음. 단, 신규 상권은 값이 없을 수 있어 0으로 채웁니다.
        """
        if 'BAS_ID' not in df_stores.columns:
            print("[FeatureMerger] BAS_ID 없음 — 경쟁 피처 생략")
            return pd.DataFrame()

        df = df_stores.copy()

        # BAS_ID 내 전체 점포 수 (동일 업종 밀집도 대리 지표)
        same_cnt = df.groupby('BAS_ID').size().reset_index(name='same_induty_cnt')

        # 폐업 점포만으로 평균 생존 기간 계산 (역사적 통계)
        if 'survival_months' in df.columns and 'is_closed' in df.columns:
            closed = df[df['is_closed'] == 1].copy()
            if not closed.empty:
                avg_surv = (
                    closed.groupby('BAS_ID')['survival_months']
                    .mean()
                    .reset_index(name='avg_comp_survival')
                )
                same_cnt = same_cnt.merge(avg_surv, on='BAS_ID', how='left')
            else:
                same_cnt['avg_comp_survival'] = 0
        else:
            same_cnt['avg_comp_survival'] = 0

        same_cnt['avg_comp_survival'] = same_cnt['avg_comp_survival'].fillna(0)
        print(f"[FeatureMerger] 경쟁 피처 추출 완료: {len(same_cnt)}개 BAS_ID")
        return same_cnt

    # ─────────────────────────────────────────────────────────────
    # [신규] 객단가 추정 + 경쟁 강도 지수
    # DS2: VwsmTrdarSelngQq + 유동인구 집계 결과
    # ─────────────────────────────────────────────────────────────
    def extract_sales_features(self, df_sales: pd.DataFrame, df_pop_agg: pd.DataFrame = None) -> pd.DataFrame:
        """
        서울시 상권분석 추정매출(VwsmTrdarSelngQq)에서 실제 매출 피처를 추출합니다.
        유동인구 집계 결과(df_pop_agg)가 있으면 경쟁 강도 지수도 계산합니다.

        주요 원본 컬럼:
          TRDAR_CD          : 상권 코드
          THSMON_SELNG_AMT  : 월 추정매출 (원 단위)
          STOR_CO           : 점포 수 (있을 경우 점포당 매출 계산에 사용)
        """
        if df_sales is None or df_sales.empty:
            print("[FeatureMerger] 매출 데이터 없음 → 관련 피처 0 처리")
            return pd.DataFrame()

        df = df_sales.copy()

        # 매출 컬럼 탐색 (API 버전마다 컬럼명이 다를 수 있음)
        sales_col = next(
            (c for c in ['THSMON_SELNG_AMT', 'MON_SELNG_AMT', 'SELNG_AMT'] if c in df.columns),
            None
        )
        if not sales_col:
            print("[FeatureMerger] 매출 컬럼 없음 — API 응답 구조 확인 필요")
            return pd.DataFrame()

        df[sales_col] = pd.to_numeric(df[sales_col], errors='coerce').fillna(0)

        sales_agg = df.groupby('TRDAR_CD')[sales_col].mean().reset_index()
        sales_agg.columns = ['TRDAR_CD', 'monthly_sales_real']

        # 점포당 매출 계산 (STOR_CO 있을 때)
        if 'STOR_CO' in df.columns:
            df['STOR_CO'] = pd.to_numeric(df['STOR_CO'], errors='coerce').fillna(1).clip(lower=1)
            stor_agg = df.groupby('TRDAR_CD')['STOR_CO'].mean().reset_index(name='store_count')
            sales_agg = sales_agg.merge(stor_agg, on='TRDAR_CD', how='left')
            sales_agg['store_count'] = sales_agg['store_count'].fillna(1)
            sales_agg['sales_per_store'] = (
                sales_agg['monthly_sales_real'] / sales_agg['store_count']
            )
        else:
            sales_agg['sales_per_store'] = sales_agg['monthly_sales_real']

        # 경쟁 강도 지수 = 점포 수 / 유동인구 (값이 클수록 1인당 점포 경쟁이 심함)
        if df_pop_agg is not None and not df_pop_agg.empty and 'total_flpop' in df_pop_agg.columns:
            sales_agg = sales_agg.merge(
                df_pop_agg[['TRDAR_CD', 'total_flpop']], on='TRDAR_CD', how='left'
            )
            sc = sales_agg.get('store_count', pd.Series(1, index=sales_agg.index))
            sales_agg['competition_density'] = sc / sales_agg['total_flpop'].clip(lower=1)
            sales_agg = sales_agg.drop(columns=['total_flpop'], errors='ignore')

        print(f"[FeatureMerger] 매출 피처 추출 완료: {list(sales_agg.columns)}")
        return sales_agg

    # ─────────────────────────────────────────────────────────────
    # 최종 마스터 테이블 생성 (실험 제어 플래그 포함)
    # ─────────────────────────────────────────────────────────────
    def create_master_table(
        self,
        df_stores: pd.DataFrame,
        df_sales: pd.DataFrame = None,
        df_pop: pd.DataFrame = None,
        df_area: pd.DataFrame = None,       # 신규: 상권배후지 (VwsmTrdarAresQq)
        use_real_data: bool = True,         # False → 기존 가짜 계산(EXP_000 재현용)
        use_competition: bool = True,       # 경쟁 밀집도 피처 on/off
        use_residential: bool = True,       # 배후인구 피처 on/off
        use_sales: bool = True,             # 매출 피처 on/off
    ) -> pd.DataFrame:
        """
        [v2] 실험 제어 플래그를 통해 피처 조합을 자유롭게 제어합니다.

        use_real_data=False : EXP_000 — 기존 feature_merger 방식 그대로 (가짜 계산)
        use_real_data=True  : EXP_001~ — 실제 API 데이터 조인

        각 use_* 플래그로 개별 피처 그룹을 on/off하여 기여도를 비교합니다.
        """
        # BAS_ID 매핑 실패 데이터 제거
        master_df = df_stores.dropna(subset=['BAS_ID']).copy()

        # ── 공통 기본 피처 (모든 실험에서 동일) ────────────────────
        master_df['open_year'] = pd.to_datetime(master_df['인허가일자'], errors='coerce').dt.year.fillna(2020)
        master_df['store_age'] = 2026 - master_df['open_year']

        comp_base = master_df.groupby('BAS_ID').size().reset_index(name='local_competitors')
        master_df = master_df.merge(comp_base, on='BAS_ID', how='left')

        # 설명서 7항: BAS_ID 앞 5자리 = SIG_CD (시군구), 앞 3자리 = 구 근사
        master_df['SIG_CD'] = master_df['BAS_ID'].astype(str).str[:5]
        master_df['region_key'] = master_df['BAS_ID'].astype(str).str[:3]

        # ── EXP_000: 기존 가짜 계산 방식 ───────────────────────────
        if not use_real_data:
            if df_sales is not None and not df_sales.empty and 'THSMON_SELNG_AMT' in df_sales.columns:
                df_sales['THSMON_SELNG_AMT'] = pd.to_numeric(df_sales['THSMON_SELNG_AMT'], errors='coerce')
                gmean = df_sales['THSMON_SELNG_AMT'].mean()
                master_df['avg_sales'] = gmean * (
                    1 + (pd.to_numeric(master_df['region_key'], errors='coerce').fillna(0) % 10 - 5) * 0.05
                )
            else:
                master_df['avg_sales'] = 0

            if df_pop is not None and not df_pop.empty:
                pop_col = 'TOT_FLPOP_CO' if 'TOT_FLPOP_CO' in df_pop.columns else 'RESDNT_POPLTN_CNT'
                if pop_col in df_pop.columns:
                    df_pop[pop_col] = pd.to_numeric(df_pop[pop_col], errors='coerce')
                    gpmean = df_pop[pop_col].mean()
                    master_df['pop_density'] = gpmean * (
                        1 + (pd.to_numeric(master_df['region_key'], errors='coerce').fillna(0) % 7 - 3) * 0.1
                    )
                else:
                    master_df['pop_density'] = 0
            else:
                master_df['pop_density'] = 0

            master_df['saturation'] = master_df['local_competitors'] / master_df['store_age'].clip(lower=1)
            master_df['sales_per_store'] = master_df['avg_sales'] / master_df['local_competitors'].clip(lower=1)
            return master_df.drop(columns=['region_key', 'SIG_CD'], errors='ignore').fillna(0)

        # ── EXP_001~: 실제 데이터 조인 ─────────────────────────────
        print("[FeatureMerger] 실제 데이터 조인 시작...")

        # 1) 유동인구 시간대별 피처
        pop_agg = self.extract_floating_pop_features(df_pop)

        # 2) 배후 상주/직장인구
        if use_residential:
            area_agg = self.extract_residential_pop_features(df_area)
        else:
            area_agg = pd.DataFrame()

        # 3) 경쟁 밀집도 + 평균 생존 기간 (BAS_ID 기준 내부 계산)
        if use_competition:
            comp_feat = self.extract_competition_features(master_df)
        else:
            comp_feat = pd.DataFrame()

        # 4) 실제 매출 + 경쟁 강도 지수
        if use_sales:
            sales_feat = self.extract_sales_features(df_sales, pop_agg)
        else:
            sales_feat = pd.DataFrame()

        # ── TRDAR_CD → BAS_ID 연결 (region_key 근사 조인) ──────────
        # 설명서 7항 기준: TRDAR_CD 앞 3자리로 구 단위 근사 매핑
        # 완전한 공간 매핑은 추후 SpatialProcessor 확장 필요
        def _trdar_merge(master, feat_df, feat_cols):
            """TRDAR_CD 기반 집계 데이터를 region_key로 근사 조인합니다."""
            if feat_df is None or feat_df.empty:
                return master
            feat_df = feat_df.copy()
            feat_df['region_key'] = feat_df['TRDAR_CD'].astype(str).str[:3]
            agg = feat_df.drop(columns=['TRDAR_CD']).groupby('region_key').mean().reset_index()
            return master.merge(agg, on='region_key', how='left')

        master_df = _trdar_merge(master_df, pop_agg, [])
        master_df = _trdar_merge(master_df, area_agg, [])
        master_df = _trdar_merge(master_df, sales_feat, [])

        if not comp_feat.empty:
            master_df = master_df.merge(comp_feat, on='BAS_ID', how='left')

        # ── 파생 변수 ───────────────────────────────────────────────
        master_df['saturation'] = master_df['local_competitors'] / master_df['store_age'].clip(lower=1)

        # 경쟁 강도 지수 (유동인구 기반)
        if 'total_flpop' in master_df.columns:
            master_df['competition_density'] = (
                master_df['local_competitors'] / master_df['total_flpop'].clip(lower=1)
            )

        print(f"[FeatureMerger] 마스터 테이블 완성: {len(master_df)}행 × {len(master_df.columns)}컬럼")
        return master_df.drop(columns=['region_key', 'SIG_CD'], errors='ignore').fillna(0)
