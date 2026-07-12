WITH sector_volatility AS (

    SELECT
        sector,

        STDDEV(daily_return_pct) AS volatility,

        COUNT(DISTINCT ticker) AS asset_count

    FROM analytics.company_daily

    WHERE trade_date >= (
        SELECT MAX(trade_date)
        FROM analytics.company_daily
    ) - INTERVAL '30 days'

    GROUP BY sector

)

SELECT

    sector,

    ROUND(volatility::numeric,4) AS return_volatility_stddev,

    asset_count,

    RANK() OVER (
        ORDER BY volatility DESC
    ) AS volatility_rank

FROM sector_volatility

ORDER BY volatility_rank;