# SA Financial Pulse — Architecture
**Author:** Thapelo  
**Status:** Phase 1 — In Progress  
**Last Updated:** June 2026

---

## 1. Folder Structure

This is the complete project layout when Phase 1 is done. Every file has a home before I write a single line of code.

```
sa-financial-pulse/
├── docs/
│   ├── requirements.md
│   └── architecture.md
├── data/
│   ├── raw/
│   └── clean/
├── ingestion/
│   └── fetch_prices.py
├── transformation/
│   └── clean_prices.py
├── loading/
│   └── load_to_postgres.py
├── aggregation/
│   └── aggregate.py
├── sql/
│   ├── q1_sector_performance.sql
│   ├── q2_top_bottom_movers.sql
│   ├── q3_volume_leaders.sql
│   ├── q4_sector_volatility.sql
│   └── q5_company_trend.sql
├── requirements.txt
└── README.md
```

---

## 2. Script Responsibilities

**`ingestion/fetch_prices.py`**  
This script is the entry point for the entire pipeline. It uses the `yfinance` library to download daily share price data for all 25 JSE-listed companies and saves the result as a date-stamped CSV file in `data/raw/`. It takes no file input — it pulls directly from Yahoo Finance on each run. The output is a raw, unmodified snapshot of the day's prices exactly as the source returned them, in cents.

**`transformation/clean_prices.py`**  
This script reads the raw CSV produced by `fetch_prices.py` and applies all necessary cleaning and enrichment using pandas. It converts prices from cents to rands, handles any null values, standardises column names, and calculates three derived fields: daily return percentage, 7-day moving average, and 30-day moving average. The output is a clean, analytics-ready CSV saved to `data/clean/` with the same date stamp as the raw file it came from.

**`loading/load_to_postgres.py`**  
This script takes both the raw and clean CSVs and loads them into the `sa_financial_pulse` PostgreSQL database. The raw CSV loads into `raw.daily_prices` without any modification — exactly as received from the transformation step. The clean CSV loads into `analytics.company_daily`. This script does nothing else; it does not calculate, aggregate, or transform anything.

**`aggregation/aggregate.py`**  
This script reads from `analytics.company_daily` inside PostgreSQL and produces the sector-level summary table `analytics.sector_daily`. It groups company-level data by sector and trade date, calculating average daily return, total volume, and company count per sector per day. It is the final step before the SQL query files run, and it is the only script that writes to `analytics.sector_daily`.

---

## 3. Data Flow

```
yfinance (Yahoo Finance)
        ↓
fetch_prices.py
        ↓ data/raw/prices_YYYY-MM-DD.csv
clean_prices.py
        ↓ data/clean/prices_YYYY-MM-DD.csv
load_to_postgres.py
        ↓ raw.daily_prices
        ↓ analytics.company_daily
aggregate.py
        ↓ analytics.sector_daily
sql/ query files
        ↓
Terminal output
```

All five steps run manually in Phase 1 in the order shown above. In Phase 3 this entire flow becomes a single Airflow DAG that runs on a daily schedule.

---

## 4. Schema Design Decisions

- **Why `raw` and `analytics` are separate schemas.** I wanted a clear boundary between data that came from the source and data that my code touched. If I introduce a bug in the cleaning or transformation logic, the raw data is completely unaffected — I can fix the bug and reprocess from `raw.daily_prices` without re-fetching anything from Yahoo Finance. This separation also makes it immediately obvious to anyone reading the schema which layer they are in and what guarantees they can expect from the data.

- **Why prices stay in cents in `raw.daily_prices` instead of converting immediately.** The raw table is meant to be an exact record of what the source gave me, nothing more. If I convert to rands on the way in, I lose the ability to verify that my transformation logic is correct — I can no longer compare raw against clean and confirm the conversion happened properly. Keeping cents in raw and rands in analytics also makes the cents-to-rands conversion an explicit, traceable step in `clean_prices.py` rather than something that silently happens during ingestion.

- **Why `aggregate.py` is a separate script and not part of `load_to_postgres.py`.** Each script in this pipeline has one job. `load_to_postgres.py` loads data — it moves CSVs into tables. `aggregate.py` transforms data — it reads from one table and writes a derived result into another. Mixing those two responsibilities into a single script makes debugging harder: if `analytics.sector_daily` has wrong numbers, I want to know immediately that the problem is in aggregation, not somewhere inside a script that is also handling file loading. Keeping them separate is the same principle behind why `raw` and `analytics` are different schemas — every layer of this pipeline should have a single, clearly defined responsibility.