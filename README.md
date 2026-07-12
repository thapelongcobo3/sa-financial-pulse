# 📈 SA Financial Pulse

Built while learning the foundations of Data Engineering using Python, pandas and PostgreSQL.

A Python and PostgreSQL data engineering project that downloads daily share price data for 25 JSE-listed companies, transforms it into an analytics-ready dataset, stores it in PostgreSQL, and answers five real business questions using SQL.

---

## About

I built this project as part of learning data engineering.

One thing I realized early on was that I needed a dataset that changed over time so I could build a complete data pipeline - from ingestion all the way to querying the data with SQL.

While looking for free APIs to work with, I noticed that most beginner-friendly datasets tend to fall into a few categories like financial markets, weather, and social or media data. Financial data interested me the most because it naturally fits the kind of pipelines data engineers build.

After exploring different options, I came across `yfinance`, a Python library that provides access to Yahoo Finance market data. It let me start working immediately without having to register for an API key or worry about usage limits, making it perfect for learning.

Using that data, I built **SA Financial Pulse** - a small end-to-end data pipeline that downloads daily share prices for 25 JSE-listed companies, transforms and enriches the data with pandas, stores it in PostgreSQL, aggregates it into sector-level metrics, and answers five business questions using SQL.

The goal of this project wasn't to build a production-grade financial platform. It was to practise the Python, SQL and data engineering concepts I was learning by building something from start to finish.

---

## Features

- Download daily share price data for 25 JSE-listed companies
- Store raw market data as date-stamped CSV files
- Clean and transform the data using pandas
- Convert prices from cents to rands
- Calculate daily returns
- Calculate 7-day and 30-day moving averages
- Load raw and analytics data into PostgreSQL
- Aggregate company-level data into sector-level metrics
- Answer five business questions using SQL

---

## Data Pipeline

```
Yahoo Finance (yfinance)
            │
            ▼
fetch_prices.py
Downloads market data
            │
            ▼
clean_prices.py
Transforms and enriches the data
            │
            ▼
load_to_postgres.py
Loads data into PostgreSQL
            │
            ▼
aggregate.py
Builds sector-level metrics
            │
            ▼
SQL Queries
Business reports
```

---

## Business Questions

This project answers the following questions directly from PostgreSQL:

1. Which JSE sectors performed best and worst this week?
2. Which companies had the biggest gains and losses today?
3. Which companies are experiencing unusually high trading volume?
4. Which sectors have been the most volatile over the last 30 days?
5. How has a specific company's share price changed over the last 90 days?

---

## Tech Stack

### Python

- Object-Oriented Programming
- pandas
- pathlib
- psycopg2
- python-dotenv

### PostgreSQL

- Multiple schemas
- Aggregate functions
- Window functions
- CTEs
- Batch inserts
- Conflict handling

### Other Tools

- Git & GitHub
- Linux CLI
- VS Code

---

## Project Structure

```
sa-financial-pulse/
├── aggregation/
│   ├── __init__.py
│   └── aggregate.py
│
├── config/
│   └── companies.py
│
├── data/
│   ├── clean/
│   └── raw/
│
├── docs/
│   ├── architecture.md
│   ├── postgresql_setup_guide.md
│   └── requirements.md
│
├── ingestion/
│   ├── __init__.py
│   └── fetch_prices.py
│
├── loading/
│   ├── __init__.py
│   └── load_to_postgres.py
│
├── sql/
│   ├── q1_sector_performance.sql
│   ├── q2_top_bottom_movers.sql
│   ├── q3_volume_leaders.sql
│   ├── q4_sector_volatility.sql
│   └── q5_company_trend.sql
│
├── transformation/
│   ├── __init__.py
│   └── clean_prices.py
│
├── .env.example
├── .gitignore
├── README.md
└── setup_db.sql
```

---

## Documentation

I wanted this project to be something another student could clone and learn from, so I documented the thinking behind the project as I built it.

The `docs/` folder contains:

- **requirements.md** - the original project requirements, business questions and database schema.
- **architecture.md** - explains how the pipeline works, why each script has a single responsibility, and how data flows through the project.
- **postgresql_setup_guide.md** - a step-by-step guide (with all problems you might come across and how to solvw them) for setting up PostgreSQL from the terminal, especially if you're coming from SQLite like me.

---

## Database Design

The database is split into two schemas.

### raw

Stores the data exactly as it comes from Yahoo Finance.

```
raw.daily_prices
```

### analytics

Stores cleaned and aggregated data used for analysis.

```
analytics.company_daily
analytics.sector_daily
```

Keeping these schemas separate means the original source data always remains untouched. If I ever change the transformation logic or introduce a bug, I can rebuild the analytics layer directly from the raw data without downloading everything again.

---

## Running the Pipeline

Clone the repository.

```bash
git clone https://github.com/thapelongcobo3/sa-financial-pulse.git

cd sa-financial-pulse
```

Run each stage of the pipeline from the project root.

```bash
python3 -m ingestion.fetch_prices

python3 -m transformation.clean_prices

python3 -m loading.load_to_postgres

python3 -m aggregation.aggregate
```

---

## Running the SQL Reports

Each SQL file answers one of the five business questions.

Example:

```bash
sudo -u postgres psql \
-d sa_financial_pulse \
-v ticker='FSR.JO' \
-f sql/q5_company_trend.sql
```

Available reports:

- `q1_sector_performance.sql`
- `q2_top_bottom_movers.sql`
- `q3_volume_leaders.sql`
- `q4_sector_volatility.sql`
- `q5_company_trend.sql`

---

## Skills Practised

Building this project gave me hands-on experience with:

- Designing a small ETL pipeline
- Writing modular Python using classes
- Working with CSV data using pandas
- Loading data into PostgreSQL
- Writing analytical SQL queries
- Using window functions and CTEs
- Organising a Python project into packages
- Using Git throughout development