CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS raw.daily_prices (
    id              SERIAL PRIMARY KEY,
    ticker          VARCHAR(20)     NOT NULL,
    trade_date      DATE            NOT NULL,
    open_cents      NUMERIC(12, 2)  NOT NULL,
    high_cents      NUMERIC(12, 2)  NOT NULL,
    low_cents       NUMERIC(12, 2)  NOT NULL,
    close_cents     NUMERIC(12, 2)  NOT NULL,
    volume          BIGINT          NOT NULL,
    dividends       NUMERIC(10, 4)  DEFAULT 0,
    stock_splits    NUMERIC(10, 4)  DEFAULT 0,
    ingested_at     TIMESTAMP       DEFAULT NOW(),
    UNIQUE (ticker, trade_date)
);

CREATE TABLE IF NOT EXISTS analytics.company_daily (
    id                  SERIAL PRIMARY KEY,
    ticker              VARCHAR(20)     NOT NULL,
    company_name        VARCHAR(100)    NOT NULL,
    sector              VARCHAR(50)     NOT NULL,
    trade_date          DATE            NOT NULL,
    open_rands          NUMERIC(12, 2)  NOT NULL,
    high_rands          NUMERIC(12, 2)  NOT NULL,
    low_rands           NUMERIC(12, 2)  NOT NULL,
    close_rands         NUMERIC(12, 2)  NOT NULL,
    volume              BIGINT          NOT NULL,
    daily_return_pct    NUMERIC(8, 4),
    ma_7_day            NUMERIC(12, 2),
    ma_30_day           NUMERIC(12, 2),
    UNIQUE (ticker, trade_date)
);

CREATE TABLE IF NOT EXISTS analytics.sector_daily (
    id                      SERIAL PRIMARY KEY,
    sector                  VARCHAR(50)     NOT NULL,
    trade_date              DATE            NOT NULL,
    avg_daily_return_pct    NUMERIC(8, 4),
    total_volume            BIGINT,
    company_count           INTEGER,
    UNIQUE (sector, trade_date)
);