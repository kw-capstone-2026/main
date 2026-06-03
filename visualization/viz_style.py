"""차트 공통 스타일 — 한글 폰트, 팔레트, 제목/저장 헬퍼.

13장의 차트가 동일한 디자인 언어를 갖도록 색·폰트·여백을 한 곳에서 관리합니다.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# ── 한글 폰트 등록 ───────────────────────────────────────────
# Noto Sans CJK KR (대부분의 리눅스/도커 이미지에 기본 포함).
# 없으면 NanumGothic / AppleGothic / Malgun Gothic 등으로 교체하세요.
_FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",   # macOS
    "C:/Windows/Fonts/malgun.ttf",                  # Windows
]


def _setup_font():
    for path in _FONT_CANDIDATES:
        try:
            fm.fontManager.addfont(path)
            name = fm.FontProperties(fname=path).get_name()
            plt.rcParams["font.family"] = name
            break
        except (FileNotFoundError, RuntimeError):
            continue
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.dpi"] = 200
    plt.rcParams["savefig.dpi"] = 200
    plt.rcParams["figure.facecolor"] = "white"
    plt.rcParams["axes.facecolor"] = "white"


_setup_font()

# ── 팔레트 ───────────────────────────────────────────────────
INK = "#16213E"     # 본문/제목
SUB = "#5C6378"     # 보조 텍스트
NEG = "#4C72A8"     # 다수/정상 (블루)
POS = "#E26D5C"     # 소수/위험 (코랄)
TEAL = "#2A9D8F"
GOLD = "#E4B363"
PURPLE = "#6C5B7B"
GRID = "#E8E9F0"
MUTE = "#B8BCCB"


def style_ax(ax):
    """축에 공통 스타일(스파인 제거, 연한 그리드)을 적용."""
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    for s in ["left", "bottom"]:
        ax.spines[s].set_color("#C9CCD8")
        ax.spines[s].set_linewidth(0.9)
    ax.tick_params(colors=SUB, labelsize=11)
    ax.grid(axis="y", color=GRID, lw=0.9, zorder=0)
    ax.set_axisbelow(True)


def titleblock(fig, title, subtitle, footnote="", x=0.045):
    """그림 상단 제목/부제, 하단 출처를 일관된 위치에 배치."""
    fig.text(x, 0.965, title, fontsize=19, fontweight="bold", color=INK, va="top")
    fig.text(x, 0.905, subtitle, fontsize=12.5, color=SUB, va="top")
    if footnote:
        fig.text(x, 0.022, footnote, fontsize=8.8, color=MUTE, va="bottom")


def save(fig, name, chart_dir):
    """PNG로 저장."""
    fig.savefig(f"{chart_dir}/{name}.png", bbox_inches="tight",
                facecolor="white", pad_inches=0.35)
    plt.close(fig)
