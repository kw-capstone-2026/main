"""
scratch/test_geo_features.py
D5 지리적/물리적 제약 피처 API 테스트 스크립트

실행 방법:
    cd /Users/baekjiyun/Documents/capstone/main
    python scratch/test_geo_features.py

테스트 항목:
    1. VWorld 고도 API — 서울 주요 지점 5곳 고도 조회
    2. 서울 횡단보도 API — 데이터셋 탐색 및 샘플 수집
    3. 소규모 점포 샘플에 피처 적용 (data_dump.pkl 있을 경우)
"""

import os
import sys
import pickle
import pandas as pd
import numpy as np
import geopandas as gpd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from dotenv import load_dotenv
load_dotenv()

from src.data_acquisition import PublicDataAPI
from src.spatial_processor import SpatialProcessor
from src.feature_engineering.spatial_features import (
    compute_nearest_distance,
    compute_count_within_radius,
    build_geo_constraint_features,
)

RESULT_LOG = []

def log(tag: str, msg: str, value=None):
    entry = f"[{tag}] {msg}" + (f" → {value}" if value is not None else "")
    print(entry)
    RESULT_LOG.append(entry)


# ──────────────────────────────────────────────────────────
# Test 1: VWorld 고도 API
# ──────────────────────────────────────────────────────────

def test_elevation_api(api: PublicDataAPI):
    print("\n" + "="*55)
    print("Test 1: VWorld 고도(LT_C_LHFPC) API")
    print("="*55)

    # 서울 주요 지점 (위도, 경도, 예상 고도)
    test_points = [
        ("광화문",        37.5759, 126.9769, "약 30~40m"),
        ("남산 중턱",     37.5512, 126.9882, "약 150m+"),
        ("강남 테헤란로", 37.4979, 127.0276, "약 20~30m"),
        ("은평구 진관동", 37.6389, 126.9208, "약 60m+"),
        ("강동구 암사동", 37.5508, 127.1314, "약 15m"),
    ]

    success = 0
    for name, lat, lng, expected in test_points:
        elev = api.get_elevation_srtm(lat=lat, lng=lng)
        status = "OK" if elev is not None else "FAIL (None 반환)"
        log("Elevation", f"{name} ({lat}, {lng})  예상={expected}", f"{elev}m  [{status}]")
        if elev is not None:
            success += 1

    log("Elevation", f"성공률: {success}/{len(test_points)}")
    return success > 0


# ──────────────────────────────────────────────────────────
# Test 2: 횡단보도 API
# ──────────────────────────────────────────────────────────

def test_crosswalk_api(api: PublicDataAPI):
    print("\n" + "="*55)
    print("Test 2: 서울 횡단보도 위치 API")
    print("="*55)

    data = api.get_crosswalk_locations_seoul()

    if data:
        log("Crosswalk", f"수집 건수", len(data))
        log("Crosswalk", f"샘플 (첫 3건)", data[:3])
        # 좌표 범위 확인 (서울: lat 37.4~37.7, lng 126.7~127.2)
        lats = [r['lat'] for r in data]
        lngs = [r['lng'] for r in data]
        log("Crosswalk", f"위도 범위: {min(lats):.4f} ~ {max(lats):.4f}")
        log("Crosswalk", f"경도 범위: {min(lngs):.4f} ~ {max(lngs):.4f}")
        return True
    else:
        log("Crosswalk", "FAIL — 데이터 없음 (횡단보도 API 미수집)")
        return False


# ──────────────────────────────────────────────────────────
# Test 3: 소규모 샘플에 D5 피처 전체 적용
# ──────────────────────────────────────────────────────────

