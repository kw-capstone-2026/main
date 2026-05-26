# 소득_구간_코드, 상권-업종 적합도 변수 추가
# final_merged_commercial_data.parquet -> final_merged_commercial_data_v2.parquet

import pandas as pd
import requests
import xml.etree.ElementTree as ET
from tqdm import tqdm

# =========================================================
# 1. 설정
# =========================================================

API_KEY = "4f5a75507a646264383269706b4e72"

BASE_URL = "http://openapi.seoul.go.kr:8088"

INPUT_PATH = (
    "data/parquet_datas/"
    "final_merged_commercial_data.parquet"
)

OUTPUT_PATH = (
    "data/parquet_datas/"
    "final_merged_commercial_data_v2.parquet"
)

# =========================================================
# 2. 기존 데이터 로드
# =========================================================

print("📂 기존 데이터 로드 중...")

df = pd.read_parquet(INPUT_PATH)

# 타입 통일
df["기준_년분기_코드"] = (
    df["기준_년분기_코드"]
    .astype(str)
)

df["상권_코드"] = (
    df["상권_코드"]
    .astype(str)
)

print("✅ 기존 데이터 로드 완료")
print(df.shape)

# =========================================================
# 3. 대상 분기 추출
# =========================================================

quarters = sorted(
    df["기준_년분기_코드"].unique()
)

# 소비 데이터 최신 분기 제한
quarters = [
    q for q in quarters
    if int(q) <= 20244
]

print(f"📊 대상 분기 수: {len(quarters)}")
print(quarters)

# =========================================================
# 4. API 데이터 수집 함수
# =========================================================

def fetch_consumption_data(quarter):

    all_rows = []

    start = 1
    end = 1000

    while True:

        url = (
            f"{BASE_URL}/{API_KEY}/xml/"
            f"trdarNcmCnsmp/"
            f"{start}/{end}/{quarter}"
        )

        response = requests.get(url)

        # 요청 실패
        if response.status_code != 200:

            print(f"❌ 요청 실패: {quarter}")
            break

        root = ET.fromstring(response.text)

        rows = root.findall(".//row")

        # 데이터 없으면 종료
        if len(rows) == 0:
            break

        for row in rows:

            item = {

                # 조인 키
                "기준_년분기_코드":
                    row.findtext("STDR_YYQU_CD"),

                "상권_구분_코드":
                    row.findtext("TRDAR_SE_CD"),

                "상권_코드":
                    row.findtext("TRDAR_CD"),

                # 신규 변수
                "소득_구간_코드":
                    row.findtext("INCOME_SCTN_CD"),

                # 소비 데이터
                "지출_총금액":
                    row.findtext("EXPNDTR_TOTAMT"),

                "식료품_지출_총금액":
                    row.findtext(
                        "FDSTFFS_EXPNDTR_TOTAMT"
                    ),

                "의류_신발_지출_총금액":
                    row.findtext(
                        "CLTHS_FTWR_EXPNDTR_TOTAMT"
                    ),

                "생활용품_지출_총금액":
                    row.findtext(
                        "LVSPL_EXPNDTR_TOTAMT"
                    ),

                "의료비_지출_총금액":
                    row.findtext(
                        "MCP_EXPNDTR_TOTAMT"
                    ),

                "교통_지출_총금액":
                    row.findtext(
                        "TRNSPORT_EXPNDTR_TOTAMT"
                    ),

                "여가_지출_총금액":
                    row.findtext(
                        "LSR_EXPNDTR_TOTAMT"
                    ),

                "문화_지출_총금액":
                    row.findtext(
                        "CLTUR_EXPNDTR_TOTAMT"
                    ),

                "교육_지출_총금액":
                    row.findtext(
                        "EDC_EXPNDTR_TOTAMT"
                    ),

                "유흥_지출_총금액":
                    row.findtext(
                        "PLESR_EXPNDTR_TOTAMT"
                    ),
            }

            all_rows.append(item)

        start += 1000
        end += 1000

    print(
        f"{quarter} 수집 완료: "
        f"{len(all_rows)} rows"
    )

    return pd.DataFrame(all_rows)

# =========================================================
# 5. 전체 분기 데이터 수집
# =========================================================

