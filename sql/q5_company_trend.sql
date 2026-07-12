SELECT
    trade_date,
    ticker,
    company_name,
    close_rands,
    ma_7_day,
    ma_30_day,
    daily_return_pct,
    volume
FROM analytics.company_daily
WHERE ticker = :'ticker'
AND trade_date >= (
    SELECT MAX(trade_date)
    FROM analytics.company_daily
) - INTERVAL '90 days'
ORDER BY trade_date;