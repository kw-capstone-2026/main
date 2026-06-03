"""STEP 4 — 추가 분석용 집계 (공간·생존·시계열 파생 피처).

산출물: artifacts/extra_agg.json
실행:   python step4_extra_agg.py
"""
import json
import warnings

import numpy as np
import pandas as pd

import config as C

warnings.filterwarnings("ignore")


# ── 헬퍼 ─────────────────────────────────────────────────────

def _quarter_order(q_code):
    """'20191' → 0, '20192' → 1, ..., '20244' → 23."""
    s = str(int(q_code))
    return (int(s[:4]) - 2019) * 4 + int(s[4:]) - 1


def _find_area_key(df):
    """상권 고유 식별자 컬럼을 탐색. 없으면 좌표 근사로 생성."""
    for cand in ["상권_코드", "상권_코드_명", "상권_코드_명_x"]:
        if cand in df.columns:
            return df, cand
    df = df.copy()
    df["_area_key"] = (
        df["lat"].round(3).astype(str) + "_" + df["lon"].round(3).astype(str)
    )
    return df, "_area_key"


def _km_curve(durations, events):
    """Kaplan-Meier 생존 함수 수동 구현.

    패널 데이터 기반 그룹별 이벤트 추출 결과를 받아
    step-function 형태의 (times, survival) 반환.
    """
    data = pd.DataFrame({"t": durations, "e": events}).dropna()
    data = data[data["t"] >= 0].sort_values("t")

    event_times = sorted(data.loc[data["e"] == 1, "t"].unique())
    S = 1.0
    times, surv = [0.0], [1.0]

    for t in event_times:
        n_i = int((data["t"] >= t).sum())
        d_i = int(((data["t"] == t) & (data["e"] == 1)).sum())
        if n_i > 0:
            S *= 1.0 - d_i / n_i
        times.append(float(t))
        surv.append(float(round(S, 6)))

    return times, surv


# ── 1. 공간 집계 ──────────────────────────────────────────────

def agg_spatial(df):
    """상권별 폐업 발생률 + lat/lon."""
    df, area_key = _find_area_key(df)

    g = df.groupby(area_key).agg(
        lat=("lat", "mean"),
        lon=("lon", "mean"),
        rate=(C.TARGET, "mean"),
        n=(C.TARGET, "count"),
        seg=("상권_구분_코드_명_x", lambda x: x.value_counts().index[0] if len(x) else ""),
    )

    return {
        "points": [
            {
                "lat": round(float(r.lat), 5),
                "lon": round(float(r.lon), 5),
                "rate": round(float(r.rate), 4),
                "n": int(r.n),
                "seg": str(r.seg),
            }
            for _, r in g.iterrows()
        ]
    }


# ── 2. 생존 분석 집계 ─────────────────────────────────────────

