from __future__ import annotations

from pathlib import Path
import sqlite3
import pandas as pd
from dateutil import parser as date_parser

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
DEFAULT_DB_PATH = DATA_DIR / "courses.db"
DEFAULT_ENROLMENTS_CSV = DATA_DIR / "enrolments.csv"

COURSES_SCHEMA = """
CREATE TABLE IF NOT EXISTS courses (
    course_id INTEGER PRIMARY KEY,
    name TEXT,
    description TEXT,
    prerequisites TEXT
);
"""

ENROLMENTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS enrollments (
    enrollment_id INTEGER PRIMARY KEY,
    participant_id TEXT NOT NULL,
    participant_name TEXT NOT NULL,
    course_id INTEGER NOT NULL,
    course_date DATE,
    amount REAL,
    subsidy REAL,
    credits_used REAL
);
"""


def create_database(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)

    cursor = conn.cursor()
    # Ensure only approved/new tables remain. Drop legacy/old tables.
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing = {row[0] for row in cursor.fetchall()}
    allowed = {"courses", "enrollments"}
    to_drop = existing - allowed
    for tbl in to_drop:
        cursor.execute(f"DROP TABLE IF EXISTS {tbl}")
    conn.commit()
    cursor.execute(COURSES_SCHEMA)
    cursor.execute(ENROLMENTS_SCHEMA)
    conn.commit()
    return conn


def load_and_clean_enrolments(csv_path: Path | str = DEFAULT_ENROLMENTS_CSV) -> pd.DataFrame:
    csv_path = Path(csv_path)
    df = pd.read_csv(csv_path)

    # Robust parsing: try common explicit formats first, then fall back to dateutil
    from datetime import datetime

    raw_dates = df['course_date'].astype(str).fillna("")

    formats = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d %b %Y",
        "%d %B %Y",
        "%d %b %y",
        "%d %B %y",
    ]

    def _parse_str(s: str):
        s = s.strip()
        if not s or s.lower() == 'nan':
            return pd.NaT
        for fmt in formats:
            try:
                return pd.to_datetime(datetime.strptime(s, fmt))
            except Exception:
                continue
        try:
            return pd.to_datetime(date_parser.parse(s, dayfirst=True, fuzzy=True))
        except Exception:
            return pd.NaT

    df['course_date'] = raw_dates.map(_parse_str)
    df['course_date'] = df['course_date'].dt.strftime('%Y-%m-%d')

    numeric_columns = ['amount', 'subsidy', 'credits_used']
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors='coerce')

    df = df.dropna(subset=['enrollment_id', 'participant_id', 'course_id'])
    df['enrollment_id'] = df['enrollment_id'].astype(int)
    df['course_id'] = df['course_id'].astype(int)

    return df


def ingest_enrolments(
    db_path: Path | str = DEFAULT_DB_PATH,
    csv_path: Path | str = DEFAULT_ENROLMENTS_CSV,
) -> Path:
    df = load_and_clean_enrolments(csv_path)
    conn = create_database(db_path)
    df.to_sql('enrollments', conn, if_exists='replace', index=False)
    conn.commit()
    conn.close()
    return Path(db_path)


def validate_enrolment_load(db_path: Path | str = DEFAULT_DB_PATH) -> pd.DataFrame:
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query('SELECT * FROM enrollments LIMIT 20', conn)
    conn.close()
    return df
