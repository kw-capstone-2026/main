"""STEP 2 — 진단 차트용 기술통계 집계.

타겟 클래스 비율, zero-inflation, 업종 쏠림(로렌츠/지니),
상권구분별 위험, 분기 시계열, 업종별 양성률 등을 artifacts/agg.json 에 저장.

실행:  python step2_aggregate.py
"""
import json

import numpy as np
import pandas as pd

import config as C


def main():
    df = pd.read_parquet(C.DATA_PATH)
    df[C.TARGET] = (df["폐업_점포_수"] > 0).astype(int)
    A = {}

    # 1. 타겟 클래스 (폐업 발생 / 과포화 위험)
    A["tgt_close"] = {"pos": int((df["폐업_점포_수"] > 0).sum()),
                      "neg": int((df["폐업_점포_수"] == 0).sum())}
    A["tgt_over"] = {"pos": int((df["과포화_위험_여부"] == 1).sum()),
                     "neg": int((df["과포화_위험_여부"] == 0).sum())}

    # 2. zero-inflation: 폐업 점포 수 분포 (5는 5건 이상)
    vc = df["폐업_점포_수"].clip(upper=5).value_counts().sort_index()
    A["zero_dist"] = {str(int(k)): int(v) for k, v in vc.items()}

    # 3. 업종 쏠림
    ind = df["서비스_업종_코드_명_x"].value_counts()
    A["ind_top"] = {k: int(v) for k, v in ind.head(15).items()}
    A["ind_bottom"] = {k: int(v) for k, v in ind.tail(5).items()}
    A["ind_ratio"] = float(ind.max() / ind.min())

    # 로렌츠 곡선 / 지니계수 (업종별 행 수 집중도)
    s = np.sort(ind.values)
    cum = np.cumsum(s) / s.sum()
    x = np.arange(1, len(s) + 1) / len(s)
    gini = 1 - 2 * np.trapezoid(cum, x) + (cum[-1] / len(s))
    A["lorenz_x"], A["lorenz_y"], A["gini"] = x.tolist(), cum.tolist(), float(round(gini, 3))

    # 4. 상권구분: 표본 수 + 폐업 발생률
    seg = df.groupby("상권_구분_코드_명_x").agg(n=(C.TARGET, "size"), rate=(C.TARGET, "mean"))
    A["seg"] = {i: {"n": int(r.n), "rate": float(r.rate)} for i, r in seg.iterrows()}

    # 5. 분기 시계열
    g = df.groupby("기준_년분기_코드").agg(
        폐업=("폐업_점포_수", "sum"), 개업=("개업_점포_수", "sum"),
        매출중앙=("당월_매출_금액", "median"), 양성률=(C.TARGET, "mean"))
    A["q"] = g.index.tolist()
    A["q_close"] = g["폐업"].tolist()
    A["q_open"] = g["개업"].tolist()
    A["q_sales"] = (g["매출중앙"] / 1e8).round(3).tolist()  # 억원
    A["q_posrate"] = g["양성률"].round(4).tolist()

    # 6. 업종별 양성률 (상위 20개 업종, 불균형의 이질성)
    top20 = ind.head(20).index
    br = (df[df["서비스_업종_코드_명_x"].isin(top20)]
          .groupby("서비스_업종_코드_명_x")[C.TARGET].mean().sort_values())
    A["ind_posrate"] = {k: float(v) for k, v in br.items()}
    A["overall_posrate"] = float(df[C.TARGET].mean())

    with open(C.ART_DIR / "agg.json", "w") as f:
        json.dump(A, f, ensure_ascii=False)

    print(f"gini {A['gini']} | ind_ratio {A['ind_ratio']:,.0f}:1")
    print("seg rates", {k: round(v["rate"], 3) for k, v in A["seg"].items()})


if __name__ == "__main__":
    main()