def test_full_pipeline(api: PublicDataAPI):
    print("\n" + "="*55)
    print("Test 3: 소규모 샘플 파이프라인 (20개 점포)")
    print("="*55)

    dump_path = 'scratch/data_dump.pkl'
    if not os.path.exists(dump_path):
        log("Pipeline", "SKIP — data_dump.pkl 없음 (prepare_data.py 먼저 실행 필요)")
        return

    with open(dump_path, 'rb') as f:
        raw = pickle.load(f)

    df_stores = pd.DataFrame(raw['stores']).head(20)  # 20개만 테스트
    log("Pipeline", f"샘플 점포 수", len(df_stores))

    shp_path = "data/(도로명주소)기초구역_서울/TL_KODIS_BAS_11_202604.shp"
    if not os.path.exists(shp_path):
        log("Pipeline", "SKIP — SHP 파일 없음")
        return

    sp        = SpatialProcessor(bas_shp_path=shp_path)
    gdf       = sp.create_point_geometry(df_stores, lat_col='lat', lng_col='lon')
    gdf_mapped = sp.assign_bas_id(gdf)

    log("Pipeline", f"BAS_ID 매핑 성공", gdf_mapped['BAS_ID'].notna().sum())

    result = build_geo_constraint_features(gdf_mapped, api, cache_dir='scratch')

    for col in ['elevation', 'slope', 'dist_crosswalk']:
        valid = result[col].notna().sum()
        mean  = result[col].mean() if valid > 0 else float('nan')
        log("Pipeline", f"{col}: 유효={valid}/{len(result)}, mean={mean:.2f}")

    print("\n[Pipeline] 결과 테이블 (앞 5행):")
    print(result[['BAS_ID', 'is_closed', 'elevation', 'slope', 'dist_crosswalk']].head())


# ──────────────────────────────────────────────────────────
# Test 4: compute_nearest_distance / compute_count_within_radius 단위 테스트
# ──────────────────────────────────────────────────────────

def test_spatial_functions():
    print("\n" + "="*55)
    print("Test 4: 공간 연산 함수 단위 테스트")
    print("="*55)

    # 더미 점포 5개 (서울 시청 근처)
    stores_data = {
        'store_id': range(5),
        'geometry': [
            gpd.points_from_xy([126.977 + i * 0.001], [37.566])[0]
            for i in range(5)
        ]
    }
    stores_gdf = gpd.GeoDataFrame(stores_data, crs='EPSG:4326')

    # 더미 POI 3개 (횡단보도 가정)
    poi_data = {
        'poi_id': range(3),
        'geometry': [
            gpd.points_from_xy([126.977 + i * 0.002], [37.5665])[0]
            for i in range(3)
        ]
    }
    poi_gdf = gpd.GeoDataFrame(poi_data, crs='EPSG:4326')

    # 최근접 거리
    result_dist = compute_nearest_distance(stores_gdf, poi_gdf, 'dist_poi')
    log("SpatialFunc", "compute_nearest_distance 결과 (m)",
        result_dist['dist_poi'].round(1).tolist())

    # 반경 내 개수 (500m)
    result_cnt = compute_count_within_radius(stores_gdf, poi_gdf, 500, 'cnt_poi_500m')
    log("SpatialFunc", "compute_count_within_radius (r=500m)",
        result_cnt['cnt_poi_500m'].tolist())

    log("SpatialFunc", "단위 테스트 완료")


# ──────────────────────────────────────────────────────────
# 결과 요약 저장
# ──────────────────────────────────────────────────────────

def save_report():
    report_path = 'scratch/test_geo_report.txt'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=== D5 지리적/물리적 제약 피처 API 테스트 결과 ===\n\n")
        for line in RESULT_LOG:
            f.write(line + "\n")
    print(f"\n[Report] 결과 저장 → {report_path}")


# ──────────────────────────────────────────────────────────
# 실행
# ──────────────────────────────────────────────────────────

if __name__ == '__main__':
    api = PublicDataAPI()

    test_spatial_functions()          # API 불필요 — 먼저 실행
    elev_ok      = test_elevation_api(api)
    crosswalk_ok = test_crosswalk_api(api)
    test_full_pipeline(api)

    print("\n" + "="*55)
    print("최종 요약")
    print("="*55)
    log("Summary", f"VWorld 고도 API",     "정상" if elev_ok      else "실패")
    log("Summary", f"서울 횡단보도 API",   "정상" if crosswalk_ok else "실패")

    save_report()
