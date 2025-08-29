WITH reference_date AS (
    SELECT MAX(date::date) AS max_date FROM raw_ads_spend
),
date_periods AS (
    SELECT
        *,
        CASE
            WHEN date::date > (SELECT max_date FROM reference_date) - INTERVAL '30 days' AND date::date <= (SELECT max_date FROM reference_date) THEN 'Last 30 Days'
            WHEN date::date > (SELECT max_date FROM reference_date) - INTERVAL '60 days' AND date::date <= (SELECT max_date FROM reference_date) - INTERVAL '30 days' THEN 'Prior 30 Days'
            ELSE NULL
        END AS period
    FROM raw_ads_spend
    WHERE date::date > (SELECT max_date FROM reference_date) - INTERVAL '60 days'
),
aggregated_metrics AS (
    SELECT
        period,
        SUM(spend) AS total_spend,
        SUM(conversions) AS total_conversions,
        SUM(conversions * 100) AS total_revenue
    FROM date_periods
    WHERE period IS NOT NULL
    GROUP BY period
),
kpi_by_period AS (
    SELECT
        period,
        total_spend / NULLIF(total_conversions, 0) AS cac,
        total_revenue / NULLIF(total_spend, 0) AS roas
    FROM aggregated_metrics
),
final_comparison AS (
    SELECT
        'CAC' AS kpi,
        MAX(CASE WHEN period = 'Last 30 Days' THEN cac END) AS current_value,
        MAX(CASE WHEN period = 'Prior 30 Days' THEN cac END) AS prior_value
    FROM kpi_by_period
    UNION ALL
    SELECT
        'ROAS' AS kpi,
        MAX(CASE WHEN period = 'Last 30 Days' THEN roas END) AS current_value,
        MAX(CASE WHEN period = 'Prior 30 Days' THEN roas END) AS prior_value
    FROM kpi_by_period
)
SELECT
    kpi,
    ROUND(current_value::numeric, 2) AS last_30_days,
    ROUND(prior_value::numeric, 2) AS prior_30_days,
    ROUND((((current_value - prior_value) / prior_value) * 100)::numeric, 2) || '%' AS delta
FROM final_comparison;