"""STEP 3 — 발표용 고해상도 차트 13종 생성.

artifacts/agg.json, model_out.json, curves.npz 를 읽어
output/charts/01~13_*.png 를 생성합니다.

실행:  python step3_plots.py   (step1, step2 를 먼저 실행해야 함)
"""
import json

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

import config as C
from viz_style import (INK, SUB, NEG, POS, TEAL, GOLD, PURPLE, GRID, MUTE,
                       style_ax, titleblock, save)


def load():
    A = json.load(open(C.ART_DIR / "agg.json"))
    M = json.load(open(C.ART_DIR / "model_out.json"))
    cur = np.load(C.ART_DIR / "curves.npz")
    return A, M, cur


# ════════════════════════ 1막 · 진단 ════════════════════════
def c01_target(A):
    fig = plt.figure(figsize=(12, 6.5))
    ax1 = fig.add_axes([0.06, 0.12, 0.40, 0.66])
    ax2 = fig.add_axes([0.56, 0.12, 0.40, 0.66])

    def donut(ax, pos, neg, title, poslab):
        tot = pos + neg
        ax.pie([neg, pos], colors=[MUTE, POS], startangle=90, counterclock=False,
               wedgeprops=dict(width=0.42, edgecolor="white", linewidth=2))
        ax.text(0, 0.12, f"{pos / tot * 100:.1f}%", ha="center", fontsize=26,
                fontweight="bold", color=POS)
        ax.text(0, -0.18, poslab, ha="center", fontsize=12, color=SUB)
        ax.text(0, -0.42, f"1 : {neg / pos:.0f}", ha="center", fontsize=11,
                color=INK, fontweight="bold")
        ax.set_title(title, fontsize=13.5, color=INK, pad=14, fontweight="bold")

    donut(ax1, A["tgt_close"]["pos"], A["tgt_close"]["neg"], "타겟 ①  폐업 발생 여부", "폐업 발생 분기")
    donut(ax2, A["tgt_over"]["pos"], A["tgt_over"]["neg"], "타겟 ②  과포화 위험 여부", "과포화 위험")
    titleblock(fig, "문제의 출발점 — 예측 대상 자체가 소수 클래스다",
               "두 후보 타겟 모두 양성(위험)이 소수. 폐업 발생은 1:3.4, 과포화 위험은 1:33의 클래스 불균형",
               C.SRC_DATA)
    fig.text(0.5, 0.045, "※ 일반 분류기는 다수(정상) 클래스에 최적화되어 소수(위험) 클래스를 무시하는 경향 — He & Garcia (2009)",
             ha="center", fontsize=9.5, color=SUB, style="italic")
    save(fig, "01_target_imbalance", C.CHART_DIR)


def c02_zero(A):
    zd = A["zero_dist"]
    ks = ["0", "1", "2", "3", "4", "5"]
    lbl = ["0건", "1건", "2건", "3건", "4건", "5건+"]
    vals = [zd.get(k, 0) for k in ks]
    tot = sum(vals)
    fig = plt.figure(figsize=(12, 6.4))
    ax = fig.add_axes([0.08, 0.16, 0.86, 0.6])
    style_ax(ax)
    b = ax.bar(lbl, vals, color=[POS] + [NEG] * 5, zorder=3, width=0.66, edgecolor="white")
    for r, v in zip(b, vals):
        ax.text(r.get_x() + r.get_width() / 2, v + 4000, f"{v / tot * 100:.1f}%",
                ha="center", fontsize=11, color=INK, fontweight="bold")
    ax.set_ylabel("상권×업종×분기 행 수", fontsize=11, color=SUB)
    ax.set_ylim(0, max(vals) * 1.16)
    ax.annotate("전체의 77%가 폐업 0건\n→ zero-inflated 구조",
                xy=(0, vals[0] * 0.5), xytext=(1.4, vals[0] * 0.72),
                fontsize=12, color=POS, fontweight="bold", ha="left",
                arrowprops=dict(arrowstyle="->", color=POS, lw=1.6))
    titleblock(fig, "불균형 진단 ① — 0에 짓눌린 분포 (Zero-Inflation)",
               "대부분의 상권·업종·분기 조합에서 폐업은 발생하지 않음. 단순 정확도는 무의미해진다", C.SRC_DATA)
    save(fig, "02_zero_inflation", C.CHART_DIR)