print("🌐 소비 데이터 수집 시작...")

consumption_df_list = []

for q in tqdm(quarters):

    temp_df = fetch_consumption_data(q)

    consumption_df_list.append(temp_df)

consumption_df = pd.concat(
    consumption_df_list,
    ignore_index=True
)

print("✅ 소비 데이터 수집 완료")
print(consumption_df.shape)

# =========================================================
# 6. 타입 변환
# =========================================================

print("🔧 타입 변환 중...")

numeric_cols = [

    "소득_구간_코드",

    "지출_총금액",
    "식료품_지출_총금액",
    "의류_신발_지출_총금액",
    "생활용품_지출_총금액",
    "의료비_지출_총금액",
    "교통_지출_총금액",
    "여가_지출_총금액",
    "문화_지출_총금액",
    "교육_지출_총금액",
    "유흥_지출_총금액",
]

for col in numeric_cols:

    consumption_df[col] = pd.to_numeric(
        consumption_df[col],
        errors="coerce"
    )

# 키 타입 통일
consumption_df["기준_년분기_코드"] = (
    consumption_df["기준_년분기_코드"]
    .astype(str)
)

consumption_df["상권_코드"] = (
    consumption_df["상권_코드"]
    .astype(str)
)

print("✅ 타입 변환 완료")

# =========================================================
# 7. 소비 비율 생성
# =========================================================

print("🧠 소비 비율 생성 중...")

# 0 division 방지
consumption_df["지출_총금액"] = (
    consumption_df["지출_총금액"]
    .replace(0, 1)
)

consumption_df["식료품비율"] = (
    consumption_df["식료품_지출_총금액"]
    / consumption_df["지출_총금액"]
)

consumption_df["의류비율"] = (
    consumption_df["의류_신발_지출_총금액"]
    / consumption_df["지출_총금액"]
)

consumption_df["생활용품비율"] = (
    consumption_df["생활용품_지출_총금액"]
    / consumption_df["지출_총금액"]
)

consumption_df["의료비율"] = (
    consumption_df["의료비_지출_총금액"]
    / consumption_df["지출_총금액"]
)

consumption_df["교통비율"] = (
    consumption_df["교통_지출_총금액"]
    / consumption_df["지출_총금액"]
)

consumption_df["여가문화비율"] = (

    (
        consumption_df["여가_지출_총금액"]
        + consumption_df["문화_지출_총금액"]
    )

    / consumption_df["지출_총금액"]
)

consumption_df["교육비율"] = (
    consumption_df["교육_지출_총금액"]
    / consumption_df["지출_총금액"]
)

consumption_df["유흥비율"] = (
    consumption_df["유흥_지출_총금액"]
    / consumption_df["지출_총금액"]
)

print("✅ 소비 비율 생성 완료")

# =========================================================
# 8. 필요한 컬럼 병합
# =========================================================

merge_cols = [

    "기준_년분기_코드",
    "상권_코드",

    "소득_구간_코드",

    "식료품비율",
    "의류비율",
    "생활용품비율",
    "의료비율",
    "교통비율",
    "여가문화비율",
    "교육비율",
    "유흥비율",
]

print("🔗 기존 데이터와 병합 중...")

df = pd.merge(

    df,

    consumption_df[merge_cols],

    how="left",

    on=[
        "기준_년분기_코드",
        "상권_코드"
    ]
)

print("✅ 병합 완료")
print(df.shape)

# =========================================================
# 9. 업종별 적합도 매핑
# =========================================================

print("🧠 상권-업종 적합도 생성 중...")

