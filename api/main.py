import os
from fastapi import FastAPI, HTTPException, Query
from datetime import date, timedelta
import pandas as pd
import psycopg2

app = FastAPI()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASS = os.getenv("POSTGRES_PASSWORD")

conn_string = f"dbname='{DB_NAME}' user='{DB_USER}' host='{DB_HOST}' password='{DB_PASS}'"

@app.get("/metrics")
def get_metrics(start_date: date, end_date: date):
    """
    Endpoint que calcula CAC e ROAS, lendo os dados de um banco de dados Postgres.
    """
    try:
        if start_date >= end_date:
            raise HTTPException(status_code=400, detail="A data de início deve ser anterior à de fim.")

        period_duration = (end_date - start_date).days
        prior_start_date = start_date - timedelta(days=period_duration)

        query = f"""
        WITH date_periods AS (
            SELECT
                *,
                CASE
                    WHEN "date" >= '{start_date}' AND "date" < '{end_date}' THEN 'Current Period'
                    WHEN "date" >= '{prior_start_date}' AND "date" < '{start_date}' THEN 'Prior Period'
                    ELSE NULL
                END AS period
            FROM raw_ads_spend
            WHERE "date" >= '{prior_start_date}' AND "date" < '{end_date}'
        ),
        aggregated_metrics AS (
            SELECT period, SUM(spend) AS total_spend, SUM(conversions) AS total_conversions, SUM(conversions * 100) AS total_revenue
            FROM date_periods WHERE period IS NOT NULL GROUP BY period
        ),
        kpi_by_period AS (
            SELECT period, total_spend / NULLIF(total_conversions, 0) AS cac, total_revenue / NULLIF(total_spend, 0) AS roas
            FROM aggregated_metrics
        ),
        final_comparison AS (
            SELECT 'CAC' AS kpi, MAX(CASE WHEN period = 'Current Period' THEN cac END) AS current_value, MAX(CASE WHEN period = 'Prior Period' THEN cac END) AS prior_value FROM kpi_by_period
            UNION ALL
            SELECT 'ROAS' AS kpi, MAX(CASE WHEN period = 'Current Period' THEN roas END) AS current_value, MAX(CASE WHEN period = 'Prior Period' THEN roas END) AS prior_value FROM kpi_by_period
        )
        SELECT
            kpi,
            ROUND(current_value::numeric, 2) AS current_period_value,
            ROUND(prior_value::numeric, 2) AS prior_period_value,
            ROUND((((current_value - prior_value) / prior_value) * 100)::numeric, 2) || '%' AS delta
        FROM final_comparison;
        """
        con = psycopg2.connect(conn_string)
        df = pd.read_sql_query(query, con)
        con.close()
        results = df.to_dict('records')

        return {"requested_period": {"start_date": start_date, "end_date": end_date}, "comparison_data": results}
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
        raise HTTPException(status_code=500, detail=str(e))