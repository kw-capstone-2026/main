import pandas as pd
import requests
import xml.etree.ElementTree as ET
from tqdm import tqdm

# =========================================================
# 1. 설정
# =========================================================

API_KEY = "4f5a75507a646264383269706b4e72"
BASE_URL = "http://openapi.seoul.go.kr:8088"

INPUT_PATH = "data/parquet_datas/final_merged_commercial_data_v2.parquet"
OUTPUT_PATH = "data/parquet_datas/final_merged_commercial_data_v3.parquet"

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

def fetch_apartment_data(quarter):

    result = []

    start = 1
    step = 1000

    while True:

        end = start + step - 1

        url = (
            f"{BASE_URL}/{API_KEY}/xml/"
            f"InfoTrdarAptQq/"
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

                "기준_년분기_코드": row.findtext("STDR_YYQU_CD"),
                "상권_코드": row.findtext("TRDAR_CD"),

                "AE_66_BELOW": row.findtext("AE_66_SQMT_BELO_HSHLD_CO"),
                "AE_66": row.findtext("AE_66_SQMT_HSHLD_CO"),
                "AE_99": row.findtext("AE_99_SQMT_HSHLD_CO"),
                "AE_132": row.findtext("AE_132_SQMT_HSHLD_CO"),
                "AE_165": row.findtext("AE_165_SQMT_HSHLD_CO"),

                "AVRG_MKTC": row.findtext("AVRG_MKTC"),
            }

            result.append(item)

        start += step

    return result

# =========================================================
# 5. 전체 수집
# =========================================================

all_data = []

print("🌐 아파트 데이터 수집 시작...")

for q in tqdm(quarters):

    data = fetch_apartment_data(q)

    all_data.extend(data)

apt_df = pd.DataFrame(all_data)

print("✅ 아파트 데이터 수집 완료")
print(apt_df.shape)

# =========================================================
# 6. 타입 변환
# =========================================================

print("🔧 타입 변환 중...")

num_cols = [
    "AE_66_BELOW",
    "AE_66",
    "AE_99",
    "AE_132",
    "AE_165",
    "AVRG_MKTC"
]

for col in num_cols:
    apt_df[col] = pd.to_numeric(apt_df[col], errors="coerce")

apt_df["기준_년분기_코드"] = apt_df["기준_년분기_코드"].astype(str)
apt_df["상권_코드"] = apt_df["상권_코드"].astype(str)

print("✅ 타입 변환 완료")

# =========================================================
# 7. 파생 변수 생성
# =========================================================

print("🧠 아파트 파생 변수 생성 중...")

apt_df["총_아파트_세대수"] = apt_df[
    ["AE_66_BELOW", "AE_66", "AE_99", "AE_132", "AE_165"]
].fillna(0).sum(axis=1)

apt_df["아파트_평균_시가"] = apt_df["AVRG_MKTC"]

apt_df = apt_df[
    [
        "기준_년분기_코드",
        "상권_코드",
        "총_아파트_세대수",
        "아파트_평균_시가"
    ]
]

print("✅ 파생 변수 생성 완료")

# =========================================================
# 8. 중복 제거
# =========================================================

apt_df = apt_df.drop_duplicates(
    subset=["기준_년분기_코드", "상권_코드"]
)

print("✅ 중복 제거 완료")
print(apt_df.shape)

# =========================================================
# 9. merge
# =========================================================

print("🔗 기존 데이터와 병합 중...")

df = df.merge(
    apt_df,
    how="left",
    on=["기준_년분기_코드", "상권_코드"]
)

print("✅ 병합 완료")
print(df.shape)

# =========================================================
# 10. 결측 처리
# =========================================================

print("🧹 결측 처리 중...")

df["총_아파트_세대수"] = df["총_아파트_세대수"].fillna(0)
df["아파트_평균_시가"] = df["아파트_평균_시가"].fillna(0)

print("✅ 결측 처리 완료")

# =========================================================
# 11. 저장
# =========================================================

print("💾 parquet 저장 중...")

df.to_parquet(OUTPUT_PATH, index=False)

print("🎉 완료!")
print("📁 저장 위치:")
print(OUTPUT_PATH)

# =========================================================
# 12. 확인
# =========================================================

print("\n===== 최종 확인 =====")

print(df[
    [
        "기준_년분기_코드",
        "상권_코드",
        "총_아파트_세대수",
        "아파트_평균_시가"
    ]
].head())

print("\n===== 결측 확인 =====")
print(
    df[
        [
            "총_아파트_세대수",
            "아파트_평균_시가"
        ]
    ].isna().sum()
)