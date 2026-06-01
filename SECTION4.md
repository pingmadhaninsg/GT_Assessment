# Solution Design — Skillset Inference Pipeline (Top-to-bottom)

## Overview
- Goal: Build a scalable pipeline to predict skillsets from course descriptions at large scale (200M records). Start with data preparation, support an initial full load and daily incremental processing, and design inference to be batch-first and asynchronous.

## Problem Summary
- Current per-record synchronous inference is too slow and expensive for 200M rows. We will remove per-row endpoint preprocessing and per-row synchronous calls by pre-processing and batching, and by using an async/queued inference pattern or Batch Transform.

**Top-to-bottom approach**
- Prepare & model-ready the data (schema, SCD2 handling, partitioning).
- Ingest and transform: full-load then incremental loads using watermarking.
- Preprocess text (tokenization / embedding) offline and store in `token_embedded_description`.
- Batch inference: choose between S3-based Batch Transform, async endpoints, or a worker fleet.
- Result collection: async transaction IDs, status tracking, result retrieval and merge back into downstream stores.
- Monitoring, retries, and model optimization.

## Data preparation (first phase)

**Source schema**
- `course_details` columns: ID, courses, description, category, sub_category, is_active, start_date, end_date, price, grand_code, created_at, updated_at, effective_start, effective_end, is_current, token_embedded_description
- Note: the last 3 columns (`effective_start`, `effective_end`, `is_current`) are used for SCD2 versioning.

**Partitioning & storage**
- Partition tables by `category` and `sub_category` to enable partition-pruned processing, or create using the chosen "liquid cluster" approach if preferred.
- Store base data in a columnar format (Parquet) for efficient reads and for use with SageMaker Batch Transform or job workers.

**SCD2 handling**
- Maintain SCD2 using `effective_start`, `effective_end`, `is_current`.
- On ingest, new or changed rows create a new SCD2 version and set previous `is_current=false` with `effective_end` populated.

## Ingestion & ETL: full + incremental

- Full load (first run): export the entire `course_details` table into partitioned Parquet/JSONL files in S3, including the preprocessed token/embedding column.
- Incremental loads: use `updated_at` as the watermark column. On daily runs, select rows where `updated_at > last_watermark` and process only those partitions or record batches.
- Maintain a small metadata store recording `last_watermark` per category/sub_category (or global) to support parallel incremental workers.

## Text preprocessing & tokenization

- Requirement: The AI/ML model does not accept raw text; tokenization or embedding must be done before calling the model.
- Preprocess pipeline:
   - Normalize and clean `description` (lowercase, remove control characters, normalize whitespace).
   - Tokenize and/or compute embeddings using the chosen tokenizer/encoder offline.
   - Persist results into `token_embedded_description` (store token ids or a serialized embedding vector). Prefer a compact binary or base64-encoded representation for vectors.

- Rationale: Storing tokenized/embedded text avoids repeated per-record preprocessing at the model endpoint and enables high-throughput batch inference.

## Batch processing strategy (design choices)

- Two primary batching strategies to decide during dry-run:
   1. Partition-based batching: process by `category`/`sub_category` partitions. Advantages: natural data locality, easier incremental targeting, smaller result files per partition. Best when categories are relatively balanced.
   2. Size-based batching: process fixed-size batches (e.g., 10k records per batch). Advantages: predictable memory and compute per job, independent of partition skew.
- Recommendation: run a dry-run benchmark for both strategies and choose the one with the best throughput/cost tradeoff for your data distribution. Start with partition-based when categories are well distributed; otherwise use size-based batching with parallel partition assignment.

## Inference: async & scalable pattern

- Do not expect per-batch low-latency transactional responses. Design for async processing with acknowledgement and later retrieval of results.

- Flow (client -> inference system):
   1. Client (or orchestrator) submits a batch job (S3 input path or list of record IDs) to the inference API.
   2. API returns a unique `transaction_id` and initial status `IN_PROGRESS` (or `QUEUED`). This call is fast and non-blocking.
   3. Worker/endpoint processes the input batch (Batch Transform job, async endpoint, or worker fleet). When complete, results are written to S3 and the job status updates to `SUCCESS` or `FAILED` in the job metadata store.
   4. Client polls or subscribes to notifications (SNS/SQS or webhook) to detect status change. When `SUCCESS`, client fetches results using the `transaction_id`.

- Implementation options:
   - SageMaker Batch Transform: simplest for large offline runs; input/output via S3; jobs are naturally batch-oriented.
   - SageMaker Asynchronous Inference: use for decoupled endpoints that accept S3 inputs and output S3 results with job IDs.
   - Worker fleet (ECS/EKS/EC2): for custom logic or when you need fine-grained control (e.g., GPU pools, custom batching logic, callbacks).

## Result handling & downstream merge

- Results should be written partition-wise to S3 and also persisted to a results table keyed by source `ID` plus a `transaction_id` and `inference_timestamp`.
- A final merge/UPSERT process reads the results and updates the destination store. For SCD2-aware tables, create new versions on change and set `is_current` flags accordingly.

## Operational considerations

- Retries & failures: implement idempotent retry semantics for batch submission. Store job input metadata so a failed job can be safely retried.
- Monitoring: track job queue length, per-job throughput, error rates, model latency distribution, and instance utilization.
- Cost optimization: prefer spot instances for ephemeral worker fleets; benchmark GPU vs CPU for model throughput per dollar.
- Security & privacy: encrypt data at rest and in transit; control access to S3 buckets and inference APIs.

## Model optimization

- Batch multiple tokenized records into a single model inference call where possible to leverage vectorized execution on GPUs.

## Dry-run & benchmarking

- Dry-run tasks:
   - Measure throughput for several batch sizes (1k, 5k, 10k) and for partition-based batches.
   - Evaluate average processing time per batch on chosen instance types.
   - Use results to choose partitioning vs fixed-size batching and estimate instance-days required.

## Daily incremental run

- Use `updated_at` as the watermark to select changed rows since the last successful run. Run daily to keep skillset predictions up to date.
- Optionally maintain per-partition watermarks for faster parallel incremental processing.

## Next steps (practical)

- Prepare an ETL job that:
   - Exports partitioned Parquet to S3 for full load.
   - Runs the offline tokenizer/embedding and writes `token_embedded_description`.
- Build a small orchestrator that:
   - Submits batch inference jobs and returns `transaction_id`.
   - Polls job status or receives notifications and retrieves results on `SUCCESS`.
- Run the dry-run benchmark and decide on partition vs fixed-size batching and on instance types.

---

File updated to include a data-first pipeline, SCD2 handling, async inference pattern, and clear dry-run steps.