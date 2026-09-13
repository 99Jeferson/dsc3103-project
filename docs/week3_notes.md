# Week 3 Notes

For this project, I chose ETL rather than ELT. The sales dataset is the primary operational source, and the rainfall table is a small contextual augmentation that joins on market and date. It is more efficient to validate and clean the raw sales table before loading it into the target store so bad rows are removed once, and the resulting curated fact table is easier to merge with weather context without carrying corrupted records forward. This keeps the store cleaner and makes downstream analysis more trustworthy.

I used overwrite semantics for the processed output. Each run of the pipeline rebuilds the cleaned and merged parquet files from the source inputs, which guarantees the output is current and prevents duplicate rows from being introduced by repeated execution. This is a simple and reliable choice for a lab project with a small, deterministic dataset.
