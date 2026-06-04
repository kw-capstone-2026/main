"""STEP 5 — 추가 분석 차트 5종 (14~18).

artifacts/extra_agg.json 을 읽어 charts/14~18_*.png 를 생성합니다.
실행: python step5_extra_plots.py  (step4 먼저 실행 필요)
"""
import json

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

import config as C
from viz_style import (INK, SUB, NEG, POS, TEAL, GOLD, PURPLE, GRID, MUTE,
                       style_ax, titleblock, save)


def load():
    with open(C.ART_DIR / "extra_agg.json", encoding="utf-8") as f:
        return json.load(f)


# ════════════════════════════════════════════════════
# C14  공간 위험도 산점도
# ════════════════════════════════════════════════════
def c14_geo_risk(A):
    pts = A["spatial"]["points"]
    lons = np.array([p["lon"] for p in pts])
    lats = np.array([p["lat"] for p in pts])
    rates = np.array([p["rate"] for p in pts])
    ns = np.array([p["n"] for p in pts])

    fig = plt.figure(figsize=(12, 9))
    ax = fig.add_axes([0.06, 0.09, 0.80, 0.78])

    sizes = 10 + np.sqrt(ns / ns.max()) * 45
    sc = ax.scatter(
        lons, lats, c=rates, s=sizes,
        cmap="RdYlGn_r", vmin=0, vmax=rates.max(),
        alpha=0.75, linewidths=0.3, edgecolors="#00000033", zorder=3,
    )

    cbar = fig.colorbar(sc, ax=ax, pad=0.02, shrink=0.82)
    cbar.set_label("폐업 발생률", fontsize=11, color=SUB, labelpad=8)
    cbar.ax.tick_params(labelsize=9, colors=SUB)

    # 위험 상위 10% 강조 레이블
    thresh = np.percentile(rates, 90)
    high = [p for p in pts if p["rate"] >= thresh]
    ax.scatter(
        [p["lon"] for p in high], [p["lat"] for p in high],
        s=60, facecolors="none", edgecolors=POS, linewidths=1.2,
        zorder=4, label=f"상위 10% 고위험 상권 (≥{thresh:.0%})",
    )

    ax.legend(loc="upper left", fontsize=10, framealpha=0.9)
    ax.set_xlabel("경도", fontsize=11, color=SUB)
    ax.set_ylabel("위도", fontsize=11, color=SUB)
    style_ax(ax)
    ax.grid(axis="both", color=GRID, lw=0.7)

    titleblock(
        fig,
        "폐업 위험의 공간적 분포",
        f"서울시 {len(pts)}개 상권의 폐업 발생률을 좌표계에 매핑  |  점 크기 = 관측 수  |  원형 테두리 = 상위 10% 고위험",
        C.SRC_DATA,
    )
    save(fig, "14_geo_risk", C.CHART_DIR)


# ════════════════════════════════════════════════════
# C15  업종별 Kaplan-Meier 생존 곡선
# ════════════════════════════════════════════════════
def c15_km_industry(A):
    km = A.get("km_industry", {})
    if not km:
        print("  [skip] km_industry 데이터 없음")
        return

    high = {k: v for k, v in km.items() if v["group"] == "high"}
    low = {k: v for k, v in km.items() if v["group"] == "low"}

    fig = plt.figure(figsize=(13, 7.5))
    ax = fig.add_axes([0.08, 0.12, 0.86, 0.68])

    red_shades = [POS, "#C0392B", "#E74C3C", "#CB4335", "#A93226"]
    blue_shades = [NEG, "#1A5276", "#2980B9", "#1F618D", "#5DADE2"]

    for i, (ind, d) in enumerate(sorted(high.items(), key=lambda x: -x[1]["rate"])):
        label = f"{ind[:12]}… ({d['rate']:.0%})" if len(ind) > 12 else f"{ind} ({d['rate']:.0%})"
        ax.step(d["t"], d["s"], where="post",
                color=red_shades[i % len(red_shades)], lw=2.0,
                label=label, alpha=0.9)

    for i, (ind, d) in enumerate(sorted(low.items(), key=lambda x: x[1]["rate"])):
        label = f"{ind[:12]}… ({d['rate']:.0%})" if len(ind) > 12 else f"{ind} ({d['rate']:.0%})"
        ax.step(d["t"], d["s"], where="post",
                color=blue_shades[i % len(blue_shades)], lw=2.0,
                label=label, alpha=0.9, linestyle="--")

    ax.axhline(0.5, color=MUTE, lw=1.0, linestyle=":", zorder=0)
    ax.text(2, 0.51, "S(t) = 0.5  (중앙 생존기간)", fontsize=8.5, color=MUTE)

    ax.set_xlim(left=0)
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("평균 운영 기간 (개월, 6개월 단위)", fontsize=12, color=INK)
    ax.set_ylabel("생존율  S(t)", fontsize=12, color=INK)
    style_ax(ax)

    legend = ax.legend(
        loc="lower left", fontsize=9, framealpha=0.92, ncol=2,
        title="업종 (폐업 발생률)  |  실선=고위험·점선=저위험",
        title_fontsize=9,
    )
    legend.get_title().set_color(SUB)

    titleblock(
        fig,
        "업종별 생존 곡선 — 고위험 vs 저위험 업종의 차이",
        "Kaplan-Meier 추정  |  패널 데이터 기반 이벤트 추출  |  운영 기간(6개월 단위) 기준",
        "참고: Kaplan & Meier (1958) JASA  |  " + C.SRC_DATA,
    )
    save(fig, "15_km_industry", C.CHART_DIR)


