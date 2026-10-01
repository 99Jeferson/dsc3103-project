"""Build and query the analytical star schema for DSC3103 Lab 4."""

import os
import time #timer for measuring performance of queries
from pathlib import Path

import duckdb as db
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW_JOINED_PATH = ROOT / "data" / "processed" / "prices_with_rainfall.parquet"
DB_PATH = ROOT / "data" / "processed" / "analytics.duckdb"

REQUIRED_COLUMNS = {
    "id",
    "date",
    "market",
    "commodity",
    "price",
    "rainfall_mm",
}


def _check_input_file():
    if not RAW_JOINED_PATH.exists():
        raise FileNotFoundError(
            f"Assignment input not found: {RAW_JOINED_PATH}. "
            "Place prices_with_rainfall.parquet in data/processed/."
        )

    columns = set(pd.read_parquet(RAW_JOINED_PATH).columns)
    missing = REQUIRED_COLUMNS - columns
    if missing:
        raise ValueError(f"Input parquet is missing required columns: {sorted(missing)}")


def baseline_query():
    """Run the supplied flat-Parquet baseline for Maize."""
    _check_input_file()
    input_path = RAW_JOINED_PATH.as_posix().replace("'", "''")

    t0 = time.perf_counter()
    result = db.sql(f"""
        SELECT market, AVG(price) AS mean_price
        FROM '{input_path}'
        WHERE commodity = 'Maize'
        GROUP BY market
        ORDER BY mean_price DESC
    """).df()
    elapsed = time.perf_counter() - t0

    print("=== Step 1: Baseline query (flat Parquet; Maize) ===")
    print(result)
    print(f"Time: {elapsed:.4f}s | File size: {os.path.getsize(RAW_JOINED_PATH)} bytes")
    return elapsed


def build_star_schema():
    """Build the two dimensions and observation fact table in DuckDB."""
    _check_input_file()
    df = pd.read_parquet(RAW_JOINED_PATH)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = db.connect(str(DB_PATH))

    try:
        dim_market = (
            df[["market"]]
            .drop_duplicates()
            .sort_values("market")
            .reset_index(drop=True)
        )
        dim_market.insert(0, "market_id", range(len(dim_market)))
        dim_market = dim_market.rename(columns={"market": "market_name"})

        dim_commodity = (
            df[["commodity"]]
            .drop_duplicates()
            .sort_values("commodity")
            .reset_index(drop=True)
        )
        dim_commodity.insert(0, "commodity_id", range(len(dim_commodity)))
        dim_commodity = dim_commodity.rename(columns={"commodity": "commodity_name"})

        fact = df.merge(
            dim_market,
            left_on="market",
            right_on="market_name",
            how="left",
            validate="many_to_one",
        ).merge(
            dim_commodity,
            left_on="commodity",
            right_on="commodity_name",
            how="left",
            validate="many_to_one",
        )
        fact = fact[
            ["id", "date", "market_id", "commodity_id", "price", "rainfall_mm"]
        ]

        con.register("dim_market_frame", dim_market)
        con.register("dim_commodity_frame", dim_commodity)
        con.register("fact_frame", fact)
        con.execute(
            "CREATE OR REPLACE TABLE dim_market AS "
            "SELECT market_id, market_name FROM dim_market_frame"
        )
        con.execute(
            "CREATE OR REPLACE TABLE dim_commodity AS "
            "SELECT commodity_id, commodity_name FROM dim_commodity_frame"
        )
        con.execute(
            "CREATE OR REPLACE TABLE fact_price_observation AS "
            "SELECT id, date, market_id, commodity_id, price, rainfall_mm "
            "FROM fact_frame"
        )

        fact_rows = con.execute(
            "SELECT COUNT(*) FROM fact_price_observation"
        ).fetchone()[0]
        if fact_rows != len(df):
            raise RuntimeError(
                f"Fact table has {fact_rows} rows, expected {len(df)} input observations."
            )

        print("=== Step 3: Star schema built ===")
        print("Database:", DB_PATH)
        print("Fact table row count:", fact_rows)
        print("Market dimension rows:", len(dim_market))
        print("Commodity dimension rows:", len(dim_commodity))
    finally:
        con.close()