industry_mapping = {

    # 식료품
    "한식음식점": "식료품비율",
    "중식음식점": "식료품비율",
    "일식음식점": "식료품비율",
    "양식음식점": "식료품비율",
    "제과점": "식료품비율",
    "패스트푸드점": "식료품비율",
    "치킨전문점": "식료품비율",
    "분식전문점": "식료품비율",
    "육류판매": "식료품비율",
    "반찬가게": "식료품비율",
    "미곡판매": "식료품비율",
    "수산물판매": "식료품비율",
    "청과상": "식료품비율",

    # 유흥
    "호프-간이주점": "유흥비율",
    "노래방": "유흥비율",

    # 여가문화
    "커피-음료": "여가문화비율",
    "PC방": "여가문화비율",
    "당구장": "여가문화비율",
    "스포츠클럽": "여가문화비율",
    "골프연습장": "여가문화비율",

    # 교육
    "일반교습학원": "교육비율",
    "외국어학원": "교육비율",
    "예술학원": "교육비율",
    "스포츠 강습": "교육비율",
    "서적": "교육비율",
    "문구": "교육비율",

    # 의류/패션
    "일반의류": "의류비율",
    "신발": "의류비율",
    "가방": "의류비율",
    "화장품": "의류비율",
    "시계및귀금속": "의류비율",
    "안경": "의류비율",

    # 생활용품
    "슈퍼마켓": "생활용품비율",
    "편의점": "생활용품비율",
    "세탁소": "생활용품비율",
    "화초": "생활용품비율",
    "가구": "생활용품비율",
    "조명용품": "생활용품비율",
    "철물점": "생활용품비율",
    "인테리어": "생활용품비율",
    "가전제품": "생활용품비율",

    # 의료
    "일반의원": "의료비율",
    "치과의원": "의료비율",
    "한의원": "의료비율",
    "의약품": "의료비율",
    "의료기기": "의료비율",
}

# 기본값
df["상권_업종_적합도"] = 0.0

# 업종별 매핑
for industry, ratio_col in industry_mapping.items():

    mask = (
        df["서비스_업종_코드_명_x"]
        == industry
    )

    df.loc[
        mask,
        "상권_업종_적합도"
    ] = df.loc[
        mask,
        ratio_col
    ]

print("✅ 적합도 생성 완료")

# =========================================================
# 10. 결측 처리
# =========================================================

print("🧹 결측치 처리 중...")

df["소득_구간_코드"] = (
    df["소득_구간_코드"]
    .fillna(0)
    .astype("int8")
)

df["상권_업종_적합도"] = (
    df["상권_업종_적합도"]
    .astype("float32")
)

# =========================================================
# 11. 상권_업종_적합도 유효 데이터만 유지
# =========================================================

print("🧹 상권_업종_적합도 0 / NaN 제거 중...")

before_shape = df.shape

df = df[

    (df["상권_업종_적합도"].notna()) &

    (df["상권_업종_적합도"] > 0)
]

after_shape = df.shape

print(f"기존 shape: {before_shape}")
print(f"정제 후 shape: {after_shape}")

# =========================================================
# 12. 중간 비율 컬럼 제거
# =========================================================

print("🗑 중간 비율 컬럼 제거 중...")

drop_cols = [

    "식료품비율",
    "의류비율",
    "생활용품비율",
    "의료비율",
    "교통비율",
    "여가문화비율",
    "교육비율",
    "유흥비율",
]

drop_cols = [
    col for col in drop_cols
    if col in df.columns
]

df.drop(
    columns=drop_cols,
    inplace=True
)

print("✅ 중간 컬럼 제거 완료")

# =========================================================
# 13. 저장
# =========================================================

print("💾 parquet 저장 중...")

df.to_parquet(
    OUTPUT_PATH,
    index=False
)

print("🎉 저장 완료")
print(f"📁 저장 위치: {OUTPUT_PATH}")

# =========================================================
# 14. 최종 확인
# =========================================================

print("\n===== 최종 추가 컬럼 확인 =====")

print(
    df[
        [
            "서비스_업종_코드_명_x",
            "소득_구간_코드",
            "상권_업종_적합도"
        ]
    ].head(20)
)

print("\n===== 제거 여부 확인 =====")

for col in drop_cols:

    if col in df.columns:
        print(f"❌ 아직 존재: {col}")
    else:
        print(f"✅ 제거 완료: {col}")

print("\n===== 최종 적합도 확인 =====")

print(
    df["상권_업종_적합도"]
    .describe()
)

print("\n===== 0 개수 =====")

print(
    (df["상권_업종_적합도"] == 0)
    .sum()
)

print("\n===== NaN 개수 =====")

print(
    df["상권_업종_적합도"]
    .isna()
    .sum()
)