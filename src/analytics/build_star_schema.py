from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[2]
FINAL_PARQUET = ROOT / "data/processed/prices_with_rainfall.parquet"
DB_PATH = ROOT / "data/analytics" / "market_prices.duckdb"

DB_PATH.parent.mkdir(parents=True, exist_ok=True)

con = duckdb.connect(str(DB_PATH))
con.execute("CREATE SCHEMA IF NOT EXISTS analytics;")

con.execute(f"""
    CREATE OR REPLACE TABLE analytics.dim_date AS
    SELECT
        ROW_NUMBER() OVER (ORDER BY date) AS date_id,
        date,
        EXTRACT(YEAR FROM date) AS year,
        EXTRACT(MONTH FROM date) AS month,
        EXTRACT(DAY FROM date) AS day
    FROM (
        SELECT DISTINCT CAST(date AS DATE) AS date
        FROM read_parquet('{FINAL_PARQUET}')
    )
""")

con.execute(f"""
    CREATE OR REPLACE TABLE analytics.dim_market AS
    SELECT
        ROW_NUMBER() OVER (ORDER BY market) AS market_id,
        market
    FROM (
        SELECT DISTINCT market
        FROM read_parquet('{FINAL_PARQUET}')
    )
""")

con.execute(f"""
    CREATE OR REPLACE TABLE analytics.dim_commodity AS
    SELECT
        ROW_NUMBER() OVER (ORDER BY commodity) AS commodity_id,
        commodity
    FROM (
        SELECT DISTINCT commodity
        FROM read_parquet('{FINAL_PARQUET}')
    )
""")

con.execute(f"""
    CREATE OR REPLACE TABLE analytics.fact_prices AS
    SELECT
        p.id AS record_id,
        d.date_id,
        m.market_id,
        c.commodity_id,
        p.price,
        p.rainfall_mm
    FROM read_parquet('{FINAL_PARQUET}') p
    JOIN analytics.dim_date d
      ON d.date = CAST(p.date AS DATE)
    JOIN analytics.dim_market m
      ON m.market = p.market
    JOIN analytics.dim_commodity c
      ON c.commodity = p.commodity
""")

print("Completed star schema build.")
print(f"Database: {DB_PATH}")

result = con.execute("""
    SELECT
        COUNT(*) AS fact_rows,
        (SELECT COUNT(*) FROM analytics.dim_market) AS market_count,
        (SELECT COUNT(*) FROM analytics.dim_commodity) AS commodity_count,
        (SELECT COUNT(*) FROM analytics.dim_date) AS date_count
    FROM analytics.fact_prices
""").fetchone()

print(result)

queries = {
    "avg_price_by_commodity": """
        SELECT
            dc.commodity,
            AVG(fp.price) AS avg_price
        FROM analytics.fact_prices fp
        JOIN analytics.dim_commodity dc
          ON dc.commodity_id = fp.commodity_id
        GROUP BY dc.commodity
        ORDER BY avg_price DESC
    """,
    "avg_price_by_market": """
        SELECT
            dm.market,
            AVG(fp.price) AS avg_price
        FROM analytics.fact_prices fp
        JOIN analytics.dim_market dm
          ON dm.market_id = fp.market_id
        GROUP BY dm.market
        ORDER BY avg_price DESC
    """,
    "avg_rainfall_by_market": """
        SELECT
            dm.market,
            AVG(fp.rainfall_mm) AS avg_rainfall
        FROM analytics.fact_prices fp
        JOIN analytics.dim_market dm
          ON dm.market_id = fp.market_id
        GROUP BY dm.market
        ORDER BY avg_rainfall DESC
    """,
    "monthly_average_price": """
        SELECT
            dd.year,
            dd.month,
            AVG(fp.price) AS avg_price
        FROM analytics.fact_prices fp
        JOIN analytics.dim_date dd
          ON dd.date_id = fp.date_id
        GROUP BY dd.year, dd.month
        ORDER BY dd.year, dd.month
    """,
    "rainfall_price_correlation": """
        SELECT
            dc.commodity,
            CORR(fp.rainfall_mm, fp.price) AS rainfall_price_corr
        FROM analytics.fact_prices fp
        JOIN analytics.dim_commodity dc
          ON dc.commodity_id = fp.commodity_id
        GROUP BY dc.commodity
        ORDER BY rainfall_price_corr DESC
    """
}

for name, sql in queries.items():
    print(f"\n--- {name} ---")
    print(con.execute(sql).fetchdf())