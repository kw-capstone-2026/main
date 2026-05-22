import pandas as pd
import requests
import xml.etree.ElementTree as ET
from tqdm import tqdm

# =========================================================
# 1. 설정
# =========================================================

API_KEY = "4f5a75507a646264383269706b4e72"
BASE_URL = "http://openapi.seoul.go.kr:8088"

INPUT_PATH = "data/parquet_datas/final_merged_commercial_data_v3.parquet"
OUTPUT_PATH = "data/parquet_datas/final_merged_commercial_data_v4.parquet"

# =========================================================
# 2. 기존 parquet 로드
# =========================================================

print("📂 기존 parquet 로드 중...")

df = pd.read_parquet(INPUT_PATH)

df["기준_년분기_코드"] = df["기준_년분기_코드"].astype(str)
df["상권_코드"] = df["상권_코드"].astype(str)

print("✅ 로드 완료")
print(df.shape)

# =========================================================
# 3. 대상 분기 생성
# =========================================================

quarters = []

for year in range(2019, 2025):

    for q in range(1, 5):

        quarter = f"{year}{q}"

        if quarter > "20244":
            break

        quarters.append(quarter)

print("📊 대상 분기 수:", len(quarters))
print(quarters)

# =========================================================
# 4. API 호출 함수
# =========================================================

def fetch_worker_population_data(quarter):

    result = []

    start = 1
    step = 1000

    while True:

        end = start + step - 1

        url = (
            f"{BASE_URL}/{API_KEY}/xml/"
            f"VwsmTrdarWrcPopltnQq/"
            f"{start}/{end}/{quarter}"
        )

        response = requests.get(url)

        if response.status_code != 200:

            print(f"❌ 요청 실패: {quarter}")
            break

        root = ET.fromstring(response.text)

        rows = root.findall(".//row")

        if len(rows) == 0:
            break

        for row in rows:

            item = {

                "기준_년분기_코드":
                    row.findtext("STDR_YYQU_CD"),

                "상권_코드":
                    row.findtext("TRDAR_CD"),

                "총_직장_인구_수":
                    row.findtext("TOT_WRC_POPLTN_CO"),

                "남성_직장_인구_수":
                    row.findtext("ML_WRC_POPLTN_CO"),

                "여성_직장_인구_수":
                    row.findtext("FML_WRC_POPLTN_CO"),
            }

            result.append(item)

        # 마지막 페이지 종료
        if len(rows) < step:
            break

        start += step

    return result

# =========================================================
# 5. 전체 데이터 수집
# =========================================================

all_data = []

print("🌐 직장인구 데이터 수집 시작...")

for q in tqdm(quarters):

    data = fetch_worker_population_data(q)

    all_data.extend(data)

worker_df = pd.DataFrame(all_data)

print("✅ 직장인구 데이터 수집 완료")
print(worker_df.shape)

# =========================================================
# 6. 데이터 비어있는지 확인
# =========================================================

if worker_df.empty:

    print("❌ API 데이터가 비어있습니다.")
    exit()

# =========================================================
# 7. 타입 변환
# =========================================================

print("🔧 타입 변환 중...")

num_cols = [
    "총_직장_인구_수",
    "남성_직장_인구_수",
    "여성_직장_인구_수"
]

for col in num_cols:

    worker_df[col] = pd.to_numeric(
        worker_df[col],
        errors="coerce"
    )

worker_df["기준_년분기_코드"] = (
    worker_df["기준_년분기_코드"]
    .astype(str)
)

worker_df["상권_코드"] = (
    worker_df["상권_코드"]
    .astype(str)
)

print("✅ 타입 변환 완료")

# =========================================================
# 8. 필요한 컬럼만 선택
# =========================================================

worker_df = worker_df[
    [
        "기준_년분기_코드",
        "상권_코드",
        "총_직장_인구_수",
        "남성_직장_인구_수",
        "여성_직장_인구_수"
    ]
]

# =========================================================
# 9. 중복 제거
# =========================================================

worker_df = worker_df.drop_duplicates(
    subset=["기준_년분기_코드", "상권_코드"]
)

print("✅ 중복 제거 완료")
print(worker_df.shape)

# =========================================================
# 10. 기존 컬럼 제거 (이미 존재할 경우 대비)
# =========================================================

drop_cols = [
    "총_직장_인구_수",
    "남성_직장_인구_수",
    "여성_직장_인구_수"
]

existing_cols = [
    col for col in drop_cols
    if col in df.columns
]

if existing_cols:

    print("⚠️ 기존 직장인구 컬럼 제거 중...")

    df = df.drop(columns=existing_cols)

    print("✅ 제거 완료")

# =========================================================
# 11. merge
# =========================================================

print("🔗 기존 데이터와 병합 중...")

df = df.merge(
    worker_df,
    how="left",
    on=["기준_년분기_코드", "상권_코드"]
)

print("✅ 병합 완료")
print(df.shape)

# =========================================================
# 12. 결측 처리
# =========================================================

print("🧹 결측 처리 중...")

for col in num_cols:

    df[col] = df[col].fillna(0)

print("✅ 결측 처리 완료")

# =========================================================
# 13. 저장
# =========================================================

print("💾 parquet 저장 중...")

df.to_parquet(
    OUTPUT_PATH,
    index=False
)

print("🎉 저장 완료!")
print(f"📁 저장 위치: {OUTPUT_PATH}")

# =========================================================
# 14. 최종 확인
# =========================================================

print("\n===== 샘플 확인 =====")

print(
    df[
        [
            "기준_년분기_코드",
            "상권_코드",
            "총_직장_인구_수",
            "남성_직장_인구_수",
            "여성_직장_인구_수"
        ]
    ].head()
)

print("\n===== 결측 확인 =====")

print(
    df[
        [
            "총_직장_인구_수",
            "남성_직장_인구_수",
            "여성_직장_인구_수"
        ]
    ].isna().sum()
)