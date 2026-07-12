WITH volume_stats AS (

    SELECT
        trade_date,
        ticker,
        company_name,
        volume,

        AVG(volume) OVER (
            PARTITION BY ticker
        ) AS avg_volume_30d

    FROM analytics.company_daily

    WHERE trade_date >= (
        SELECT MAX(trade_date)
        FROM analytics.company_daily
    ) - INTERVAL '30 days'

)

SELECT
    trade_date,
    ticker,
    company_name,
    volume AS current_volume,
    ROUND(avg_volume_30d, 0) AS avg_volume_30d,

    ROUND(
        volume / NULLIF(avg_volume_30d, 0),
        2
    ) AS volume_spike_multiplier

FROM volume_stats

WHERE trade_date = (
    SELECT MAX(trade_date)
    FROM analytics.company_daily
)

AND volume > avg_volume_30d

ORDER BY volume_spike_multiplier DESC

LIMIT 10;