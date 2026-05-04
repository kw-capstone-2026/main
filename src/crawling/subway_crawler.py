"""
crawling/subway_crawler.py
--------------------------
담당: 팀원 A (크롤링 파트)

목적: 전국 지하철 역사 위치(위경도) 및 노선 정보를 수집합니다.
출처: 서울 열린데이터광장 API (subway_station_info) / Kakao Maps API

수집 컬럼:
    - station_name   : 역 이름 (str)
    - line_num       : 노선 번호 (str, 예: '2호선')
    - lon            : 경도 (float)
    - lat            : 위도 (float)
"""

import requests
import pandas as pd


def fetch_subway_stations(api_key: str) -> pd.DataFrame:
    """서울시 지하철 역사 정보를 수집하여 DataFrame으로 반환합니다."""
    # TODO: API 엔드포인트 및 파라미터 구현
    raise NotImplementedError("fetch_subway_stations() 구현 필요")


if __name__ == "__main__":
    API_KEY = "YOUR_API_KEY_HERE"
    df = fetch_subway_stations(API_KEY)
    df.to_csv("../../data/raw/subway_stations.csv", index=False, encoding="utf-8-sig")
    print(f"수집 완료: {len(df)}개 역사")