def c03_industry_skew(A):
    it = A["ind_top"]
    names = list(it.keys())[::-1]
    vv = list(it.values())[::-1]
    fig = plt.figure(figsize=(12, 7.4))
    ax = fig.add_axes([0.26, 0.12, 0.62, 0.66])
    style_ax(ax)
    ax.grid(axis="x", color=GRID)
    ax.grid(axis="y", visible=False)
    b = ax.barh(names, vv, color=NEG, zorder=3, height=0.72)
    b[-1].set_color(POS)
    for r, v in zip(b, vv):
        ax.text(v + 250, r.get_y() + r.get_height() / 2, f"{v:,}", va="center",
                fontsize=9.5, color=SUB)
    ax.set_xlabel("행 수", fontsize=11, color=SUB)
    bot = A["ind_bottom"]
    btxt = "최소 업종:  " + ",  ".join([f"{k} {v:,}행" for k, v in list(bot.items())])
    titleblock(fig, "불균형 진단 ② — 업종 쏠림 (Category Imbalance)",
               f"한식음식점 등 상위 업종이 데이터를 지배.  최다:최소 = {A['ind_ratio']:,.0f} : 1  (한식음식점 33,800 vs 고시원 18)",
               C.SRC_DATA)
    fig.text(0.26, 0.045, btxt, fontsize=9.5, color=POS)
    save(fig, "03_industry_skew", C.CHART_DIR)


def c04_lorenz(A):
    fig = plt.figure(figsize=(11, 7))
    ax = fig.add_axes([0.1, 0.12, 0.82, 0.66])
    style_ax(ax)
    x, y = A["lorenz_x"], A["lorenz_y"]
    ax.plot([0, 1], [0, 1], "--", color=MUTE, lw=1.6, label="완전 균등 (이상)")
    ax.plot(x, y, color=PURPLE, lw=2.8, label="실제 업종 분포", zorder=3)
    ax.fill_between(x, y, x, color=PURPLE, alpha=0.12)
    ax.text(0.62, 0.30, f"Gini = {A['gini']}", fontsize=20, color=PURPLE, fontweight="bold")
    ax.text(0.62, 0.22, "(0=완전균등, 1=완전집중)", fontsize=10, color=SUB)
    ax.set_xlabel("업종 누적 비율 (적은 업종 → 많은 업종)", fontsize=11, color=SUB)
    ax.set_ylabel("누적 데이터 비율", fontsize=11, color=SUB)
    ax.legend(fontsize=11, frameon=False, loc="upper left")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    titleblock(fig, "불균형 진단 ②-보강 — 업종 집중도 (로렌츠 곡선)",
               "곡선이 대각선에서 멀수록 소수 업종에 데이터가 집중. 업종 균형은 표본 수준에서도 깨져 있다", C.SRC_DATA)
    save(fig, "04_industry_lorenz", C.CHART_DIR)


def c05_segment(A):
    seg = A["seg"]
    order = ["골목상권", "발달상권", "전통시장", "관광특구"]
    ns = [seg[k]["n"] for k in order]
    rt = [seg[k]["rate"] * 100 for k in order]
    fig = plt.figure(figsize=(12, 6.6))
    ax = fig.add_axes([0.08, 0.14, 0.84, 0.62])
    style_ax(ax)
    b = ax.bar(order, ns, color=[NEG, NEG, NEG, POS], width=0.6, zorder=3, edgecolor="white")
    tot = sum(ns)
    for r, v in zip(b, ns):
        ax.text(r.get_x() + r.get_width() / 2, v + 5000, f"{v / tot * 100:.1f}%",
                ha="center", fontsize=11, color=SUB)
    ax.set_ylabel("표본 수 (행)", fontsize=11, color=NEG)
    ax.set_ylim(0, max(ns) * 1.18)
    ax2 = ax.twinx()
    ax2.plot(order, rt, "o-", color=GOLD, lw=2.6, ms=11, zorder=5,
             markeredgecolor="white", markeredgewidth=1.5)
    for i, v in enumerate(rt):
        ax2.text(i, v + 2.2, f"{v:.1f}%", ha="center", fontsize=11, color="#C98A1A", fontweight="bold")
    ax2.set_ylabel("폐업 발생률 (%)", fontsize=11, color="#C98A1A")
    ax2.set_ylim(0, 60)
    ax2.spines["top"].set_visible(False)
    ax2.tick_params(colors="#C98A1A")
    titleblock(fig, "불균형 진단 ③ — 표본이 적은 집단이 오히려 더 위험하다",
               "관광특구는 표본의 1.2%에 불과하지만 폐업 발생률은 49%로 최고. 무작정 균형을 맞추면 핵심 위험 신호를 왜곡한다",
               C.SRC_DATA)
    fig.text(0.08, 0.045, "막대=표본 비중(좌축)   ●선=폐업 발생률(우축)", fontsize=9.5, color=SUB)
    save(fig, "05_segment_risk", C.CHART_DIR)


