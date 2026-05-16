-- database/schema.sql
-- API 서버용 스키마 (ERD 기준)
-- docker compose down -v 후 docker compose up -d 로 재초기화

-- 1. 사용자 테이블
CREATE TABLE IF NOT EXISTS users (
    id          BIGSERIAL PRIMARY KEY,
    email       VARCHAR(255) NOT NULL UNIQUE,
    password    VARCHAR(255) NOT NULL,
    nickname    VARCHAR(100),
    created_at  TIMESTAMP   NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- 2. 블록 테이블 (서울 격자 단위 상권)
CREATE TABLE IF NOT EXISTS blocks (
    id              BIGSERIAL PRIMARY KEY,
    bas_id          VARCHAR(20)  NOT NULL UNIQUE,
    name            VARCHAR(100),
    region          VARCHAR(100),
    main_industry   VARCHAR(50),
    csi_score       NUMERIC(4,2),
    lat             NUMERIC(10,7),
    lng             NUMERIC(10,7),
    area            NUMERIC(12,2),
    adm_dr_cd       VARCHAR(20),
    adm_dr_nm       VARCHAR(100)
);

-- 3. 예측 결과 테이블
CREATE TABLE IF NOT EXISTS predictions (
    id              BIGSERIAL PRIMARY KEY,
    block_id        BIGINT       NOT NULL REFERENCES blocks(id),
    csi_score       NUMERIC(4,2),
    risk_grade      VARCHAR(20),
    closure_rate    NUMERIC(5,2),
    open_rate       NUMERIC(5,2),
    survival_6m     NUMERIC(5,2),
    risk_score      INTEGER,
    predicted_at    TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- 4. 생존 확률 곡선 테이블
CREATE TABLE IF NOT EXISTS survival_curve (
    id              BIGSERIAL PRIMARY KEY,
    block_id        BIGINT       NOT NULL REFERENCES blocks(id),
    month           INTEGER      NOT NULL,
    survival_rate   NUMERIC(5,2) NOT NULL
);

-- 5. SHAP 피처 기여도 테이블
CREATE TABLE IF NOT EXISTS shap_features (
    id          BIGSERIAL PRIMARY KEY,
    block_id    BIGINT       NOT NULL REFERENCES blocks(id),
    rank        INTEGER      NOT NULL,
    name        VARCHAR(100) NOT NULL,
    shap_value  NUMERIC(8,4) NOT NULL,
    label       VARCHAR(200)
);

-- 6. 점포 테이블
CREATE TABLE IF NOT EXISTS stores (
    id              BIGSERIAL PRIMARY KEY,
    block_id        BIGINT       NOT NULL REFERENCES blocks(id),
    name            VARCHAR(200),
    industry        VARCHAR(100),
    lat             NUMERIC(10,7),
    lng             NUMERIC(10,7),
    open_date       DATE,
    close_date      DATE,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    survival_days   INTEGER
);

-- 7. 업종 통계 테이블
CREATE TABLE IF NOT EXISTS industry_stats (
    id                  BIGSERIAL PRIMARY KEY,
    block_id            BIGINT       NOT NULL REFERENCES blocks(id),
    industry_name       VARCHAR(100) NOT NULL,
    store_count         INTEGER,
    avg_survival_days   INTEGER,
    ratio               NUMERIC(5,2),
    recorded_at         DATE         NOT NULL
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_blocks_lat_lng        ON blocks (lat, lng);
CREATE INDEX IF NOT EXISTS idx_blocks_region         ON blocks (region);
CREATE INDEX IF NOT EXISTS idx_predictions_block     ON predictions (block_id);
CREATE INDEX IF NOT EXISTS idx_survival_curve_block  ON survival_curve (block_id);
CREATE INDEX IF NOT EXISTS idx_shap_features_block   ON shap_features (block_id);
CREATE INDEX IF NOT EXISTS idx_stores_block          ON stores (block_id);
CREATE INDEX IF NOT EXISTS idx_stores_open_date      ON stores (open_date);
CREATE INDEX IF NOT EXISTS idx_industry_stats_block  ON industry_stats (block_id);
