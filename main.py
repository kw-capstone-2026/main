"""
main.py  ← 기존 파일을 이 버전으로 교체
------------------------------------------------------------
[변경 사항]
  - ExperimentLogger 연동: 모든 실험 결과 자동 CSV/MD 저장
  - 실험 제어 플래그(EXP_ID)로 EXP_000~EXP_009 순서대로 실행
  - data_acquisition.py에 get_seoul_commercial_area() 추가 필요
  - 기존 main() 함수 구조 및 파이프라인 순서 100% 유지

[실험 목록]
  EXP_000 : 베이스라인 (기존 가짜 계산, 기준점 AUC ≈ 0.77)
  EXP_001 : 유동인구 시간대별 피처 추가 (VwsmTrdarFlpopQq 실제 조인)
  EXP_002 : 배후 상주인구·직장인 수 추가 (VwsmTrdarAresQq)
  EXP_003 : 동일 업종 밀집도·경쟁 점포 평균 생존 기간 추가
  EXP_004 : 실제 매출 데이터 조인 + 점포당 매출·경쟁 강도 지수 추가
  EXP_005 : 전체 신규 피처 통합 (EXP_001~004 합산)
  EXP_006 : EXP_005 + n_estimators=200 (학습 횟수 증가)
  EXP_007 : EXP_005 + max_depth=3 (과적합 방지)
  EXP_008 : EXP_005 + learning_rate=0.01, n_estimators=500
  EXP_009 : EXP_005 + reg_lambda=15 (L2 규제 강화)

[Data Leakage 방지]
  exclude_cols에 survival_months, 폐업일자, close_date, end_date 포함 유지
"""

import os
import sys
import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv
from sklearn.metrics import roc_auc_score, accuracy_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from src.data_acquisition import PublicDataAPI
from src.spatial_processor import SpatialProcessor
from src.feature_merger import FeatureMerger
from src.models.baseline_xgboost import BaselineXGBoost
from experiment_logger import ExperimentLogger

load_dotenv()

# ─────────────────────────────────────────────────────────────
# 공통 설정
# ─────────────────────────────────────────────────────────────
SHP_PATH = "data/(도로명주소)기초구역_서울/TL_KODIS_BAS_11_202604.shp"
YEAR_QUARTER = "20241"

# 설명서 6항: Data Leakage 방지 제외 컬럼 목록
EXCLUDE_COLS = [
    'BAS_ID', '상가업소번호', '상호명',
    '인허가일자', '폐업일자', 'open_date', 'close_date', 'end_date',
    'lat', 'lon', 'geometry',
    'is_closed',
    'survival_months',   # ← Data Leakage 위험: 절대 피처로 투입 금지
    'open_year',
]

# 기본 하이퍼파라미터 (EXP_000~EXP_005 공통)
BASE_HP = {
    "n_estimators": 100,
    "max_depth": 4,
    "learning_rate": 0.05,
    "reg_lambda": 5,
}


# ─────────────────────────────────────────────────────────────
# 헬퍼: XGBoost 학습 및 평가
# ─────────────────────────────────────────────────────────────
def _train_and_score(master_table: pd.DataFrame, hp: dict) -> tuple:
    """
    master_table에서 피처를 추출하고 XGBoost를 학습하여
    (auc, accuracy, features, train_n, test_n) 튜플을 반환합니다.
    """
    features = [c for c in master_table.columns if c not in EXCLUDE_COLS]

    df_clean = master_table.copy()
    for col in features:
        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)
    df_clean['is_closed'] = pd.to_numeric(df_clean['is_closed'], errors='coerce').fillna(0).astype(int)

    if len(df_clean) < 10:
        print("[Warning] 데이터 부족 — 학습 불가")
        return 0.0, 0.0, features, 0, 0

    X = df_clean[features]
    y = df_clean['is_closed']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 클래스 불균형 자동 보정 (설명서 6항)
    ratio = float(np.sum(y_train == 0)) / max(int(np.sum(y_train == 1)), 1)

    model = XGBClassifier(
        n_estimators=hp.get("n_estimators", 100),
        max_depth=hp.get("max_depth", 4),
        learning_rate=hp.get("learning_rate", 0.05),
        reg_lambda=hp.get("reg_lambda", 5),
        scale_pos_weight=ratio,
        random_state=42,
        use_label_encoder=False,
        eval_metric='auc',
    )

    print(f"  Training XGBoost on {len(X_train)} samples... (피처 {len(features)}개)")
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    probs = model.predict_proba(X_test)[:, 1]

    if len(np.unique(y_test)) < 2:
        print("  [Warning] 테스트셋에 단일 클래스만 존재 — AUC 계산 불가")
        auc = 0.0
    else:
        auc = round(roc_auc_score(y_test, probs), 4)

    acc = round(accuracy_score(y_test, preds), 4)

    print(f"  → AUC: {auc:.4f} | Accuracy: {acc:.4f} | 피처: {len(features)}개")
    print(f"     피처 목록: {features}")

    return auc, acc, features, len(X_train), len(X_test)