# ════════════════════════ 2막 · 맥락 ════════════════════════
def c06_timeseries(A):
    q, close, opn, sales = A["q"], A["q_close"], A["q_open"], A["q_sales"]
    xi = np.arange(len(q))
    fig = plt.figure(figsize=(13, 6.8))
    ax = fig.add_axes([0.07, 0.18, 0.86, 0.58])
    style_ax(ax)
    ci = [i for i, c in enumerate(q) if c[:4] in ("2020", "2021")]
    ax.axvspan(min(ci) - 0.5, max(ci) + 0.5, color=POS, alpha=0.07, zorder=0)
    ax.text((min(ci) + max(ci)) / 2, max(close) * 1.02, "코로나19 (2020–2021)",
            ha="center", fontsize=10.5, color=POS)
    ax.plot(xi, opn, "o-", color=TEAL, lw=2.3, ms=5, label="개업 점포 수")
    ax.plot(xi, close, "o-", color=POS, lw=2.3, ms=5, label="폐업 점포 수")
    ax.set_xticks(xi[::2])
    ax.set_xticklabels([f"{c[:4]}\nQ{c[4]}" for c in q[::2]], fontsize=9)
    ax.set_ylabel("분기 합계 (점포 수)", fontsize=11, color=SUB)
    ax.legend(fontsize=11, frameon=False, loc="lower left", ncol=2)
    ax2 = ax.twinx()
    ax2.plot(xi, sales, color=GOLD, lw=2, ls="--", alpha=0.9, label="매출 중앙값(억)")
    ax2.set_ylabel("당월 매출 중앙값 (억원)", fontsize=10.5, color="#C98A1A")
    ax2.tick_params(colors="#C98A1A")
    ax2.spines["top"].set_visible(False)
    titleblock(fig, '맥락 — 폐업은 "지연"되었다 (시계열로 본 불균형의 위험)',
               "코로나기 매출 중앙값은 하락했지만 폐업은 폭증하지 않고 2022년 이후로 이연. 시점을 섞어 샘플링하면 이 구조가 사라진다",
               C.SRC_DATA)
    fig.text(0.07, 0.06, "※ 시간 누수 방지를 위해 모델 검증은 마지막 4개 분기(2024)를 테스트셋으로 분리 — 무작위 분할은 미래 정보 누수 위험",
             fontsize=9.3, color=SUB, style="italic")
    save(fig, "06_timeseries_covid", C.CHART_DIR)


def c07_industry_posrate(A):
    pr = A["ind_posrate"]
    names = list(pr.keys())
    vals = [v * 100 for v in pr.values()]
    fig = plt.figure(figsize=(12, 7.6))
    ax = fig.add_axes([0.24, 0.11, 0.66, 0.67])
    style_ax(ax)
    ax.grid(axis="x", color=GRID)
    ax.grid(axis="y", visible=False)
    norm = [(v - min(vals)) / (max(vals) - min(vals)) for v in vals]
    cols = [plt.cm.coolwarm(0.25 + 0.5 * n) for n in norm]
    b = ax.barh(names, vals, color=cols, zorder=3, height=0.72)
    for r, v in zip(b, vals):
        ax.text(v + 0.6, r.get_y() + r.get_height() / 2, f"{v:.0f}%", va="center",
                fontsize=9.5, color=SUB)
    ov = A["overall_posrate"] * 100
    ax.axvline(ov, color=INK, ls="--", lw=1.4)
    ax.text(ov + 0.5, 0.3, f"전체 평균 {ov:.0f}%", fontsize=10, color=INK, rotation=90, va="bottom")
    ax.set_xlabel("폐업 발생률 (%)", fontsize=11, color=SUB)
    titleblock(fig, "불균형 진단 ④ — 불균형의 정도가 업종마다 다르다 (이질성)",
               "상위 20개 업종 기준 폐업 발생률 11%~51%로 편차가 큼. 전역 단일 샘플링/가중치가 부적절한 이유", C.SRC_DATA)
    save(fig, "07_industry_posrate", C.CHART_DIR)


