# Lab 4 — Analytics notes

## Schema design trade-off

I traded the simplicity of querying one flat table for the added joins and storage of dimension tables, gaining reusable market and commodity labels plus a clearer structure for analytical queries.

The fact table, `fact_price_observation`, stores one row per observation with `market_id` and `commodity_id` keys. `dim_market` and `dim_commodity` hold the corresponding labels. The fact table contains 889 rows, while the market and commodity dimensions contain 5 and 2 rows respectively.

## Highest-mean-price market by commodity

| Commodity | Market | Mean price |
| --- | --- | ---: |
| Beans | Nakasero | 2741.82 |
| Maize | Bwaise | 3103.85 |

## Step 5 — Performance observation

In the latest recorded run, the flat Parquet query took **0.0074 seconds**, while the equivalent query against the DuckDB star schema took **0.0057 seconds**. The star-schema measurement was about 0.0017 seconds lower in this run, but the absolute difference is small. This is not strong evidence that either design is inherently faster. The input is only 889 rows, and one-off timings at this scale are sensitive to startup, filesystem caching, and other machine activity. Repeated runs and a much larger dataset would be needed for a dependable performance comparison.

## Architecture decision: Is the star schema worth it at this data size?

For this dataset, the star schema is useful mainly for organization and learning, rather than for a measurable speed improvement. In the latest run, the average-price-by-market query took 0.0074 seconds against flat Parquet and 0.0057 seconds against the DuckDB fact table joined to the market dimension. The star-schema query was 0.0017 seconds faster in that run, but a single measurement over 889 observations is too small to establish a general performance advantage and is sensitive to startup, caching, and machine activity. The flat file is simpler to distribute and inspect, and it avoids maintaining a database and dimension keys. By contrast, the star schema separates observation facts from market and commodity labels, gives the fact table compact integer keys, and provides a consistent place to extend or enrich those descriptive categories as the project grows. Analytical queries also make their relationships explicit through joins. I would keep the star schema for repeated analysis or if more dimensions and larger data volumes are introduced, but I would not justify its added complexity here on query speed alone. For this lab’s current scale, retaining the Parquet source alongside the DuckDB analytical model is a practical balance.
