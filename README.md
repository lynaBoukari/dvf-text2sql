# dvf-text2sql

Fine-tuning a small language model to generate SQL over a real star schema,
and evaluating it by executing what it produces.

**Status: in progress, October 2026.**

## Why this setup

Most text-to-SQL work is evaluated on string similarity against a reference
query. That rewards queries that look right. Here the metric is execution
accuracy: the generated query is run against the warehouse and its result set
is compared to the expected one. A query that looks wrong but returns the
right rows passes; a query that looks right and returns nothing does not.

## The warehouse

The target is the star schema built in
[dvf-price-api](https://github.com/lynaBoukari/dvf-price-api): French property
transaction records (DVF), modelled in BigQuery with dbt.

- `fct_ventes` — one row per transaction, 61,000 rows, declared grain
- `dim_commune` — 524 municipalities, surrogate keys
- `dim_date` — 1,096 days, generated calendar

Referential integrity is enforced by data tests at each build, so the schema
the model learns against is known to be consistent.

## Plan

1. **Data.** Generate question / SQL pairs over this schema, covering joins,
   aggregation, window functions and date filters. Validate every pair by
   executing it; discard anything that errors or returns an empty result.
2. **Training.** Supervised fine-tuning of a compact model (Qwen2.5-0.5B)
   with `peft` (LoRA) and `trl`, single GPU.
3. **Evaluation.** Execution accuracy on a held-out set, against the base
   model as a baseline. Failures classified by type: hallucinated column,
   wrong grain, missing join, invalid syntax.
4. **Write-up.** What transferred, what did not, and where the model breaks.

## Results

Not yet. This section will contain the numbers, including the ones that
disappoint.
