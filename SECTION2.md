# Database Schema Design for Course Enrollment Analytics

## Overview
This design describes how to model course and enrollment data across a lakehouse-style Bronze/Silver/Gold architecture, while also covering analytical schema choices and quality controls.

## Bronze / Raw Ingestion Layer
### Purpose
- Capture upstream source data as-is
- Standardize file formats and schema
- Preserve audit metadata and provenance
- Provide a single source of truth for the enterprise data platform

### Design
- Convert incoming files into Parquet or Delta format
- Add metadata columns:
  - `meta_year`
  - `meta_month`
  - `meta_day`
  - `meta_filename`
  - `meta_ingestion_date`
  - `meta_run_id`
- Partition by `meta_year`, `meta_month`, `meta_day`

### Transformations
- Normalize dates and timestamps from raw string formats
- Standardize column names and types
- Preserve raw source values as fallback fields when needed
- Apply file-level checks before writing Bronze

### Benefits
- Easier audit and backfill of specific ingestion dates
- Partition refreshes on accepted date partitions only
- Single source of truth for downstream validation and reconciliation

## Silver / Curated Validation Layer
### Purpose
- Validate and clean Bronze data
- Apply business rules and enforce schema
- Surface trusted, ready-for-analysis records

### Design
- Store as Delta or Parquet with schema enforcement
- Keep core facts and normalized reference fields
- Include validation state and error routing when records fail

### Transformations
- Run dynamic validation rules using Great Expectations or equivalent
- Deduplicate records by natural keys or `enrollment_id`
- Convert numeric fields (`amount`, `subsidy`, `credits_used`) to proper numeric types
- Standardize date columns to `DATE`/`TIMESTAMP`
- Normalize names, codes, currencies, booleans, and text values
- Apply referential integrity checks against dimension lookups

### Quality checks
- File-level
  - file exists
  - non-empty file
  - expected columns present
  - valid file format
  - duplicate file detection
- Record-level
  - malformed rows
  - invalid encoding
  - null primary identifiers
  - invalid dates
  - invalid numeric values
- Business-level
  - `course_id` exists in `dim_course`
  - `participant_id` exists in `dim_participant` or reference system
  - `enrollment_id` uniqueness

### Failure handling
- Critical validation failure: stop Silver load and raise pipeline error
- Non-critical issues: route invalid rows to exception tables for review
- Emit detailed validation reports and metrics

## Gold / Business Curated Layer
### Purpose
- Expose business-ready, analytics-optimized datasets
- Support BI, dashboards, reporting, and machine learning
- Provide stable semantic objects for downstream consumption

### Design options
- Star schema with fact and dimension tables
- Materialized views or Delta tables for commonly used business metrics
- Optional One Big Table (OBT) for denormalized reporting

### Transformations
- Join Silver records to dimensions
- Calculate derived metrics and KPIs
- Flatten and denormalize business entities for performance
- Create surrogate keys (`date_key`, `course_key`, `participant_key`)
- Add business-friendly fields such as `course_category`, `enrollment_status`, `revenue_amount`

### Gold-layer quality checks
- KPI reconciliation: compare report totals to source totals
- Aggregate consistency: verify SUMs across layers
- Dimension conformance: ensure consistent dimension values
- Freshness: verify latest partition or run timestamps
- Volume anomaly detection: detect spikes/drops in ingestion count

### Efficient analytical design
- Prefer star schema for BI:
  - Fact table: `fact_enrollments`
  - Dimensions: `dim_course`, `dim_participant`, `dim_date`, `dim_provider`
- Use materialized views for high-value aggregates
- Partition by date fields and cluster by business keys
- Store as Delta or columnar table for fast reads
- Build a semantic layer on top for business users

## Modeling Many-to-Many: Courses and Enrollments
### Transactional / OLTP perspective
- Use normalized 3NF design for write safety and consistency
- Example normalized tables:
  - `courses` (course metadata)
  - `participants` (learner metadata)
  - `enrollments` (transaction fact linking participants to courses)
- This design is update-safe and concurrency-safe in Postgres/RDS

### Analytical perspective
- Use a star schema for faster analytics:
  - `fact_enrollments` holds each enrollment event
  - `dim_course` holds course attributes
  - `dim_participant` holds learner attributes
  - `dim_date` holds calendar attributes
- This minimizes join complexity for BI and columnar engines

### One Big Table (OBT) alternative
- Flatten `fact_enrollments` with joined dimension attributes
- Good for dashboards and simple queries
- Very fast in cloud columnar warehouses, often cheaper compute

## Common Transformations Between Layers
### Deduplication
- Remove duplicate enrollments by natural key or `enrollment_id`
- Critical when ingesting CDC feeds or repeated loads

### Type standardization
- Convert strings to proper DATE/TIMESTAMP
- Normalize booleans, decimals, and currencies
- Example:
  - `"2026-05-29"` → `2026-05-29`

### Null handling
- Use `COALESCE` or route invalid records to exceptions
- Example: `COALESCE(status, 'UNKNOWN')`

### Reference integrity checks
- Ensure foreign keys exist before Gold load
- Example:
  - `course_id` exists in `dim_course`
  - `participant_id` exists in `dim_participant`

### Standardization
- Normalize case and spelling across source values
- Example:
  - `"Male", "male", "M"` → `"M"`
  - `"USA", "US", "United States"` → `"US"`

### Slowly Changing Dimensions
- Handle historical changes for dimensions such as course metadata
- Common patterns:
  - Type 1 overwrite for non-historical fields
  - Type 2 historical tracking for status changes

### Business rule enforcement
- Enforce rules like:
  - `course_capacity >= enrolled_students`
  - `enrollment_date` within valid registration window

## Data Quality Checks Summary
### Bronze
- file checksum validation
- file shape and format
- missing file / duplicate file detection

### Silver
- completeness and null percentage checks
- uniqueness checks for active enrollments
- referential integrity and lookup validation
- validity checks for status and numeric ranges
- freshness checks on ingestion timestamps
- volume anomaly detection for sudden spikes or drops

### Gold
- KPI reconciliation with trusted source totals
- aggregate consistency across datasets
- dimension conformance across reports
- semantic correctness and business logic validation

## Gold Layer Architecture for Analytics
### Goals
- business-friendly data objects
- fast query performance
- governed and stable datasets
- optimized for BI and analytics

### Recommended layout
- `fact_enrollments`
- `dim_course`
- `dim_participant`
- `dim_date`
- `dim_provider`
- `dim_location`

### Performance optimizations
- materialized views for frequent aggregates
- partition by date and optional business keys
- cluster or sort on join keys
- use columnar storage (Delta/Parquet)
- build semantic models for business consumption

## Conclusion
This design balances raw data capture, trusted validation, and analytics-ready business consumption. The layered approach allows focused quality checks, easier auditing and backfill, and efficient query performance in the Gold layer while preserving flexibility for both normalized transactional and denormalized analytical use cases.
