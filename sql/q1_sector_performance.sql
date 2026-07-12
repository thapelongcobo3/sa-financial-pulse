WITH latest_date AS (
    SELECT MAX(trade_date) AS max_date FROM analytics.sector_daily
),
weekly_returns AS (
    SELECT 
        sd.sector,
        AVG(sd.avg_daily_return_pct) AS avg_weekly_return_pct
    FROM analytics.sector_daily sd, latest_date ld
    WHERE sd.trade_date >= ld.max_date - INTERVAL '7 days'
    GROUP BY sd.sector
)
SELECT 
    sector,
    ROUND(avg_weekly_return_pct, 4) AS avg_weekly_return_pct,
    RANK() OVER (ORDER BY avg_weekly_return_pct DESC) AS performance_rank
FROM weekly_returns
ORDER BY performance_rank;

