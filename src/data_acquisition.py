import os
import requests
import pandas as pd
from typing import Optional, Dict, Any, List
from urllib.parse import unquote

class DataAcquisition:
    def __init__(self):
        self.seoul_key = os.environ.get('SEOUL_DATA_KEY')
        self.public_data_key = os.environ.get('PUBLIC_DATA_API_KEY')

    def get_store_info_hybrid(self) -> Dict[str, Any]:
        """DS1(소상공인) + DS3(인허가) 하이브리드 수집"""
        refined_items = []
        try:
            init_url = f"http://openapi.seoul.go.kr:8088/{self.seoul_key}/json/LOCALDATA_072405/1/1/"
            init_res = requests.get(init_url, timeout=10).json()
            total_count = int(init_res['LOCALDATA_072405']['list_total_count'])
            
            # 샘플링 수집 (과거 및 최신 데이터)
            range_list = list(range(1, 20001, 1000)) + list(range(max(1, total_count-5000), total_count, 1000))
            for start in range_list:
                end = start + 999
                url = f"http://openapi.seoul.go.kr:8088/{self.seoul_key}/json/LOCALDATA_072405/{start}/{end}/"
                try:
                    res = requests.get(url, timeout=15).json()
                    if 'LOCALDATA_072405' in res and 'row' in res['LOCALDATA_072405']:
                        for row in res['LOCALDATA_072405']['row']:
                            status = str(row.get('TRDSTATENM') or row.get('DTLSTATENM') or '')
                            x, y = str(row.get('X', '')), str(row.get('Y', ''))
                            if x and y:
                                is_closed = 0 if '영업' in status or '정상' in status else 1
                                refined_items.append({
                                    '상가업소번호': row.get('MGTNO'), '상호명': row.get('BPLCNM'),
                                    'lat': row.get('Y'), 'lon': row.get('X'),
                                    '인허가일자': row.get('APVPERMYMD'), '폐업일자': row.get('DCBYMD'),
                                    'is_closed': is_closed, 'BAS_ID': row.get('SITEPOSTNO')
                                })
                except: continue
        except Exception as e: print(f"DS3 Error: {e}")

        # DS1 추가 수집 (상권업종별 점포)
        for page in range(1, 11):
            url_ds1 = "http://apis.data.go.kr/B553077/api/open/sdsc2/storeListInUpjong"
            params_ds1 = {"serviceKey": unquote(self.public_data_key), "pageNo": str(page), "numOfRows": "1000", "divId": "indsLclsCd", "key": "I2", "type": "json"}
            try:
                res = requests.get(url_ds1, params=params_ds1, timeout=15).json()
                if 'body' in res and 'items' in res['body']:
                    for item in res['body']['items']:
                        refined_items.append({
                            '상가업소번호': item.get('bizesId'), '상호명': item.get('bizesNm'),
                            'lat': item.get('lat'), 'lon': item.get('lon'),
                            '인허가일자': '20200101', '폐업일자': None, 'is_closed': 0, 'BAS_ID': str(item.get('lnoAdr', '00000'))[:5]
                        })
            except: break
        return {'body': {'items': refined_items}}

    def get_seoul_commercial_sales(self, year_quarter: str) -> Optional[List[Dict[str, Any]]]:
        url = f"http://openapi.seoul.go.kr:8088/{self.seoul_key}/json/VwsmTrdarSelngQq/1/1000/{year_quarter}"
        try:
            res = requests.get(url).json()
            if 'VwsmTrdarSelngQq' in res:
                return [row for row in res['VwsmTrdarSelngQq']['row'] if row.get('SVC_INDUTY_CD') == 'CS100001']
        except: pass
        return None

    def get_seoul_subway(self) -> pd.DataFrame:
        url = f"http://openapi.seoul.go.kr:8088/{self.seoul_key}/json/subwayStationMaster/1/1000/"
        res = requests.get(url).json()
        return pd.DataFrame(res['subwayStationMaster']['row'])

    def get_seoul_bus_stops(self) -> pd.DataFrame:
        all_bus = []
        for start in range(1, 12001, 1000):
            url = f"http://openapi.seoul.go.kr:8088/{self.seoul_key}/json/busStopLocationXyInfo/{start}/{start+999}/"
            res = requests.get(url).json()
            if 'busStopLocationXyInfo' in res: all_bus.extend(res['busStopLocationXyInfo']['row'])
            else: break
        return pd.DataFrame(all_bus)

    def get_seoul_large_stores(self) -> pd.DataFrame:
        url = f"http://openapi.seoul.go.kr:8088/{self.seoul_key}/json/LOCALDATA_082501/1/1000/"
        res = requests.get(url).json()
        return pd.DataFrame(res['LOCALDATA_082501']['row']) if 'LOCALDATA_082501' in res else pd.DataFrame()

    def get_seoul_apartments(self) -> pd.DataFrame:
        """[신규] 서울시 공동주택 아파트 정보 수집"""
        all_apts = []
        for start in range(1, 3001, 1000): # 약 3000개 단지 수집
            url = f"http://openapi.seoul.go.kr:8088/{self.seoul_key}/json/OpenAptInfo/{start}/{start+999}/"
            try:
                res = requests.get(url).json()
                if 'OpenAptInfo' in res:
                    all_apts.extend(res['OpenAptInfo']['row'])
                else: break
            except: break
        return pd.DataFrame(all_apts)