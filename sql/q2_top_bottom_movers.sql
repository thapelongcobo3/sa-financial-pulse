-- q2_top_bottom_movers.sql
WITH ranked_movers AS (
    SELECT
        trade_date,
        ticker,
        company_name,
        sector,
        daily_return_pct,
        RANK() OVER (ORDER BY daily_return_pct DESC) AS top_rank,
        RANK() OVER (ORDER BY daily_return_pct ASC) AS bottom_rank
    FROM analytics.company_daily
    WHERE trade_date = (
        SELECT MAX(trade_date)
        FROM analytics.company_daily
    )
)
SELECT
    1 AS movement_order,
    'TOP' AS movement_type,
    top_rank AS movement_rank,
    ticker,
    company_name,
    sector,
    daily_return_pct
FROM ranked_movers
WHERE top_rank <= 5

UNION ALL

SELECT
    2 AS movement_order,
    'BOTTOM' AS movement_type,
    bottom_rank AS movement_rank,
    ticker,
    company_name,
    sector,
    daily_return_pct
FROM ranked_movers
WHERE bottom_rank <= 5

ORDER BY
    movement_order,
    movement_rank;