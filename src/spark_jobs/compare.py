import time

import duckdb as db
from pyspark.sql import SparkSession, functions as F

BIG_PATH = "data/processed/prices_skewed.parquet"


def duckdb_job():
    t0 = time.perf_counter()
    result = db.sql(f'''
        SELECT market, AVG(price) AS mean_price, COUNT(*) AS n
        FROM '{BIG_PATH}'
        WHERE price IS NOT NULL
        GROUP BY market
        ORDER BY mean_price DESC
    ''').df()
    elapsed = time.perf_counter() - t0
    print("=== DuckDB ===")
    print(result)
    print(f"Time: {elapsed:.3f}s")
    return elapsed


def spark_job():
    spark = (
        SparkSession.builder
        .appName("DSC3103")
        .master("local[*]")
        .getOrCreate()
    )

    t0 = time.perf_counter()
    df = spark.read.parquet(BIG_PATH)

    summary = (
        df.filter(F.col("price").isNotNull())
        .groupBy("market")
        .agg(F.avg("price").alias("mean_price"), F.count("*").alias("n"))
        .orderBy(F.col("mean_price").desc())
    )

    print("=== Spark plan ===")
    summary.explain()

    print("=== Spark result ===")
    summary.show()
    elapsed = time.perf_counter() - t0
    print(f"Time: {elapsed:.3f}s")

    print("Partitions in input:", df.rdd.getNumPartitions())
    df.groupBy("market").count().orderBy(F.col("count").desc()).show()

    repartitioned = df.repartition(6, "market")
    print("Partitions after repartition:", repartitioned.rdd.getNumPartitions())
    repartitioned.groupBy(F.spark_partition_id().alias("pid")).count().show()

    spark.stop()
    return elapsed


def spark_cache_job(use_cache):
    spark = SparkSession.builder.master("local[*]").appName("cache").getOrCreate()
    df = spark.read.parquet(BIG_PATH).filter(F.col("commodity") == "Maize")

    if use_cache:
        df = df.cache()

    t0 = time.perf_counter()
    df.groupBy("market").agg(F.avg("price")).collect()  # action 1
    df.groupBy("market").agg(F.avg("rainfall_mm")).collect()  # action 2
    elapsed = time.perf_counter() - t0

    print(f"use_cache={use_cache}: {elapsed:.3f}s")
    spark.stop()
    return elapsed


if __name__ == "__main__":
    duckdb_job()
    spark_job()
    for use_cache in (False, True):
        spark_cache_job(use_cache)