# ─────────────────────────────────────────────────────────────
# 상권배후지 데이터 수집 (data_acquisition.py 미구현 시 여기서 직접 호출)
# ─────────────────────────────────────────────────────────────
def _fetch_area_data(seoul_key: str, year_quarter: str) -> list:
    """
    VwsmTrdarAresQq (서울시 상권배후지) 데이터를 수집합니다.
    data_acquisition.py에 get_seoul_commercial_area()가 없을 경우 여기서 직접 호출합니다.
    """
    try:
        url = f"http://openapi.seoul.go.kr:8088/{seoul_key}/json/VwsmTrdarAresQq/1/1000/{year_quarter}"
        res = requests.get(url, timeout=15).json()
        if 'VwsmTrdarAresQq' in res and 'row' in res['VwsmTrdarAresQq']:
            rows = res['VwsmTrdarAresQq']['row']
            print(f"[Data] 상권배후지 Records: {len(rows)}")
            return rows
    except Exception as e:
        print(f"[Warning] 상권배후지 수집 실패: {e}")
    return []


# ─────────────────────────────────────────────────────────────
# 메인 파이프라인
# ─────────────────────────────────────────────────────────────
def main():
    print("[System] 서울시 폐업 예측 파이프라인 (실험 기록 버전) 가동...")

    # ── Step 0: 초기화 ──────────────────────────────────────────
    logger = ExperimentLogger()   # experiments/ 폴더 자동 생성
    api = PublicDataAPI()
    fm = FeatureMerger()

    if not os.path.exists(SHP_PATH):
        print(f"[Error] SHP 파일을 찾을 수 없습니다: {SHP_PATH}")
        return

    print(f"[Info] 기준점 데이터 로드 중: {SHP_PATH}")
    sp = SpatialProcessor(bas_shp_path=SHP_PATH)

    # ── Step 1: 데이터 수집 (DS1~DS5) ──────────────────────────
    print("\n[Step 1] 전수 데이터 수집 시도 (DS1~DS5)...")

    stores_json = api.get_store_info_hybrid()
    if not stores_json or 'body' not in stores_json:
        print("❌ [Error] 상가 데이터 수집 실패.")
        sys.exit(1)

    df_stores_raw = pd.DataFrame(stores_json['body']['items'])
    print(f"[Success] 상가 데이터 {len(df_stores_raw)}건 수집 완료.")

    sales_raw  = api.get_seoul_commercial_sales(YEAR_QUARTER)
    pop_raw    = api.get_seoul_commercial_pop(YEAR_QUARTER)
    living_raw = api.get_seoul_living_pop_grid("20240101")
    area_raw   = _fetch_area_data(api.seoul_key, YEAR_QUARTER)  # 신규: 상권배후지

    print(f"[Data] DS2 Sales   : {len(sales_raw)  if sales_raw  else 0}건")
    print(f"[Data] DS2 Pop     : {len(pop_raw)    if pop_raw    else 0}건")
    print(f"[Data] DS5 Grid    : {len(living_raw) if living_raw else 0}건")
    print(f"[Data] DS2 Area    : {len(area_raw)   if area_raw   else 0}건")

    # ── Step 2: 공간 연산 및 BAS_ID 할당 ───────────────────────
    print("\n[Step 2] 공간 연산 및 기초구역(BAS_ID) 매핑 중...")
    gdf_stores = sp.create_point_geometry(df_stores_raw, lat_col='lat', lng_col='lon')
    gdf_mapped = sp.assign_bas_id(gdf_stores)
    mapped_count = gdf_mapped['BAS_ID'].notna().sum()
    print(f"[Success] 공간 매핑 완료: {mapped_count} / {len(gdf_mapped)} 건")

    # ── Step 3: 생존 기간 및 타겟 생성 ─────────────────────────
    print("\n[Step 3] 생존 기간 및 타겟 변수 생성 중...")
    df_with_survival = fm.calculate_survival_duration(gdf_mapped)

    df_sales = pd.DataFrame(sales_raw) if sales_raw else pd.DataFrame()
    df_pop   = pd.DataFrame(pop_raw)   if pop_raw   else pd.DataFrame()
    df_area  = pd.DataFrame(area_raw)  if area_raw  else pd.DataFrame()

    print(f"\n[Data] Target(Closure) Distribution:")
    print(df_with_survival['is_closed'].value_counts())

    # ═══════════════════════════════════════════════════════════
    # Step 4: 실험 루프
    # ═══════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("  Step 4: 실험 시작")
    print("=" * 60)

    # ──────────────────────────────────────────────────────────
    # EXP_000: 베이스라인 (기존 가짜 계산 — 기준점 재현)
    # ──────────────────────────────────────────────────────────
    print("\n[EXP_000] 베이스라인 (기존 코드 그대로, 가짜 계산값)...")
    master_000 = fm.create_master_table(
        df_stores=df_with_survival,
        df_sales=df_sales,
        df_pop=df_pop,
        use_real_data=False,        # 기존 방식
    )
    auc, acc, feats, tr_n, te_n = _train_and_score(master_000, BASE_HP)
    logger.log(
        exp_id="EXP_000",
        description="베이스라인: 기존 가짜 계산값 (avg_sales/pop_density = region_key % 연산)",
        features_used=feats,
        hyperparams=BASE_HP,
        metrics={"auc": auc, "accuracy": acc},
        data_sources=["DS1(공공데이터포털)", "DS3(서울LOCALDATA)", "DS2-매출(가짜조인)", "DS2-유동인구(가짜조인)"],
        train_samples=tr_n, test_samples=te_n,
        notes=(
            f"설명서 기준 베이스라인 AUC ≈ 0.77. "
            f"실제 측정값: {auc:.4f}. "
            "avg_sales·pop_density가 실제 API 조인이 아닌 산술 계산값이므로 "
            "이 점수는 '가짜 데이터 기준점'으로만 활용."
        ),
    )

    # ──────────────────────────────────────────────────────────
    # EXP_001: 유동인구 시간대별 피처 추가
    # ──────────────────────────────────────────────────────────
    print("\n[EXP_001] 유동인구 시간대별·요일별 피처 추가 (VwsmTrdarFlpopQq)...")
    master_001 = fm.create_master_table(
        df_stores=df_with_survival,
        df_sales=df_sales,
        df_pop=df_pop,
        df_area=None,
        use_real_data=True,
        use_competition=False,
        use_residential=False,
        use_sales=False,
    )
    auc, acc, feats, tr_n, te_n = _train_and_score(master_001, BASE_HP)
    new_cols_001 = [c for c in ['total_flpop','peak_hour_pop','morning_pop','lunch_pop',
                                 'afternoon_pop','evening_pop','night_pop','weekend_pop_ratio']
                    if c in master_001.columns]
    logger.log(
        exp_id="EXP_001",
        description="유동인구 시간대별·요일별 피처 추가 (VwsmTrdarFlpopQq 실제 조인)",
        features_used=feats,
        hyperparams=BASE_HP,
        metrics={"auc": auc, "accuracy": acc},
        data_sources=["DS1", "DS3", "DS2-VwsmTrdarFlpopQq"],
        train_samples=tr_n, test_samples=te_n,
        notes=(
            f"신규 피처: {new_cols_001}. "
            "TRDAR_CD 앞 3자리로 근사 조인(구 단위). "
            f"EXP_000({logger._get_last_auc('EXP_000'):.4f}) 대비 변화 확인."
        ),
    )

    # ──────────────────────────────────────────────────────────
    # EXP_002: 배후 상주인구·직장인 수 추가
    # ──────────────────────────────────────────────────────────
    print("\n[EXP_002] 배후 상주인구·직장인 수 추가 (VwsmTrdarAresQq)...")
    master_002 = fm.create_master_table(
        df_stores=df_with_survival,
        df_sales=df_sales,
        df_pop=df_pop,
        df_area=df_area,
        use_real_data=True,
        use_competition=False,
        use_residential=True,
        use_sales=False,
    )
    auc, acc, feats, tr_n, te_n = _train_and_score(master_002, BASE_HP)
    new_cols_002 = [c for c in ['resident_pop','worker_pop'] if c in master_002.columns]
    logger.log(
        exp_id="EXP_002",
        description="배후 상주인구·직장인 수 추가 (VwsmTrdarAresQq 실제 조인)",
        features_used=feats,
        hyperparams=BASE_HP,
        metrics={"auc": auc, "accuracy": acc},
        data_sources=["DS1", "DS3", "DS2-VwsmTrdarFlpopQq", "DS2-VwsmTrdarAresQq"],
        train_samples=tr_n, test_samples=te_n,
        notes=(
            f"신규 피처: {new_cols_002}. "
            "상주인구·직장인 수는 고정 수요 지표. "
            "유동인구(변동)와 달리 안정적인 배후 수요를 측정."
        ),
    )

    # ──────────────────────────────────────────────────────────
    # EXP_003: 동일 업종 밀집도·경쟁 점포 평균 생존 기간
    # ──────────────────────────────────────────────────────────
    print("\n[EXP_003] 동일 업종 밀집도·경쟁 점포 평균 생존 기간 추가...")
    master_003 = fm.create_master_table(
        df_stores=df_with_survival,
        df_sales=df_sales,
        df_pop=df_pop,
        df_area=df_area,
        use_real_data=True,
        use_competition=True,
        use_residential=True,
        use_sales=False,
    )
    auc, acc, feats, tr_n, te_n = _train_and_score(master_003, BASE_HP)
    new_cols_003 = [c for c in ['same_induty_cnt','avg_comp_survival'] if c in master_003.columns]
    logger.log(
        exp_id="EXP_003",
        description="동일 업종 밀집도(same_induty_cnt)·경쟁 점포 평균 생존 기간 추가",
        features_used=feats,
        hyperparams=BASE_HP,
        metrics={"auc": auc, "accuracy": acc},
        data_sources=["DS1", "DS3", "DS2 전체"],
        train_samples=tr_n, test_samples=te_n,
        notes=(
            f"신규 피처: {new_cols_003}. "
            "avg_comp_survival은 '이미 폐업한 점포'의 역사적 평균 — Data Leakage 아님. "
            "같은 BAS_ID 내 경쟁 환경이 폐업 예측에 미치는 영향 측정."
        ),
    )

    # ──────────────────────────────────────────────────────────
    # EXP_004: 실제 매출 + 점포당 매출·경쟁 강도 지수
    # ──────────────────────────────────────────────────────────
    print("\n[EXP_004] 실제 매출 데이터 조인 + 점포당 매출·경쟁 강도 지수 추가...")
    master_004 = fm.create_master_table(
        df_stores=df_with_survival,
        df_sales=df_sales,
        df_pop=df_pop,
        df_area=df_area,
        use_real_data=True,
        use_competition=True,
        use_residential=True,
        use_sales=True,
    )
    auc, acc, feats, tr_n, te_n = _train_and_score(master_004, BASE_HP)
    new_cols_004 = [c for c in ['monthly_sales_real','sales_per_store','competition_density']
                    if c in master_004.columns]
    logger.log(
        exp_id="EXP_004",
        description="실제 매출(VwsmTrdarSelngQq) + 점포당 매출 + 경쟁 강도 지수 추가",
        features_used=feats,
        hyperparams=BASE_HP,
        metrics={"auc": auc, "accuracy": acc},
        data_sources=["DS1", "DS3", "DS2-VwsmTrdarSelngQq", "DS2-VwsmTrdarFlpopQq"],
        train_samples=tr_n, test_samples=te_n,
        notes=(
            f"신규 피처: {new_cols_004}. "
            "기존 avg_sales(가짜) → monthly_sales_real(실제 API)로 교체. "
            "competition_density = 점포수/유동인구 (값이 클수록 경쟁 심화)."
        ),
    )

    # ──────────────────────────────────────────────────────────
    # EXP_005: 전체 신규 피처 통합
    # ──────────────────────────────────────────────────────────
    print("\n[EXP_005] 전체 신규 피처 통합 (EXP_001~004 합산)...")
    master_005 = master_004   # EXP_004가 이미 모든 피처 포함
    auc, acc, feats, tr_n, te_n = _train_and_score(master_005, BASE_HP)
    logger.log(
        exp_id="EXP_005",
        description="전체 신규 피처 통합 (유동인구+배후인구+경쟁밀집도+실제매출)",
        features_used=feats,
        hyperparams=BASE_HP,
        metrics={"auc": auc, "accuracy": acc},
        data_sources=["DS1", "DS3", "DS2 전체(유동인구·매출·배후지)"],
        train_samples=tr_n, test_samples=te_n,
        notes=(
            "모든 신규 피처를 투입한 풀 버전. "
            "과적합 여부 확인: EXP_000 대비 AUC 상승폭이 너무 크면 데이터 누출 의심."
        ),
    )

    # ──────────────────────────────────────────────────────────
    # EXP_006~EXP_009: 하이퍼파라미터 튜닝 (EXP_005 피처 기준)
    # ──────────────────────────────────────────────────────────
    hp_experiments = [
        (
            "EXP_006",
            "n_estimators=200 (학습 횟수 2배 증가)",
            {**BASE_HP, "n_estimators": 200},
            "학습 횟수를 100→200으로 늘려 underfitting 개선 시도. "
            "설명서 8A: n_estimators 증가로 미세 패턴 학습."
        ),
        (
            "EXP_007",
            "max_depth=3 (트리 깊이 축소, 과적합 방지)",
            {**BASE_HP, "max_depth": 3},
            "설명서 8A: max_depth 4→3으로 축소. "
            "복잡한 패턴 학습 능력을 줄이되 일반화 성능 개선 기대."
        ),
        (
            "EXP_008",
            "learning_rate=0.01, n_estimators=500 (미세 패턴 학습)",
            {**BASE_HP, "learning_rate": 0.01, "n_estimators": 500},
            "설명서 8A: lr 0.05→0.01 + n_estimators 500. "
            "느린 학습률로 미세한 패턴까지 학습. 수렴 보장 위해 트리 수 대폭 증가."
        ),
        (
            "EXP_009",
            "reg_lambda=15 (L2 규제 강화)",
            {**BASE_HP, "reg_lambda": 15},
            "설명서 8A: reg_lambda 5→15로 L2 규제 강화. "
            "가중치 패널티 증가로 특정 피처 과의존 감소 기대."
        ),
    ]

    for exp_id, desc, hp, note in hp_experiments:
        print(f"\n[{exp_id}] {desc}...")
        auc, acc, feats, tr_n, te_n = _train_and_score(master_005, hp)
        logger.log(
            exp_id=exp_id,
            description=desc,
            features_used=feats,
            hyperparams=hp,
            metrics={"auc": auc, "accuracy": acc},
            data_sources=["DS1", "DS3", "DS2 전체"],
            train_samples=tr_n, test_samples=te_n,
            notes=note,
        )

    # ── 최종 비교표 출력 ────────────────────────────────────────
    print("\n\n[완료] 전체 실험 비교표")
    logger.print_summary()
    print(f"  실험 로그   : experiments/experiment_log.csv")
    print(f"  개별 보고서 : experiments/reports/EXP_NNN.md")
    print("[System] 모든 실험이 성공적으로 완료되었습니다!")


# ─────────────────────────────────────────────────────────────
# ExperimentLogger 헬퍼 메서드 추가 (main.py에서 참조용)
# ─────────────────────────────────────────────────────────────
def _patch_logger():
    """logger.log() 내 EXP_000 AUC 참조를 위해 _get_last_auc 메서드를 패치합니다."""
    import csv as _csv
    from experiment_logger import ExperimentLogger

    def _get_last_auc(self, exp_id: str) -> float:
        if not self.log_path.exists():
            return 0.0
        with open(self.log_path, "r", encoding="utf-8-sig") as f:
            for row in _csv.DictReader(f):
                if row.get("exp_id") == exp_id:
                    try:
                        return float(row["auc"])
                    except (ValueError, KeyError):
                        return 0.0
        return 0.0

    ExperimentLogger._get_last_auc = _get_last_auc

_patch_logger()


if __name__ == "__main__":
    main()
