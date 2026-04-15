-- database/seed.sql
-- 대상 DB: survival_db (docker-compose.yml의 POSTGRES_DB와 동일)
-- 개발/테스트용 초기 샘플 데이터
-- docker compose up 시 schema.sql 다음에 자동 실행됩니다.
-- 실제 프로젝트 데이터 적재 전 기능 테스트 용도입니다.

-- ── 샘플 점포 데이터 (서울 강남구 일대) ──
INSERT INTO stores (store_name, business_type, address, geom, open_date, close_date, duration_months, is_closed) VALUES
('강남치킨', '치킨',   '서울 강남구 테헤란로 1길', ST_SetSRID(ST_MakePoint(127.0276, 37.4979), 4326), '2018-03-01', '2019-08-31', 17,  TRUE),
('강남카페', '카페',   '서울 강남구 역삼동 123',   ST_SetSRID(ST_MakePoint(127.0312, 37.5001), 4326), '2020-01-01', NULL,         NULL, FALSE),
('역삼분식', '분식',   '서울 강남구 역삼로 45',    ST_SetSRID(ST_MakePoint(127.0350, 37.5010), 4326), '2015-06-01', '2017-12-31', 30,  TRUE),
('강남한식당', '한식', '서울 강남구 강남대로 99',  ST_SetSRID(ST_MakePoint(127.0279, 37.4958), 4326), '2010-01-01', '2023-12-31', 167, TRUE);

-- ── 샘플 POI 데이터 (지하철역) ──
INSERT INTO poi (poi_type, poi_name, geom, metadata) VALUES
('subway', '강남역', ST_SetSRID(ST_MakePoint(127.0276, 37.4979), 4326), '{"line": "2호선, 신분당선"}'),
('subway', '역삼역', ST_SetSRID(ST_MakePoint(127.0365, 37.5001), 4326), '{"line": "2호선"}'),
('subway', '선릉역', ST_SetSRID(ST_MakePoint(127.0490, 37.5045), 4326), '{"line": "2호선, 분당선"}');
