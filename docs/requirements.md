# SA Financial Pulse — Project Requirements
**Author:** Thapelo  
**Status:** Phase 1 — In Progress  
**Last Updated:** June 2026

---

## 1. What This Project Is

The idea behind this project came from a simple question I kept asking myself — *how do JSE sectors actually move week to week, and which companies are driving that?* I couldn't find a clean, simple way to see that without going through Bloomberg or a paid terminal, so I decided to build something myself.

`sa-financial-pulse` is a data pipeline that pulls daily share price data for 25 JSE-listed companies, cleans and structures it, loads it into a PostgreSQL database, and answers five specific business questions through SQL queries. Think of it as a lightweight version of what a financial data team at a firm like Capitec or Discovery would build for internal reporting.

Right now it runs locally and outputs results to the terminal. The plan is to move it to AWS, add scheduling with Airflow, transformations with dbt, and eventually a proper dashboard. But I'm building the foundation first and doing it properly — clean schema, separated raw and analytics layers, reproducible scripts.

The people who would actually use something like this: portfolio managers, equity analysts, or any team that needs a daily view of how the market is moving without paying for a Bloomberg subscription.

---

## 2. Where the Data Comes From

I'm using **yfinance** — a Python library that pulls data directly from Yahoo Finance. No API key needed, no cost, updated daily.

```
pip install yfinance
```

For JSE companies, the tickers follow the `.JO` suffix format — for example, Capitec is `CPI.JO`, MTN is `MTN.JO`.

**Fields yfinance returns per company per day:**

| Field | What it means |
|-------|---------------|
| `Date` | The trading date |
| `Open` | Price when the market opened |
| `High` | Highest price during the day |
| `Low` | Lowest price during the day |
| `Close` | Price when the market closed |
| `Volume` | Number of shares traded |
| `Dividends` | Dividend paid that day (usually 0) |
| `Stock Splits` | Split ratio that day (usually 0) |

**One thing I had to figure out the hard way — JSE prices come back in cents, not rands.**  
A Shoprite close of `34200` means R342.00. I handle the conversion (divide by 100) in the cleaning script before anything touches the database. The raw table stores cents exactly as received; the analytics tables store rands.

---

## 3. The 25 Companies I'm Tracking

I picked these across six sectors to give the sector-level analysis enough coverage to be meaningful. Five financials, five resources, five retail, four telecoms, one diversified (Remgro), and five tech.

| # | Company | Ticker | Sector |
|---|---------|--------|--------|
| 1 | FirstRand | FSR.JO | Financials |
| 2 | Standard Bank | SBK.JO | Financials |
| 3 | Capitec | CPI.JO | Financials |
| 4 | Absa | ABG.JO | Financials |
| 5 | Sanlam | SLM.JO | Financials |
| 6 | BHP Group | BHG.JO | Resources |
| 7 | Anglo American | AGL.JO | Resources |
| 8 | Glencore | GLN.JO | Resources |
| 9 | Gold Fields | GFI.JO | Resources |
| 10 | Sasol | SOL.JO | Resources |
| 11 | Shoprite | SHP.JO | Retail |
| 12 | Woolworths | WHL.JO | Retail |
| 13 | Clicks | CLS.JO | Retail |
| 14 | Mr Price | MRP.JO | Retail |
| 15 | Pick n Pay | PIK.JO | Retail |
| 16 | MTN | MTN.JO | Telecoms |
| 17 | Vodacom | VOD.JO | Telecoms |
| 18 | Telkom | TKG.JO | Telecoms |
| 19 | Blue Label Unlimited Group Limited | BLU.JO | Telecoms |
| 20 | Remgro | REM.JO | Diversified |
| 21 | Naspers | NPN.JO | Technology |
| 22 | Prosus | PRX.JO | Technology |
| 23 | Bytes Technology | BYI.JO | Technology |
| 24 | Datatec | DTC.JO | Technology |
| 25 | Karooooo | KRO.JO | Technology |

*Note: MultiChoice (MCG.JO) was swapped out for Blue Label Unlimited Group Limited (BLU.JO) in the Telecoms slot — MultiChoice delisted from the JSE on 10 December 2025 after Canal+ completed its acquisition and squeeze-out of remaining shareholders, so the ticker is no longer available via yfinance.*

---

## 4. The 5 Business Questions This Pipeline Answers

These aren't just nice-to-haves — they're my success criteria. If the pipeline can answer all five correctly from the database, Phase 1 is done.

