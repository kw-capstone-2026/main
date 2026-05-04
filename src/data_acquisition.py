import os
import requests
import pandas as pd
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

class PublicDataAPI:
    def __init__(self):
        self.vworld_key = os.environ.get('VWORLD_API_KEY')
        self.public_data_key = os.environ.get('PUBLIC_DATA_API_KEY')
        self.seoul_key = os.environ.get('SEOUL_DATA_KEY')

    def get_seoul_subway_master(self) -> List[Dict[str, Any]]:
        """서울시 지하철 역사 마스터 정보 수집"""
        if not self.seoul_key:
            print("❌ [Error] SEOUL_DATA_KEY가 .env에 없습니다.")
            return []
            
        all_subways = []
        start, end = 1, 1000
        print("[Info] 지하철 역사 마스터 데이터 수집 중...")
        try:
            while True:
                url = f"http://openapi.seoul.go.kr:8088/{self.seoul_key}/json/subwayStationMaster/{start}/{end}/"
                res = requests.get(url, timeout=15).json()
                if 'subwayStationMaster' in res:
                    rows = res['subwayStationMaster']['row']
                    all_subways.extend(rows)
                    total_count = int(res['subwayStationMaster']['list_total_count'])
                    if end >= total_count: break
                    start += 1000
                    end += 1000
                else: break
            print(f"✅ 지하철역 {len(all_subways)}개 정보 수집 완료.")
            return all_subways
        except Exception as e:
            print(f"❌ [Error] 지하철 수집 실패: {e}")
            return []

    def get_store_info_hybrid(self) -> Optional[Dict[str, Any]]:
        refined_items = []
        print("[Info] 상가 데이터 수집 중 (DS3)...")
        try:
            init_url = f"http://openapi.seoul.go.kr:8088/{self.seoul_key}/json/LOCALDATA_072405/1/1/"
            init_res = requests.get(init_url, timeout=10).json()
            total_count = int(init_res['LOCALDATA_072405']['list_total_count'])
            
            for start in range(max(1, total_count-25000), total_count, 1000):
                url = f"http://openapi.seoul.go.kr:8088/{self.seoul_key}/json/LOCALDATA_072405/{start}/{start+999}/"
                res = requests.get(url).json()
                if 'LOCALDATA_072405' in res:
                    for row in res['LOCALDATA_072405']['row']:
                        status = str(row.get('TRDSTATENM') or '')
                        refined_items.append({
                            '상가업소번호': row.get('MGTNO'), '상호명': row.get('BPLCNM'),
                            'lat': row.get('Y'), 'lon': row.get('X'),
                            '인허가일자': row.get('APVPERMYMD'), '폐업일자': row.get('DCBYMD'),
                            'is_closed': 0 if '영업' in status or '정상' in status else 1
                        })
            return {'body': {'items': refined_items}}
        except: return None

    def get_seoul_commercial_sales(self, year_quarter: str):
        url = f"http://openapi.seoul.go.kr:8088/{self.seoul_key}/json/VwsmTrdarSelngQq/1/1000/{year_quarter}"
        try: return requests.get(url).json()['VwsmTrdarSelngQq']['row']
        except: return None

    def get_seoul_commercial_pop(self, year_quarter: str):
        url = f"http://openapi.seoul.go.kr:8088/{self.seoul_key}/json/VwsmTrdarFlpopQq/1/1000/{year_quarter}"
        try: return requests.get(url).json()['VwsmTrdarFlpopQq']['row']
        except: return None