-- database/schema.sql
-- PostGIS 초기 스키마 설정 파일
-- 담당: DB 파트 팀원
-- 실행: psql -U capstone_user -d survival_db -f schema.sql

-- PostGIS 확장 활성화
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- 1. 점포 테이블 (인허가/폐업 데이터)
CREATE TABLE IF NOT EXISTS stores (
    id              SERIAL PRIMARY KEY,
    store_name      VARCHAR(200),
    business_type   VARCHAR(100),           -- 업종 분류 (예: 한식, 카페, 편의점)
    address         TEXT,
    geom            GEOMETRY(Point, 4326),  -- GPS 좌표 (WGS84)
    open_date       DATE,                   -- 개업일
    close_date      DATE,                   -- 폐업일 (NULL이면 현재 운영 중)
    duration_months INTEGER,                -- 생존 기간 (월 단위)
    is_closed       BOOLEAN DEFAULT FALSE   -- 폐업 여부 (이벤트 발생 여부)
);

-- 2. POI 테이블 (마이크로 주변 환경 데이터)
CREATE TABLE IF NOT EXISTS poi (
    id          SERIAL PRIMARY KEY,
    poi_type    VARCHAR(100),           -- POI 종류 (subway, kindergarten, mart, bus_stop ...)
    poi_name    VARCHAR(200),
    geom        GEOMETRY(Point, 4326),
    metadata    JSONB                   -- 추가 속성 (예: 지하철 노선, 마트 브랜드 등)
);

-- 3. 공간 인덱스 (쿼리 성능 최적화)
CREATE INDEX IF NOT EXISTS idx_stores_geom ON stores USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_poi_geom    ON poi    USING GIST (geom);