# ════════════════════════ 3막 · 대응 ════════════════════════
def c08_methods(M):
    fig = plt.figure(figsize=(13, 7.4))
    titleblock(fig, "우리의 대응 — 불균형 처리 4가지 접근과 문헌 근거",
               '"왜 이렇게 했는가"에 대한 답: 데이터 차원 / 알고리즘 차원 / 평가 차원으로 나눠 대응했다',
               "근거 문헌은 각 카드 하단 표기")
    cards = [
        ("① 재샘플링 (데이터 차원)", "SMOTE로 소수 클래스 합성 오버샘플링\n+ 다수 클래스 언더샘플링 병행",
         "단순 복제는 결정영역을 축소시키지만,\n합성 표본은 결정영역을 확장해 일반화 개선",
         "Chawla et al. (2002), JAIR 16:321–357", NEG),
        ("② 비용민감 학습 (알고리즘 차원)", "scale_pos_weight로 소수 클래스\n오분류 비용을 가중 (=음성/양성 비율)",
         "재샘플링 없이 손실함수에서 직접 보정.\n트리 앙상블에 적합, 본 프로젝트 채택",
         "He & Garcia (2009), IEEE TKDE 21(9)", TEAL),
        ("③ 임계값 조정 (의사결정 차원)", "기본 0.5 대신 F1/재현율 기준으로\n분류 임계값을 재탐색",
         "확률 순위(AUC)를 바꾸지 않아도\n운영점(Operating point) 최적화 가능",
         "King & Zeng (2001), Political Analysis 9", "#C98A1A"),
        ("④ 평가지표 전환 (검증 차원)", "정확도·ROC 대신 PR-AUC·재현율로\n소수 클래스 성능을 직접 평가",
         "음성이 압도적일 때 정확도/ROC는\n착시를 유발 → PR 곡선이 더 정보적",
         "Saito & Rehmsmeier (2015), PLoS ONE", POS),
    ]
    pos = [(0.05, 0.50), (0.52, 0.50), (0.05, 0.10), (0.52, 0.10)]
    for (x, y), (t, m, r, cit, c) in zip(pos, cards):
        ax = fig.add_axes([x, y, 0.43, 0.34])
        ax.axis("off")
        ax.add_patch(FancyBboxPatch((0.01, 0.02), 0.98, 0.96,
                     boxstyle="round,pad=0.02,rounding_size=0.04", linewidth=0,
                     facecolor=c, alpha=0.07, transform=ax.transAxes))
        ax.add_patch(FancyBboxPatch((0.01, 0.92), 0.98, 0.06, boxstyle="square",
                     linewidth=0, facecolor=c, alpha=0.85, transform=ax.transAxes))
        ax.text(0.04, 0.95, t, fontsize=12.5, fontweight="bold", color="white",
                transform=ax.transAxes, va="center")
        ax.text(0.04, 0.74, m, fontsize=11, color=INK, transform=ax.transAxes, va="top")
        ax.text(0.04, 0.40, r, fontsize=10, color=SUB, transform=ax.transAxes, va="top")
        ax.text(0.04, 0.075, "근거: " + cit, fontsize=9, color=c,
                transform=ax.transAxes, va="center", fontweight="bold")
    save(fig, "08_methods_evidence", C.CHART_DIR)


# ════════════════════════ 4막 · 실증 ════════════════════════
def c09_accuracy_trap(A, M):
    r = M["results"]
    an, acc = r["always_neg_acc"], M["cm_05"]["acc"]
    roc, pr = r["base"]["roc"], r["base"]["pr"]
    labels = ['"전부 정상"\n예측기', "XGBoost\n정확도", "XGBoost\nROC-AUC", "XGBoost\nPR-AUC"]
    vals = [an, acc, roc, pr]
    fig = plt.figure(figsize=(12, 6.6))
    ax = fig.add_axes([0.08, 0.16, 0.84, 0.6])
    style_ax(ax)
    b = ax.bar(labels, vals, color=[MUTE, NEG, NEG, POS], width=0.6, zorder=3, edgecolor="white")
    for rr, v in zip(b, vals):
        ax.text(rr.get_x() + rr.get_width() / 2, v + 0.015, f"{v:.3f}",
                ha="center", fontsize=12, fontweight="bold", color=INK)
    ax.axhline(pr, color=POS, ls=":", lw=1.3)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("점수", fontsize=11, color=SUB)
    ax.annotate("아무도 못 맞혀도\n정확도 0.766", xy=(0, an), xytext=(0.05, 0.92),
                fontsize=11, color="#7A7E8C", ha="left",
                arrowprops=dict(arrowstyle="->", color=MUTE, lw=1.4))
    titleblock(fig, "검증의 함정 — 정확도·ROC는 불균형에서 착시를 만든다",
               "폐업을 한 건도 예측하지 않는 모델도 정확도 0.77. 소수 클래스 성능은 PR-AUC(0.63)가 정직하게 드러낸다",
               C.SRC_MODEL)
    fig.text(0.08, 0.045, "※ PR 곡선의 무작위 기저선 = 양성 비율(≈0.23). PR-AUC 0.63은 그 2.7배 → 실질적 식별력 (Saito & Rehmsmeier, 2015)",
             fontsize=9.3, color=SUB, style="italic")
    save(fig, "09_accuracy_trap", C.CHART_DIR)


