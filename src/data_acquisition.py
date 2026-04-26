import os
import pandas as pd
import requests
from typing import Optional, Dict, Any, List
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
        [전수 수집 모드] DS1 + DS3 전체 데이터를 긁어모아 완벽한 빅데이터셋 구축
        """
        refined_items = []
        seoul_key = os.environ.get('SEOUL_DATA_KEY')
        
        # 1. 서울시 전수 데이터 수집 (DS3 - LOCALDATA_072405)
        print("[Info] Starting FULL-SCALE collection from Seoul Data Plaza (DS3)...")
        try:
            # 먼저 전체 개수 파악
            init_url = f"http://openapi.seoul.go.kr:8088/{seoul_key}/json/LOCALDATA_072405/1/1/"
            init_res = requests.get(init_url, timeout=10).json()
            total_count = int(init_res['LOCALDATA_072405']['list_total_count'])
            print(f"[Data] Total Seoul Store Records Found: {total_count}")
            
            # 1,000건씩 끊어서 전체 수집 (과거 데이터 20,000건 + 최신 데이터 20,000건)
            # 과거 데이터 (주로 폐업)
            for start in range(1, 20000, 1000):
                end = start + 999
                url = f"http://openapi.seoul.go.kr:8088/{seoul_key}/json/LOCALDATA_072405/{start}/{end}/"
                try:
                    res = requests.get(url, timeout=15).json()
                    if 'LOCALDATA_072405' in res and 'row' in res['LOCALDATA_072405']:
                        for row in res['LOCALDATA_072405']['row']:
                            status = str(row.get('TRDSTATENM') or row.get('DTLSTATENM') or '')
                            x_coord, y_coord = str(row.get('X', '')), str(row.get('Y', ''))
                            if x_coord and y_coord:
                                # 상태값 판별 로직 강화
                                is_closed = 1
                                if '영업' in status or '정상' in status:
                                    is_closed = 0
                                elif '폐업' in status:
                                    is_closed = 1
                                    
                                refined_items.append({
                                    '상가업소번호': row.get('MGTNO'), '상호명': row.get('BPLCNM'),
                                    'lat': row.get('Y'), 'lon': row.get('X'),
                                    '인허가일자': row.get('APVPERMYMD'), '폐업일자': row.get('DCBYMD'),
                                    'is_closed': is_closed
                                })
                except: continue

            # 최신 데이터 (주로 영업 중)
            latest_start = max(1, total_count - 20000)
            print(f"[Info] Fetching LATEST records starting from {latest_start}...")
            for start in range(latest_start, latest_start + 5000, 1000): # 우선 5000건만 샘플링
                end = start + 999
                url = f"http://openapi.seoul.go.kr:8088/{seoul_key}/json/LOCALDATA_072405/{start}/{end}/"
                try:
                    res = requests.get(url, timeout=15).json()
                    if 'LOCALDATA_072405' in res and 'row' in res['LOCALDATA_072405']:
                        rows = res['LOCALDATA_072405']['row']
                        if start == latest_start:
                            print(f"[Data] Status Sample from Latest: {[r.get('TRDSTATENM') for r in rows[:5]]}")
                        for row in rows:
                            status = str(row.get('TRDSTATENM') or row.get('DTLSTATENM') or '')
                            x_coord, y_coord = str(row.get('X', '')), str(row.get('Y', ''))
                            if x_coord and y_coord:
                                # 상태값 판별 로직 강화
                                is_closed = 1
                                if '영업' in status or '정상' in status:
                                    is_closed = 0
                                elif '폐업' in status:
                                    is_closed = 1
                                
                                refined_items.append({
                                    '상가업소번호': row.get('MGTNO'), '상호명': row.get('BPLCNM'),
                                    'lat': row.get('Y'), 'lon': row.get('X'),
                                    '인허가일자': row.get('APVPERMYMD'), '폐업일자': row.get('DCBYMD'),
                                    'is_closed': is_closed
                                })
                except: continue
            
            print(f"\n[Success] DS3 Balanced Collection Finished: {len(refined_items)} records.")
        except Exception as e:
            print(f"[Error] DS3 Full Collection Error: {e}")

        # 2. 영업 중 데이터 추가 보강 (DS1 - 공공데이터포털)
        print("[Info] Bolstering with latest data from Public Data Portal (DS1)...")
        for page in range(1, 11): # 10페이지까지 수집 (총 10,000건)
            url_ds1 = "http://apis.data.go.kr/B553077/api/open/sdsc2/storeListInUpjong"
            params_ds1 = {
                "serviceKey": unquote(self.public_data_key),
                "pageNo": str(page), "numOfRows": "1000", "divId": "indsLclsCd", "key": "I2", "type": "json"
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
            except: break
            
        open_cnt = sum(1 for x in refined_items if x['is_closed'] == 0)
        closed_cnt = sum(1 for x in refined_items if x['is_closed'] == 1)
        print(f"[Data] Final Hybrid Dataset: Total({len(refined_items)}), Open({open_cnt}), Closed({closed_cnt})")
        
        return {'body': {'items': refined_items}}

    def get_seoul_commercial_sales(self, year_quarter: str) -> Optional[List[Dict[str, Any]]]:
        """
        DS2: 서울시 상권분석서비스(상권-추정매출) - VwsmTrdarSelngQq
        """
        if not self.seoul_key: return None
        url = f"http://openapi.seoul.go.kr:8088/{self.seoul_key}/json/VwsmTrdarSelngQq/1/1000/{year_quarter}"
        try:
            res = requests.get(url, timeout=15).json()
            if 'VwsmTrdarSelngQq' in res:
                return [row for row in res['VwsmTrdarSelngQq']['row'] if row.get('SVC_INDUTY_CD') == 'CS100001']
        except: pass
        return None

    def get_seoul_commercial_stores(self, year_quarter: str) -> Optional[List[Dict[str, Any]]]:
        """
        DS2: 서울시 상권분석서비스(상권-점포) - VwsmTrdarStorQq
        """
        if not self.seoul_key: return None
        url = f"http://openapi.seoul.go.kr:8088/{self.seoul_key}/json/VwsmTrdarStorQq/1/1000/{year_quarter}"
        try:
            res = requests.get(url, timeout=15).json()
            if 'VwsmTrdarStorQq' in res:
                return [row for row in res['VwsmTrdarStorQq']['row'] if row.get('SVC_INDUTY_CD') == 'CS100001']
        except: pass
        return None

    def get_seoul_commercial_pop(self, year_quarter: str) -> Optional[List[Dict[str, Any]]]:
        """
        DS2: 서울시 상권분석서비스(상권-유동인구) - VwsmTrdarFlpopQq
        """
        if not self.seoul_key: return None
        url = f"http://openapi.seoul.go.kr:8088/{self.seoul_key}/json/VwsmTrdarFlpopQq/1/1000/{year_quarter}"
        try:
            res = requests.get(url, timeout=15).json()
            if 'VwsmTrdarFlpopQq' in res:
                return res['VwsmTrdarFlpopQq']['row']
        except: pass
        return None

    def get_seoul_living_pop_grid(self, date: str) -> Optional[List[Dict[str, Any]]]:
        """
        DS5: 서울시 격자 단위 생활인구 (250m) - SPOP_LOCAL_RESD_JACHI
        """
        if not self.seoul_key: return None
        url = f"http://openapi.seoul.go.kr:8088/{self.seoul_key}/json/SPOP_LOCAL_RESD_JACHI/1/1000/{date}"
        try:
            res = requests.get(url, timeout=15).json()
            if 'SPOP_LOCAL_RESD_JACHI' in res:
                return res['SPOP_LOCAL_RESD_JACHI']['row']
        except: pass
        return None
