import os
import pandas as pd
import requests
from typing import Optional, Dict, Any
from urllib.parse import unquote

class PublicDataAPI:
    """
    공공데이터포털(DS1, DS2, DS5) 및 브이월드 API 연동을 담당하는 클래스
    """

    def __init__(self):
        # .env에서 로드된 환경변수 사용
        self.vworld_key = os.environ.get('VWORLD_API_KEY')
        # 새롭게 업데이트된 디코딩 키 사용
        self.public_data_key = os.environ.get('PUBLIC_DATA_API_KEY')
        self.seoul_key = os.environ.get('SEOUL_DATA_KEY')

    def get_coords_from_vworld(self, address: str) -> Optional[Dict[str, float]]:
        """
        주소를 위경도 좌표로 변환 (브이월드 지오코딩 API)
        """
        if not self.vworld_key:
            return None
        
        url = "https://api.vworld.kr/req/address"
        params = {
            "service": "address",
            "request": "getcoord",
            "version": "2.0",
            "crs": "epsg:4326",
            "address": address,
            "refine": "true",
            "simple": "false",
            "format": "json",
            "type": "road",
            "key": self.vworld_key
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data['response']['status'] == 'OK':
                x = float(data['response']['result']['point']['x'])
                y = float(data['response']['result']['point']['y'])
                return {'lat': y, 'lng': x}
            else:
                return None
        except Exception as e:
            print(f"Geocoding Error for {address}: {e}")
            return None

    def get_store_info_hybrid(self) -> Optional[Dict[str, Any]]:
        """
        하이브리드 수집: DS1(영업중) + DS3(폐업) 데이터를 병합하여 완벽한 균형 데이터 생성
        """
        refined_items = []
        
        # 1. 영업 중 데이터 수집 (공공데이터포털 DS1 - 업종: 음식)
        print("📡 Collecting 'Open' stores from Public Data Portal (DS1)...")
        url_ds1 = "http://apis.data.go.kr/B553077/api/open/sdsc2/storeListInUpjong"
        params_ds1 = {
            "serviceKey": unquote(self.public_data_key),
            "pageNo": "1", "numOfRows": "1000", "divId": "indsLclsCd", "key": "I2", "type": "json"
        }
        try:
            res = requests.get(url_ds1, params=params_ds1, timeout=15).json()
            if 'body' in res and 'items' in res['body']:
                for item in res['body']['items']:
                    refined_items.append({
                        '상가업소번호': item.get('bizesId'), '상호명': item.get('bizesNm'),
                        'lat': item.get('lat'), 'lon': item.get('lon'),
                        '인허가일자': '20200101', '폐업일자': None, 'is_closed': 0
                    })
        except: print("⚠️ DS1 collection failed.")

        # 2. 폐업 데이터 수집 (서울시 DS3 - 필터 완화 및 범위 확대)
        print("📡 Searching for 'Closed' stores WITH coordinates (Expanded Range)...")
        seoul_key = os.environ.get('SEOUL_DATA_KEY')
        
        # 2. 폐업 데이터 수집 (서울시 DS3 - 1000건 제한 준수)
        print("📡 Searching for 'Closed' stores WITH coordinates (Range Fix)...")
        seoul_key = os.environ.get('SEOUL_DATA_KEY')
        
        target_closed = 1000
        closed_list = []
        # 서울시 API는 한번에 최대 1000건까지만 가능함 (ERROR-336 해결)
        search_ranges = [(5001, 6000), (15001, 16000), (25001, 26000), (35001, 36000), (45001, 46000)]
        
        for start, end in search_ranges:
            if len(closed_list) >= target_closed: break
            url_ds3 = f"http://openapi.seoul.go.kr:8088/{seoul_key}/json/LOCALDATA_072405/{start}/{end}/"
            try:
                res = requests.get(url_ds3, timeout=15).json()
                if 'LOCALDATA_072405' in res and 'row' in res['LOCALDATA_072405']:
                    rows = res['LOCALDATA_072405']['row']
                    for row in rows:
                        # 영업상태가 '폐업'이고 좌표가 있으면 수집
                        status = str(row.get('TRDSTATENM') or row.get('DTLSTATENM') or '')
                        x_coord = str(row.get('X', '')).strip()
                        y_coord = str(row.get('Y', '')).strip()
                        
                        if ('폐업' in status) and x_coord and y_coord:
                            closed_list.append({
                                '상가업소번호': row.get('MGTNO'), '상호명': row.get('BPLCNM'),
                                'lat': row.get('Y'), 'lon': row.get('X'),
                                '인허가일자': row.get('APVPERMYMD'), '폐업일자': row.get('DCBYMD') or '20200101', 
                                'is_closed': 1
                            })
                            if len(closed_list) >= target_closed: break
                print(f"   - Range {start}~{end}: Found {len(closed_list)} closed stores...")
            except Exception as e:
                print(f"❌ DS3 Error at {start}~{end}: {e}")
            
        refined_items.extend(closed_list)

        open_cnt = sum(1 for x in refined_items if x['is_closed'] == 0)
        closed_cnt = sum(1 for x in refined_items if x['is_closed'] == 1)
        print(f"✅ Hybrid Collection Success: Open({open_cnt}), Closed({closed_cnt})")
        
        return {'body': {'items': refined_items}}

    def get_seoul_commercial_sales(self, year_quarter: str) -> Optional[Dict[str, Any]]:
        """
        DS2: 서울시 상권분석서비스(상권-추정매출) 조회
        """
        if not self.seoul_key:
            return None
            
        url = f"http://openapi.seoul.go.kr:8088/{self.seoul_key}/json/V_V_TRDAR_SELNG_STTUS/1/100/{year_quarter}"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Seoul Sales API Error: {e}")
            return None

    def get_seoul_living_pop_grid(self, date: str) -> Optional[Dict[str, Any]]:
        """
        DS5: 서울시 격자 단위 생활인구 조회
        """
        if not self.seoul_key:
            return None
            
        url = f"http://openapi.seoul.go.kr:8088/{self.seoul_key}/json/SPOP_LOCAL_RESD_JACHI/1/100/{date}"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Seoul Living Pop API Error: {e}")
            return None