def c10_roc_pr(A, M, cur):
    roc, pr = M["results"]["base"]["roc"], M["results"]["base"]["pr"]
    fig = plt.figure(figsize=(13, 6.4))
    ax1 = fig.add_axes([0.07, 0.13, 0.38, 0.62])
    ax2 = fig.add_axes([0.57, 0.13, 0.38, 0.62])
    style_ax(ax1)
    style_ax(ax2)
    ax1.plot(cur["fpr_b"], cur["tpr_b"], color=NEG, lw=2.6, label=f"XGBoost (AUC={roc:.3f})")
    ax1.plot([0, 1], [0, 1], "--", color=MUTE, lw=1.4, label="무작위 (0.5)")
    ax1.set_xlabel("거짓 양성률 (FPR)", fontsize=10.5, color=SUB)
    ax1.set_ylabel("재현율 (TPR)", fontsize=10.5, color=SUB)
    ax1.set_title("ROC 곡선", fontsize=13, color=INK, fontweight="bold")
    ax1.legend(fontsize=10, frameon=False, loc="lower right")
    ax1.set_xlim(0, 1)
    ax1.set_ylim(0, 1)
    ax2.plot(cur["rc_b"], cur["pr_b"], color=POS, lw=2.6, label=f"XGBoost (PR-AUC={pr:.3f})")
    base = A["overall_posrate"]
    ax2.axhline(base, ls="--", color=MUTE, lw=1.4, label=f"무작위 (≈{base:.2f})")
    ax2.set_xlabel("재현율 (Recall)", fontsize=10.5, color=SUB)
    ax2.set_ylabel("정밀도 (Precision)", fontsize=10.5, color=SUB)
    ax2.set_title("Precision–Recall 곡선", fontsize=13, color=INK, fontweight="bold")
    ax2.legend(fontsize=10, frameon=False, loc="upper right")
    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1)
    titleblock(fig, "성능 평가 — 같은 모델, 두 개의 렌즈",
               "ROC는 0.81로 후하게 보이지만, 무작위 기저선이 양성비율(0.23)인 PR 곡선이 소수 클래스 식별력을 더 엄정하게 보여준다")
    fig.text(0.5, 0.035, "※ 보강 관점: ROC는 불균형에 불변, PR은 불균형에 민감하므로 두 지표를 함께 보고한다 (cf. McDermott et al., 2024, PMC11240176)",
             ha="center", fontsize=9, color=MUTE, style="italic")
    save(fig, "10_roc_pr_curves", C.CHART_DIR)


def c11_threshold(M):
    sw, bt = M["sweep"], M["best_t"]
    thr = sw["thr"]
    fig = plt.figure(figsize=(12, 6.6))
    ax = fig.add_axes([0.08, 0.14, 0.84, 0.62])
    style_ax(ax)
    ax.plot(thr, sw["prec"], "o-", color=NEG, lw=2.3, ms=5, label="정밀도 (Precision)")
    ax.plot(thr, sw["rec"], "o-", color=POS, lw=2.3, ms=5, label="재현율 (Recall)")
    ax.plot(thr, sw["f1"], "o-", color=TEAL, lw=2.6, ms=5, label="F1")
    ax.axvline(0.5, color=MUTE, ls="--", lw=1.4)
    ax.text(0.5, 0.02, "기본 0.5", fontsize=9.5, color=SUB, ha="center")
    ax.axvline(bt, color=GOLD, ls="-", lw=1.8)
    ax.text(bt, 0.92, f"F1 최적 {bt:.2f}", fontsize=10.5, color="#C98A1A", ha="center", fontweight="bold")
    ax.set_xlabel("분류 임계값 (threshold)", fontsize=11, color=SUB)
    ax.set_ylabel("점수", fontsize=11, color=SUB)
    ax.legend(fontsize=11, frameon=False, loc="center right")
    ax.set_ylim(0, 1)
    titleblock(fig, "처리 ① — 임계값 한 줄로 위험 포착이 달라진다",
               f"기본 0.5는 정밀도에 치우쳐 폐업을 놓친다. F1 최적 임계값 {bt:.2f}로 낮추면 재현율이 크게 상승", C.SRC_MODEL)
    save(fig, "11_threshold_sweep", C.CHART_DIR)


