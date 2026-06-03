import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from typing import Optional

class SpatialProcessor:
    """
    공간 데이터 전처리 및 연산을 담당하는 모듈 (Spatial Join 등)
    """

    def __init__(self, bas_shp_path: str):
        """
        :param bas_shp_path: 기초구역도(DS4) SHP 파일 경로
        """
        # SHP 파일 로드 및 좌표계를 EPSG:5179(또는 프로젝트 기준)로 통일
        try:
            self.bas_gdf = gpd.read_file(bas_shp_path)
            # 만약 좌표계 설정이 안 되어 있다면 가정 (예: EPSG:5179)
            if self.bas_gdf.crs is None:
                self.bas_gdf = self.bas_gdf.set_crs(epsg=5179)
            else:
                self.bas_gdf = self.bas_gdf.to_crs(epsg=5179)
            print(f"Loaded Basic District SHP. Total polygons: {len(self.bas_gdf)}")
        except Exception as e:
            print(f"Failed to load SHP file: {e}")
            self.bas_gdf = None

    def create_point_geometry(self, df: pd.DataFrame, lat_col: str = 'lat', lng_col: str = 'lon') -> gpd.GeoDataFrame:
        """
        위경도(4326)와 중부원점(2097)이 섞인 데이터프레임을 개별적으로 감지하여 변환합니다.
        """
        df = df.copy()
        df[lat_col] = pd.to_numeric(df[lat_col], errors='coerce')
        df[lng_col] = pd.to_numeric(df[lng_col], errors='coerce')
        valid_df = df.dropna(subset=[lat_col, lng_col]).copy()
        
        if valid_df.empty:
            return gpd.GeoDataFrame(columns=df.columns, geometry=[], crs="EPSG:5179")

        # 위경도 데이터와 중부원점 데이터를 분리
        wgs84_mask = valid_df[lat_col].abs() < 1000
        df_wgs84 = valid_df[wgs84_mask].copy()
        df_tm = valid_df[~wgs84_mask].copy()
        
        gdfs = []
        
        # 1. 위경도 처리
        if not df_wgs84.empty:
            geom_wgs = [Point(xy) for xy in zip(df_wgs84[lng_col], df_wgs84[lat_col])]
            gdf_wgs = gpd.GeoDataFrame(df_wgs84, geometry=geom_wgs, crs="EPSG:4326")
            gdfs.append(gdf_wgs.to_crs(epsg=5179))
            
        # 2. 중부원점 처리
        if not df_tm.empty:
            geom_tm = [Point(xy) for xy in zip(df_tm[lng_col], df_tm[lat_col])]
            gdf_tm = gpd.GeoDataFrame(df_tm, geometry=geom_tm, crs="EPSG:2097")
            gdfs.append(gdf_tm.to_crs(epsg=5179))
            
        # 결과 합치기
        if not gdfs:
            return gpd.GeoDataFrame(columns=df.columns, geometry=[], crs="EPSG:5179")
            
        final_gdf = pd.concat(gdfs, ignore_index=True)
        return final_gdf

    def assign_bas_id(self, point_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        점 데이터(Point)를 기초구역도(Polygon)에 Spatial Join (sjoin) 하여 
        해당 점이 위치한 블록의 BAS_ID를 할당합니다.
        """
        if self.bas_gdf is None:
            raise ValueError("Basic District SHP is not loaded.")
        
        # 좌표계 정합성 강제 확보 (sjoin 실패 방지)
        if point_gdf.crs != self.bas_gdf.crs:
            point_gdf = point_gdf.to_crs(self.bas_gdf.crs)
            
        # sjoin 수행 (내부 포함 관계 확인)
        joined_gdf = gpd.sjoin(point_gdf, self.bas_gdf[['BAS_ID', 'SIG_CD', 'geometry']], how='left', predicate='within')
        
        # 디버깅: 영업/폐업별 매핑 성공률 확인
        if 'is_closed' in joined_gdf.columns:
            open_success = joined_gdf[joined_gdf['is_closed'] == 0]['BAS_ID'].notna().sum()
            closed_success = joined_gdf[joined_gdf['is_closed'] == 1]['BAS_ID'].notna().sum()
            print(f"   - Mapping Success: Open {open_success}, Closed {closed_success}")
            
        return joined_gdf

    def interpolate_masked_sales(self, df: pd.DataFrame, target_col: str, group_cols: list) -> pd.DataFrame:
        """
        [결측치 처리] 매출 마스킹 처리된 데이터를 특정 그룹(예: 동일 상권/분기)의 평균값으로 보간합니다.
        
        :param df: 매출 데이터가 포함된 DataFrame (DS2)
        :param target_col: 보간할 매출 컬럼
        :param group_cols: 그룹을 묶을 기준 컬럼 (예: ['YEAR_QUARTER', 'TRDAR_CD'])
        :return: 보간이 완료된 DataFrame
        """
        # 그룹별 평균을 구하여 마스킹(NaN) 값 채우기
        df[target_col] = df.groupby(group_cols)[target_col].transform(lambda x: x.fillna(x.mean()))
        
        # 그룹 평균도 없는 경우 전체 평균으로 대체
        df[target_col] = df[target_col].fillna(df[target_col].mean())
        
        return df