**Q1 — Sector Performance Ranking**  
*Which JSE sectors performed best and worst this week?*  
Reads from `analytics.sector_daily`. Returns average week-over-week return per sector, ranked. This is the headline number — the one a portfolio manager looks at on a Monday morning.

**Q2 — Top and Bottom Movers**  
*Which 5 companies had the highest and lowest daily returns today?*  
Reads from `analytics.company_daily`. Returns a ranked table by daily return %. The kind of thing a trader checks every morning before the market opens.

**Q3 — Volume Leaders**  
*Which companies are seeing unusual trading volume this month?*  
Reads from `analytics.company_daily`. Compares current volume against the 30-day average per company. Volume spikes often come before news — earnings, mergers, policy changes.

**Q4 — Sector Volatility**  
*Which sectors are most volatile over the last 30 days?*  
Reads from `analytics.company_daily`. Calculated as standard deviation of daily returns per sector. My expectation going in: Resources tops this list almost every time because of commodity price swings and currency sensitivity.

**Q5 — Individual Company Trend**  
*How has a specific company's share price moved over the last 90 days?*  
Reads from `analytics.company_daily`. Returns closing price per day for a given ticker. The view a portfolio manager would pull up when reviewing a single position.

---

## 5. Database Schema

Database name: `sa_financial_pulse`  
Two schemas: `raw` (source data, untouched) and `analytics` (cleaned and aggregated).

I separated raw from analytics on purpose. If something goes wrong in the transformation logic, the raw data is still intact and I can reprocess. This is standard practice in data engineering and I wanted to build that habit from the start.

### `raw.daily_prices`
Stores exactly what comes out of yfinance. Prices in cents. No derived fields.

```sql
CREATE SCHEMA IF NOT EXISTS raw;

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
```

### `analytics.company_daily`
One row per company per day. Prices converted to rands here. Derived fields calculated here.

```sql
CREATE SCHEMA IF NOT EXISTS analytics;

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
```

### `analytics.sector_daily`
One row per sector per day. Aggregated from `analytics.company_daily`.

```sql
CREATE TABLE IF NOT EXISTS analytics.sector_daily (
    id                      SERIAL PRIMARY KEY,
    sector                  VARCHAR(50)     NOT NULL,
    trade_date              DATE            NOT NULL,
    avg_daily_return_pct    NUMERIC(8, 4),
    total_volume            BIGINT,
    company_count           INTEGER,
    UNIQUE (sector, trade_date)
);
```

---

## 6. How the Data Flows

```
yfinance (Yahoo Finance)
        ↓
fetch_prices.py
  — downloads daily prices for all 25 tickers
  — saves to data/raw/prices_YYYY-MM-DD.csv
        ↓
clean_prices.py
  — converts cents to rands
  — calculates daily return %, 7-day MA, 30-day MA
  — saves to data/clean/prices_YYYY-MM-DD.csv
        ↓
load_to_postgres.py
  — raw CSV  →  raw.daily_prices
  — clean CSV →  analytics.company_daily
        ↓
aggregate.py
  — reads analytics.company_daily
  — aggregates by sector → analytics.sector_daily
        ↓
PostgreSQL (sa_financial_pulse)
        ↓
sql/ query files
  — answer the 5 business questions above
        ↓
Terminal output
```

Everything runs manually in Phase 1. In Phase 3 this whole flow becomes an Airflow DAG that triggers itself daily.

---

## 7. What Phase 1 Covers (and What It Doesn't)

**Building now:**
- `fetch_prices.py` — ingestion
- `clean_prices.py` — transformation
- `load_to_postgres.py` — loading raw and clean data into PostgreSQL
- `aggregate.py` — aggregates company_daily into sector_daily
- `sql/` — 5 query files, one per business question
- Local PostgreSQL only
- Manual terminal execution
- `requirements.txt` and this document

**Not in scope for Phase 1:**

| Phase | What gets added |
|-------|-----------------|
| 2 | AWS S3 for raw file storage, AWS RDS replaces local PostgreSQL |
| 3 | Apache Airflow — pipeline runs on a daily schedule automatically |
| 4 | dbt Core — replaces raw SQL transforms, adds data quality tests |
| 5 | Terraform — provisions AWS infrastructure, Docker wraps the environment |
| 6 | Redshift Serverless, Metabase dashboard, CloudWatch monitoring, GitHub Actions CI/CD |

The folder structure I'm using now (`ingestion/`, `transformation/`, `loading/`, `sql/`) stays the same as the project grows. Later phases add folders — `dbt/`, `airflow/`, `terraform/` — but nothing gets restructured or thrown away.