def run_analytical_queries():
    """Run five analytical queries, each joining the fact to a dimension."""
    con = db.connect(str(DB_PATH), read_only=True)
    queries = [
        (
            "Query 1: Average price by market",
            """
            SELECT dm.market_name, AVG(f.price) AS mean_price
            FROM fact_price_observation f
            JOIN dim_market dm ON f.market_id = dm.market_id
            GROUP BY dm.market_name
            ORDER BY mean_price DESC
            """,
        ),
        (
            "Query 2: Observation count by commodity",
            """
            SELECT dc.commodity_name, COUNT(*) AS n_observations
            FROM fact_price_observation f
            JOIN dim_commodity dc ON f.commodity_id = dc.commodity_id
            GROUP BY dc.commodity_name
            ORDER BY n_observations DESC
            """,
        ),
        (
            "Query 3: Average price by market and commodity",
            """
            SELECT dm.market_name, dc.commodity_name,
                   AVG(f.price) AS mean_price
            FROM fact_price_observation f
            JOIN dim_market dm ON f.market_id = dm.market_id
            JOIN dim_commodity dc ON f.commodity_id = dc.commodity_id
            GROUP BY dm.market_name, dc.commodity_name
            ORDER BY dc.commodity_name, mean_price DESC
            """,
        ),
        (
            "Query 4: Average rainfall by market",
            """
            SELECT dm.market_name, AVG(f.rainfall_mm) AS mean_rainfall_mm
            FROM fact_price_observation f
            JOIN dim_market dm ON f.market_id = dm.market_id
            GROUP BY dm.market_name
            ORDER BY mean_rainfall_mm DESC NULLS LAST
            """,
        ),
        (
            "Query 5: Highest-mean-price market for each commodity",
            """
            WITH market_means AS (
                SELECT dc.commodity_name, dm.market_name,
                       AVG(f.price) AS mean_price
                FROM fact_price_observation f
                JOIN dim_market dm ON f.market_id = dm.market_id
                JOIN dim_commodity dc ON f.commodity_id = dc.commodity_id
                GROUP BY dc.commodity_name, dm.market_name
            )
            SELECT commodity_name, market_name, mean_price
            FROM market_means
            QUALIFY ROW_NUMBER() OVER (
                PARTITION BY commodity_name ORDER BY mean_price DESC, market_name
            ) = 1
            ORDER BY commodity_name
            """,
        ),
    ]

    try:
        for title, sql in queries:
            print(f"=== {title} ===")
            print(con.sql(sql).df().to_string(index=False))
    finally:
        con.close()


def compare_performance():
    """Measure the same average-price-by-market query on Parquet and DuckDB."""
    _check_input_file()
    input_path = RAW_JOINED_PATH.as_posix().replace("'", "''")

    t0 = time.perf_counter()
    db.sql(f"""
        SELECT market, AVG(price) AS mean_price
        FROM '{input_path}'
        GROUP BY market
    """).df()
    flat_time = time.perf_counter() - t0

    con = db.connect(str(DB_PATH), read_only=True)
    try:
        t0 = time.perf_counter()
        con.sql("""
            SELECT dm.market_name, AVG(f.price) AS mean_price
            FROM fact_price_observation f
            JOIN dim_market dm ON f.market_id = dm.market_id
            GROUP BY dm.market_name
        """).df()
        star_time = time.perf_counter() - t0
    finally:
        con.close()

    print("=== Step 5: Performance comparison ===")
    print(f"Flat Parquet query time:  {flat_time:.4f}s")
    print(f"Star schema query time:   {star_time:.4f}s")
    return flat_time, star_time


def main():
    baseline_query()
    build_star_schema()
    run_analytical_queries()
    compare_performance()


if __name__ == "__main__":
    main()