def _build_survival_df(df):
    """패널 → 그룹별 (duration, event) 데이터셋 (벡터화).

    각 (상권, 업종) 조합을 1개 관측으로 변환:
    - 이벤트 그룹: 첫 폐업 분기의 운영_영업_개월_평균
    - 우중도 그룹: 마지막 관측 분기의 운영_영업_개월_평균
    """
    dur_col = "운영_영업_개월_평균"
    df, area_key = _find_area_key(df)
    grp = [area_key, "서비스_업종_코드_명_x"]

    df = df.copy()
    df["_q"] = df["기준_년분기_코드"].apply(_quarter_order)
    df_s = df.sort_values(grp + ["_q"])

    event_flag = df_s.groupby(grp)[C.TARGET].max().rename("event")
    ev_dur = (
        df_s[df_s[C.TARGET] == 1]
        .groupby(grp)[dur_col].first()
        .rename("ev_dur")
    )
    last_dur = df_s.groupby(grp)[dur_col].last().rename("last_dur")
    seg_col = df_s.groupby(grp)["상권_구분_코드_명_x"].last().rename("seg")

    surv = pd.concat([event_flag, ev_dur, last_dur, seg_col], axis=1)
    surv["duration"] = surv["ev_dur"].where(surv["event"] == 1, surv["last_dur"])
    # 6개월 단위 버닝 (KM 곡선 노이즈 감소, 최대 120개월)
    surv["dur_bin"] = (surv["duration"] // 6 * 6).clip(0, 120)

    return surv.dropna(subset=["dur_bin", "event"]).reset_index()


def agg_survival(df):
    """업종별·상권유형별 Kaplan-Meier 생존 곡선 집계."""
    if "운영_영업_개월_평균" not in df.columns:
        return {}

    surv = _build_survival_df(df)
    result = {}

    # 업종별 KM: 폐업 발생률 상위 5 + 하위 5 (최소 100 그룹 이상)
    ind_rates = surv.groupby("서비스_업종_코드_명_x")["event"].agg(["mean", "count"])
    ind_rates = ind_rates[ind_rates["count"] >= 100]
    top5 = ind_rates.nlargest(5, "mean").index.tolist()
    bot5 = ind_rates.nsmallest(5, "mean").index.tolist()
    selected = list(dict.fromkeys(top5 + bot5))

    km_ind = {}
    for ind in selected:
        sub = surv[surv["서비스_업종_코드_명_x"] == ind]
        t, s = _km_curve(sub["dur_bin"], sub["event"])
        km_ind[ind] = {
            "t": t, "s": s,
            "rate": round(float(ind_rates.loc[ind, "mean"]), 4),
            "n": int(ind_rates.loc[ind, "count"]),
            "group": "high" if ind in top5 else "low",
        }
    result["km_industry"] = km_ind

    # 상권 유형별 KM
    km_seg = {}
    for seg_name, sub in surv.groupby("seg"):
        t, s = _km_curve(sub["dur_bin"], sub["event"])
        km_seg[str(seg_name)] = {
            "t": t, "s": s,
            "rate": round(float(sub["event"].mean()), 4),
            "n": int(len(sub)),
        }
    result["km_segment"] = km_seg

    return result


# ── 3. 시계열 파생 피처 집계 ──────────────────────────────────

def agg_ts_features(df):
    """QoQ·YoY 파생 변수 생성 후 폐업 그룹별 분포 및 상관관계 집계."""
    df, area_key = _find_area_key(df)
    grp = [area_key, "서비스_업종_코드_명_x"]
    df = df.copy()
    df["_q"] = df["기준_년분기_코드"].apply(_quarter_order)
    df = df.sort_values(grp + ["_q"])

    feat_map = {
        "매출_QoQ": ("당월_매출_금액", 1),
        "유동인구_QoQ": ("총_유동인구_수", 1),
        "매출_YoY": ("당월_매출_금액", 4),
        "유동인구_YoY": ("총_유동인구_수", 4),
    }

    derived_cols = []
    for new_col, (src_col, lag) in feat_map.items():
        if src_col in df.columns:
            df[new_col] = df.groupby(grp)[src_col].pct_change(lag)
            derived_cols.append(new_col)

    rng = np.random.default_rng(42)
    dist = {}
    for col in derived_cols:
        sub = df[[C.TARGET, col]].replace([np.inf, -np.inf], np.nan).dropna()
        lo, hi = sub[col].quantile(0.05), sub[col].quantile(0.95)
        sub = sub[(sub[col] >= lo) & (sub[col] <= hi)]

        for label, mask in [
            ("폐업발생", sub[C.TARGET] == 1),
            ("폐업없음", sub[C.TARGET] == 0),
        ]:
            vals = sub.loc[mask, col].values
            if len(vals) > 5000:
                idx = rng.choice(len(vals), 5000, replace=False)
                vals = vals[idx]
            dist.setdefault(col, {})[label] = [round(float(v), 5) for v in vals]

    # 파생 변수 × 폐업 발생 피어슨 상관계수
    corr_df = df[derived_cols + [C.TARGET]].replace([np.inf, -np.inf], np.nan)
    corr = corr_df.corr()[C.TARGET][derived_cols].round(4)

    # 원본 피처 상관계수 (비교용)
    raw_map = {"매출_원본": "당월_매출_금액", "유동인구_원본": "총_유동인구_수"}
    raw_corr = {}
    for label, col in raw_map.items():
        if col in df.columns:
            raw_corr[label] = round(float(df[[col, C.TARGET]].corr()[C.TARGET][col]), 4)

    return {
        "dist": dist,
        "corr": corr.dropna().to_dict(),
        "raw_corr": raw_corr,
        "cols": derived_cols,
    }


# ── main ─────────────────────────────────────────────────────

def main():
    df = pd.read_parquet(C.DATA_PATH)
    df[C.TARGET] = (df["폐업_점포_수"] > 0).astype(int)
    out = {}

    print("1/3 공간 집계...")
    out["spatial"] = agg_spatial(df)
    print(f"    → {len(out['spatial']['points'])} 상권 포인트")

    print("2/3 생존 분석...")
    surv = agg_survival(df)
    out.update(surv)
    n_ind = len(surv.get("km_industry", {}))
    n_seg = len(surv.get("km_segment", {}))
    print(f"    → 업종 {n_ind}개 / 상권유형 {n_seg}개 KM 곡선")

    print("3/3 시계열 파생 피처...")
    out["ts"] = agg_ts_features(df)
    print(f"    → 파생 변수 {len(out['ts']['cols'])}개")

    with open(C.ART_DIR / "extra_agg.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    print("저장:", C.ART_DIR / "extra_agg.json")


if __name__ == "__main__":
    main()
