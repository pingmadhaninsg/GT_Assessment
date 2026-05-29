#!/usr/bin/env python3
"""
Section 1: Ingestion Pipeline - Standalone Runner
Reads data/enrolments.csv, cleans it, and loads into data/courses.db
"""

from pathlib import Path
import sqlite3
import pandas as pd

from gt_assessment.ingest import (
    ingest_enrolments,
    load_and_clean_enrolments,
    create_database,
)


def main():
    print("=" * 70)
    print("GovTech Assessment - Section 1: Data Ingestion Pipeline")
    print("=" * 70)

    # Setup paths
    db_path = Path("data/courses.db")
    source_csv = Path("data/enrolments.csv")

    # Verify source file exists
    if not source_csv.exists():
        print(f"ERROR: Source file not found: {source_csv.resolve()}")
        return 1

    print(f"\nSource CSV: {source_csv.resolve()}")
    print(f"Target DB:  {db_path.resolve()}\n")

    # Step 1: Create database and schema
    print("[1/4] Creating database and schema...")
    conn = create_database(db_path)
    conn.close()
    print("✓ Database and schema created\n")

    # Step 2: Load and clean data
    print("[2/4] Loading and cleaning enrollment data...")
    df_clean = load_and_clean_enrolments(source_csv)
    print(f"✓ Rows after cleaning: {len(df_clean)}\n")

    # Step 3: Ingest into SQLite
    print("[3/4] Ingesting cleaned data into SQLite...")
    db_path = ingest_enrolments(db_path, source_csv)
    print(f"✓ Data ingested successfully\n")

    # Step 4: Validate ingestion
    print("[4/4] Validating ingestion results...")
    conn = sqlite3.connect(db_path)
    row_count = pd.read_sql_query("SELECT COUNT(*) AS row_count FROM enrolments", conn)
    preview = pd.read_sql_query(
        "SELECT * FROM enrolments ORDER BY enrollment_id LIMIT 5", conn
    )
    conn.close()

    print(f"\n{row_count.to_string(index=False)}\n")
    print("Sample records (first 5):")
    print(preview.to_string(index=False))

    print("\n" + "=" * 70)
    print("✓ Section 1 Ingestion Pipeline Completed Successfully")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    exit(main())
