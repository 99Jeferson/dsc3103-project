# Lab 06 notes

## Step 1 — skewed dataset

I generated the skewed 5,000,000-row dataset in `src/scale/skewed_data.py`.

Question: What share of the rows belongs to Owino now, and why did we do this on purpose?

Answer: About 70% of the rows (`0.700`) belong to Owino. We did this on purpose to create a highly skewed dataset so Spark has to shuffle and redistribute records by market. That makes the workload behave more like a real-world data-skew case, where one key dominates and one partition/worker can become a bottleneck.

## Step 3 — DuckDB vs Spark

The benchmark numbers from the lab run were:

- DuckDB: 2.931 s
- Spark local: 22.495 s

So DuckDB was faster on this local 5M-row workload, by roughly 7.7x (about 22.5 / 2.9 ≈ 7.7).

Question: Nothing happened when `summary = ...` was executed. Which line actually triggered the work, and why?

Answer: The work was triggered by an action such as `summary.show()` or `summary.collect()`. The earlier `summary = ...` expression is a lazy transformation: it builds a logical Spark DataFrame plan but does not actually execute it. The real execution happens only when an action requests the data, because Spark evaluates the DAG and performs the transformation pipeline.

## Step 4 — reading the Spark plan

The `Exchange` appears because of the shuffle required by the aggregation and sorting. The relevant operations are:

- `groupBy("market")` is a wide transformation, because rows with the same key must be combined on different partitions.
- `orderBy(...)` also requires a shuffle/sort across partitions.
- `filter(...)` is narrow, because it can be applied row-by-row without moving data between partitions.

The plan line that shows Spark only reading the columns it needs is the `FileScan parquet ... ReadSchema: struct<market:string,price:bigint>` line. It reads only `market` and `price`, not the full row.

## Step 5 — partitions and skew

After repartitioning by `market` into 6 partitions, the counts were extremely uneven:

- partition 2: 4,399,624 rows
- partition 3: 600,376 rows
- other partitions: effectively empty / not used for the skewed key distribution

This shows the dataset is heavily concentrated in a few partitions. In a real cluster, the worker holding the largest partition would finish last. That creates a straggler, and the whole job waits for the slowest task, making total completion time much longer than the average task time.

## Step 6 — cache or not?

Measured times:

- Spark without cache (2 actions): 4.183 s
- Spark with cache (2 actions): 9.767 s

Caching did not help in this case; it was slower. This is because the dataset was small enough that the repeated operations were already cheap, and the overhead of caching and memory management outweighed the benefit. Caching would only be useful when a dataset is reused for multiple expensive actions. If only one action is run, caching usually adds overhead and produces little or no benefit.

## Step 7 — decision memo

### Measured numbers table

| Job | Time (s) |
|---|---:|
| DuckDB, 5M rows | 2.931 |
| Spark local, 5M rows | 22.495 |
| Spark without cache (2 actions) | 4.183 |
| Spark with cache (2 actions) | 9.767 |

### Recommendation memo

A. Weekly report on 500,000 rows stored in one Parquet file.

Use DuckDB. The benchmark shows a single 5M-row aggregate on an unclustered local file finished in about 2.9 seconds, while Spark took about 22.5 seconds for the same job. For a small-to-medium single-file analytical report, DuckDB is much faster and simpler.

B. 2 TB of mobile-money transaction logs that must be processed nightly, and the job must survive machine failures.

Use Spark. The dataset is large, distributed, and fault-tolerant execution matters. Spark can split work across many machines, handle shuffle-heavy aggregations, and recover from failed workers through its execution model. DuckDB is excellent for a single machine but not for distributed resilient ETL at this scale.

C. A 3 GB file on a lecturer's laptop with 16 GB of RAM.

Use DuckDB (or a local single-node engine). For a 3 GB file on a laptop, DuckDB is efficient and much faster than Spark for this kind of one-machine analytics. Spark may be overkill because the overhead of starting a distributed engine and managing cluster state is not justified for a modest local dataset.

## Conclusion

For single-machine analytical work on reasonably sized files, DuckDB is the better fit. Spark becomes valuable when the dataset is large enough to require distribution, many transformations are chained, and fault tolerance across machines is required.