def c12_confusion(M):
    cm05 = np.array(M["cm_05"]["cm"])
    cmbt = np.array(M["cm_bt"]["cm"])
    fig = plt.figure(figsize=(13, 6.2))

    def cmplot(ax, cm, title, rec):
        mx = cm.max()
        for i in range(2):
            for j in range(2):
                isdiag = (i == j)
                ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1,
                             facecolor=(TEAL if isdiag else POS),
                             alpha=0.10 + 0.5 * cm[i, j] / mx, edgecolor="white", lw=2))
                ax.text(j, i, f"{cm[i, j]:,}", ha="center", va="center",
                        fontsize=15, fontweight="bold", color=INK)
        ax.set_xticks([0, 1])
        ax.set_yticks([0, 1])
        ax.set_xticklabels(["정상 예측", "폐업위험 예측"], fontsize=10.5)
        ax.set_yticklabels(["실제 정상", "실제 폐업"], fontsize=10.5, rotation=90, va="center")
        ax.set_xlim(-0.5, 1.5)
        ax.set_ylim(1.5, -0.5)
        for s in ax.spines.values():
            s.set_visible(False)
        ax.tick_params(length=0)
        ax.set_title(f"{title}\n재현율(폐업 포착률) = {rec:.0%}", fontsize=12.5,
                     color=INK, fontweight="bold", pad=12)

    ax1 = fig.add_axes([0.07, 0.12, 0.36, 0.6])
    ax2 = fig.add_axes([0.57, 0.12, 0.36, 0.6])
    cmplot(ax1, cm05, "처리 전 — 임계값 0.5", M["cm_05"]["rec"])
    cmplot(ax2, cmbt, f"처리 후 — 임계값 {M['best_t']:.2f}", M["cm_bt"]["rec"])
    titleblock(fig, "처리 전 / 후 — 놓치던 폐업 위험을 잡아낸다",
               f"임계값 조정만으로 실제 폐업 포착(재현율) {M['cm_05']['rec']:.0%} → {M['cm_bt']['rec']:.0%}. "
               f"위험 점포를 사전 경보하는 시스템 목적에 부합")
    fig.text(0.5, 0.035, "※ 트레이드오프: 재현율↑ 대신 오경보(거짓 양성)도 증가 → 사업 목적(놓침의 비용 vs 오경보 비용)에 맞춰 임계값 선택",
             ha="center", fontsize=9.3, color=SUB, style="italic")
    save(fig, "12_confusion_before_after", C.CHART_DIR)


def c13_importance(M):
    idx = M["imp_idx"][::-1]
    val = M["imp_val"][::-1]
    fig = plt.figure(figsize=(12, 7.2))
    ax = fig.add_axes([0.30, 0.12, 0.6, 0.66])
    style_ax(ax)
    ax.grid(axis="x", color=GRID)
    ax.grid(axis="y", visible=False)
    ax.barh(idx, val, color=PURPLE, zorder=3, height=0.74)
    ax.set_xlabel("중요도 (gain)", fontsize=11, color=SUB)
    titleblock(fig, "무엇이 폐업 위험을 가르는가 — 변수 기여도 (XGBoost gain)",
               "폐업 파생 변수를 제외하고도 매출·유동인구·경쟁 밀도·운영기간이 핵심 신호로 작동 (SHAP 해석으로 확장 예정)",
               C.SRC_MODEL)
    save(fig, "13_feature_importance", C.CHART_DIR)


def main():
    A, M, cur = load()
    c01_target(A)
    c02_zero(A)
    c03_industry_skew(A)
    c04_lorenz(A)
    c05_segment(A)
    c06_timeseries(A)
    c07_industry_posrate(A)
    c08_methods(M)
    c09_accuracy_trap(A, M)
    c10_roc_pr(A, M, cur)
    c11_threshold(M)
    c12_confusion(M)
    c13_importance(M)
    print(f"차트 13종 생성 완료 → {C.CHART_DIR}")


if __name__ == "__main__":
    main()
