import os
import pandas as pd
import requests
from typing import Optional, Dict, Any, List
from urllib.parse import unquote
from dotenv import load_dotenv

load_dotenv()

class PublicDataAPI:
    def __init__(self):
        self.vworld_key = os.environ.get('VWORLD_API_KEY')
        self.public_data_key = os.environ.get('PUBLIC_DATA_API_KEY')
        self.seoul_key = os.environ.get('SEOUL_DATA_KEY')

    def get_seoul_subway_master(self) -> List[Dict[str, Any]]:
        """[추가] 서울시 지하철 역사 마스터 정보 수집"""
        all_subways = []
        url = f"http://openapi.seoul.go.kr:8088/{self.seoul_key}/json/subwayStationMaster/1/1000/"
        try:
            res = requests.get(url, timeout=10).json()
            if 'subwayStationMaster' in res:
                all_subways = res['subwayStationMaster']['row']
            return all_subways
        except: return []

    def get_seoul_bus_stops(self) -> List[Dict[str, Any]]:
        """[추가] 서울시 버스정류소 위치 정보 수집 (전수)"""
        all_bus_stops = []
        start, end = 1, 1000
        try:
            while True:
                url = f"http://openapi.seoul.go.kr:8088/{self.seoul_key}/json/busStopLocationXyInfo/{start}/{end}/"
                res = requests.get(url, timeout=10).json()
                if 'busStopLocationXyInfo' in res:
                    rows = res['busStopLocationXyInfo']['row']
                    all_bus_stops.extend(rows)
                    total_count = int(res['busStopLocationXyInfo']['list_total_count'])
                    if end >= total_count: break
                    start += 1000
                    end += 1000
                else: break
            return all_bus_stops
        except: return all_bus_stops

    def get_store_info_hybrid(self) -> Optional[Dict[str, Any]]:
        """베이스라인 전수 수집 로직 (DS1 + DS3)"""
        refined_items = []
        print("[Info] DS3 (Seoul Data) 전수 수집 시작...")
        try:
            init_url = f"http://openapi.seoul.go.kr:8088/{self.seoul_key}/json/LOCALDATA_072405/1/1/"
            init_res = requests.get(init_url).json()
            total_count = int(init_res['LOCALDATA_072405']['list_total_count'])
            
            # 폐업/영업 균형 수집 (과거 1만 + 최신 1만)
            ranges = [(1, 10000), (total_count-10000, total_count)]
            for r_start, r_end in ranges:
                for start in range(r_start, r_end, 1000):
                    url = f"http://openapi.seoul.go.kr:8088/{self.seoul_key}/json/LOCALDATA_072405/{start}/{start+999}/"
                    try:
                        res = requests.get(url, timeout=10).json()
                        if 'LOCALDATA_072405' in res:
                            for row in res['LOCALDATA_072405']['row']:
                                status = str(row.get('TRDSTATENM') or '')
                                if row.get('X') and row.get('Y'):
                                    refined_items.append({
                                        '상가업소번호': row.get('MGTNO'), '상호명': row.get('BPLCNM'),
                                        'lat': row.get('Y'), 'lon': row.get('X'),
                                        '인허가일자': row.get('APVPERMYMD'),
                                        'is_closed': 0 if '영업' in status or '정상' in status else 1
                                    })
                    except: continue
            return {'body': {'items': refined_items}}
        except: return None

    # 상권 데이터 API들 (FeatureMerger에서 사용)
    def get_seoul_commercial_sales(self, year_quarter: str):
        url = f"http://openapi.seoul.go.kr:8088/{self.seoul_key}/json/VwsmTrdarSelngQq/1/1000/{year_quarter}"
        try: return requests.get(url).json()['VwsmTrdarSelngQq']['row']
        except: return []

    def get_seoul_commercial_stores(self, year_quarter: str):
        url = f"http://openapi.seoul.go.kr:8088/{self.seoul_key}/json/VwsmTrdarStorQq/1/1000/{year_quarter}"
        try: return requests.get(url).json()['VwsmTrdarStorQq']['row']
        except: return []