# ════════════════════════════════════════════════════
# C16  상권 유형별 Kaplan-Meier 생존 곡선
# ════════════════════════════════════════════════════
def c16_km_segment(A):
    km = A.get("km_segment", {})
    if not km:
        print("  [skip] km_segment 데이터 없음")
        return

    palette = [POS, GOLD, TEAL, NEG, PURPLE, MUTE]
    seg_sorted = sorted(km.items(), key=lambda x: -x[1]["rate"])

    fig = plt.figure(figsize=(13, 7.5))
    ax = fig.add_axes([0.08, 0.12, 0.86, 0.68])

    for i, (seg, d) in enumerate(seg_sorted):
        lbl = f"{seg}  (폐업률 {d['rate']:.0%},  n={d['n']:,})"
        ax.step(d["t"], d["s"], where="post",
                color=palette[i % len(palette)], lw=2.4, label=lbl)

    ax.axhline(0.5, color=MUTE, lw=1.0, linestyle=":", zorder=0)
    ax.text(2, 0.51, "S(t) = 0.5", fontsize=8.5, color=MUTE)

    ax.set_xlim(left=0)
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("평균 운영 기간 (개월, 6개월 단위)", fontsize=12, color=INK)
    ax.set_ylabel("생존율  S(t)", fontsize=12, color=INK)
    style_ax(ax)

    legend = ax.legend(
        loc="lower left", fontsize=10.5, framealpha=0.92,
        title="상권 유형 (폐업 발생률, 그룹 수)",
        title_fontsize=10,
    )
    legend.get_title().set_color(SUB)

    titleblock(
        fig,
        "상권 유형별 생존 곡선",
        "Kaplan-Meier 추정  |  상권 유형에 따라 생존 패턴이 유의하게 다름",
        "참고: Kaplan & Meier (1958) JASA  |  " + C.SRC_DATA,
    )
    save(fig, "16_km_segment", C.CHART_DIR)


# ════════════════════════════════════════════════════
# C17  QoQ·YoY 파생 변수 분포 비교 (violin)
# ════════════════════════════════════════════════════
def c17_ts_violin(A):
    ts = A.get("ts", {})
    dist = ts.get("dist", {})
    if not dist:
        print("  [skip] ts.dist 데이터 없음")
        return

    order = ["매출_QoQ", "유동인구_QoQ", "매출_YoY", "유동인구_YoY"]
    cols = [c for c in order if c in dist]
    if not cols:
        return

    labels_kr = {
        "매출_QoQ": "매출\n전분기 대비(QoQ)",
        "유동인구_QoQ": "유동인구\n전분기 대비(QoQ)",
        "매출_YoY": "매출\n전년 동기 대비(YoY)",
        "유동인구_YoY": "유동인구\n전년 동기 대비(YoY)",
    }

    n = len(cols)
    fig, axes = plt.subplots(1, n, figsize=(4.2 * n, 7.5))
    if n == 1:
        axes = [axes]
    fig.subplots_adjust(left=0.07, right=0.97, bottom=0.14, top=0.82, wspace=0.38)

    for ax, col in zip(axes, cols):
        d_pos = dist[col].get("폐업발생", [])
        d_neg = dist[col].get("폐업없음", [])
        if not d_pos or not d_neg:
            continue

        parts = ax.violinplot(
            [d_pos, d_neg], positions=[1, 2],
            showmedians=True, showextrema=False, widths=0.62,
        )
        for pc, col_c in zip(parts["bodies"], [POS, NEG]):
            pc.set_facecolor(col_c)
            pc.set_alpha(0.65)
        parts["cmedians"].set_color(INK)
        parts["cmedians"].set_linewidth(2.2)

        # 중앙값 수치 표기
        med_pos = float(np.median(d_pos))
        med_neg = float(np.median(d_neg))
        ax.text(1, med_pos, f"{med_pos:+.3f}", ha="center", va="bottom",
                fontsize=9, color=POS, fontweight="bold")
        ax.text(2, med_neg, f"{med_neg:+.3f}", ha="center", va="bottom",
                fontsize=9, color=NEG, fontweight="bold")

        ax.axhline(0, color=MUTE, lw=1.1, linestyle="--", zorder=0)
        ax.set_xticks([1, 2])
        ax.set_xticklabels(["폐업\n발생", "폐업\n없음"], fontsize=11)
        ax.set_title(labels_kr.get(col, col), fontsize=12.5, color=INK, pad=9)
        ax.set_ylabel("변화율", fontsize=10, color=SUB)
        style_ax(ax)

    legend_elems = [
        Patch(facecolor=POS, alpha=0.65, label="폐업 발생"),
        Patch(facecolor=NEG, alpha=0.65, label="폐업 없음"),
    ]
    fig.legend(handles=legend_elems, loc="upper right",
               bbox_to_anchor=(0.975, 0.975), fontsize=11)

    fig.text(0.5, 0.955,
             "변화율 피처의 폐업 선행 신호 — QoQ·YoY 하락이 폐업과 동행한다",
             ha="center", fontsize=17, fontweight="bold", color=INK, va="top")
    fig.text(0.5, 0.912,
             "폐업 발생 분기의 변화율 분포(적색)가 정상 분기(청색)보다 음의 방향으로 치우침",
             ha="center", fontsize=12, color=SUB, va="top")
    fig.text(0.5, 0.022,
             "이상치 제거 (5–95th percentile)  |  각 그룹 최대 5,000 샘플  |  " + C.SRC_DATA,
             ha="center", fontsize=8.5, color=MUTE, va="bottom")

    save(fig, "17_ts_violin", C.CHART_DIR)


# ════════════════════════════════════════════════════
# C18  파생 변수 × 폐업 발생 상관계수
# ════════════════════════════════════════════════════
def c18_ts_corr(A):
    ts = A.get("ts", {})
    corr = ts.get("corr", {})
    raw_corr = ts.get("raw_corr", {})
    if not corr:
        print("  [skip] ts.corr 데이터 없음")
        return

    labels_kr = {
        "매출_QoQ": "매출 QoQ (전분기 대비)",
        "유동인구_QoQ": "유동인구 QoQ (전분기 대비)",
        "매출_YoY": "매출 YoY (전년 동기 대비)",
        "유동인구_YoY": "유동인구 YoY (전년 동기 대비)",
        "매출_원본": "매출 (절대값 원본)",
        "유동인구_원본": "유동인구 (절대값 원본)",
    }

    # 파생 변수 + 원본 변수 합산 (비교용)
    combined = {**corr, **raw_corr}
    items = sorted(combined.items(), key=lambda x: x[1])
    keys = [labels_kr.get(k, k) for k, _ in items]
    vals = [v for _, v in items]
    # 파생 = 진한 색, 원본 = 연한 색
    derived_keys = set(corr.keys())
    colors = []
    for k, v in items:
        if k in derived_keys:
            colors.append(POS if v < 0 else TEAL)
        else:
            colors.append("#E8A899" if v < 0 else "#A8C8E8")

    fig = plt.figure(figsize=(12, 6.5))
    ax = fig.add_axes([0.28, 0.12, 0.66, 0.70])

    bars = ax.barh(keys, vals, color=colors, alpha=0.88, height=0.55,
                   edgecolor="white", linewidth=0.5)

    for bar, val in zip(bars, vals):
        offset = 0.002 if val >= 0 else -0.002
        ha = "left" if val >= 0 else "right"
        ax.text(val + offset, bar.get_y() + bar.get_height() / 2,
                f"{val:+.4f}", va="center", ha=ha, fontsize=10.5, color=INK)

    ax.axvline(0, color=INK, lw=1.2)
    ax.set_xlabel("폐업 발생과의 피어슨 상관계수", fontsize=11, color=SUB)
    style_ax(ax)
    ax.grid(axis="x", color=GRID, lw=0.9)

    # 범례
    legend_elems = [
        Patch(facecolor=POS, alpha=0.88, label="파생 변수 (음의 상관)"),
        Patch(facecolor=TEAL, alpha=0.88, label="파생 변수 (양의 상관)"),
        Patch(facecolor="#E8A899", alpha=0.88, label="원본 변수 (비교)"),
    ]
    ax.legend(handles=legend_elems, loc="lower right", fontsize=9.5, framealpha=0.9)

    fig.text(0.28, 0.06,
             "음의 상관 = 해당 변수 감소 시 폐업 가능성 증가  |  파생 변수가 원본보다 상관 강도 높음",
             fontsize=8.8, color=SUB, style="italic")

    titleblock(
        fig,
        "파생 변수 vs 원본 변수 — 변화율이 더 강한 폐업 신호",
        "QoQ·YoY 변화율 피처의 폐업 발생 상관계수를 절대값 원본 피처와 비교",
        C.SRC_DATA,
    )
    save(fig, "18_ts_corr", C.CHART_DIR)


# ════════════════════════════════════════════════════
# main
# ════════════════════════════════════════════════════
def main():
    A = load()

    print("차트 14: 공간 위험도 산점도...")
    c14_geo_risk(A)

    print("차트 15: 업종별 KM 생존 곡선...")
    c15_km_industry(A)

    print("차트 16: 상권 유형별 KM 생존 곡선...")
    c16_km_segment(A)

    print("차트 17: 시계열 변화율 violin...")
    c17_ts_violin(A)

    print("차트 18: 파생 변수 상관관계...")
    c18_ts_corr(A)

    print("완료:", C.CHART_DIR)


if __name__ == "__main__":
    main()
