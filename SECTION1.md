# Section 1: Data Ingestion Pipeline

## Overview
This section implements the data ingestion pipeline for the GovTech assessment. It reads enrollment data from `data/enrolments.csv`, applies data cleaning and validation, and loads the cleaned data into the SQLite database `data/courses.db`.

### What it does:
- Parses the enrollment CSV with multiple date formats
- Normalizes dates to ISO 8601 format
- Converts numeric columns (amount, subsidy, credits_used)
- Validates and removes incomplete records
- Loads cleaned data into the `enrolments` table in SQLite

---

## Prerequisites

Before running Section 1, ensure you have:
1. Python 3.11 or higher
2. `uv` package manager installed ([uv docs](https://docs.astral.sh/uv/))
3. The project repository cloned locally
4. The source file `data/enrolments.csv` present in the repository

### Check prerequisites:
```powershell
# Check Python version
python --version

# Check uv installation
uv --version
```

---

## Step-by-Step Guide to Run Section 1

### Step 1: Navigate to project directory
```powershell
cd c:\projects\GT_Assessment
```

### Step 2: Create isolated virtual environment
```powershell
# Create a virtual environment using uv
uv venv

# Activate the environment (Windows PowerShell)
.venv\Scripts\Activate.ps1
```

If you use Command Prompt instead:
```cmd
.venv\Scripts\activate.bat
```

### Step 3: Install project dependencies
```powershell
# Install dependencies from pyproject.toml
uv pip install -e .
```

This installs:
- `pandas` — for CSV and data manipulation
- `sqlite-utils` — for SQLite operations
- `jupyter` — for notebook execution
- `pytest` and `black` — dev dependencies

### Step 4: Run the ingestion pipeline

#### Option A: Run the Jupyter notebook (interactive)
```powershell
jupyter notebook section1_ingestion.ipynb
```
- Opens the notebook in your browser
- Run cells sequentially to see output at each stage
- Recommended for exploration and validation

#### Option B: Run as a Python script (non-interactive)
```powershell
python section1_run.py
```
- Runs the entire pipeline end-to-end
- Prints summary output to terminal
- Best for automation and CI/CD

#### Option C: Run with uv directly (no manual activation needed)
```powershell
uv run section1_run.py
```
- uv automatically creates and manages the environment
- Simplest one-line approach

### Step 5: Verify ingestion success

After running, check the output for:
```
Database created/updated at: <path>/data/courses.db
Rows after cleaning: <N>
Enrolments data loaded to: <path>/data/courses.db
```

Then verify the database contents:
```powershell
# Optional: Query the database to confirm data
python -c "import sqlite3; conn = sqlite3.connect('data/courses.db'); print(conn.execute('SELECT COUNT(*) FROM enrolments').fetchone())"
```

---

## File Structure

```
GT_Assessment/
├── section1_ingestion.ipynb      # Jupyter notebook (interactive)
├── section1_run.py               # Python script (CLI)
├── SECTION1.md                   # This guide
├── pyproject.toml                # Poetry configuration
├── data/
│   ├── enrolments.csv            # Source data
│   └── courses.db                # Target SQLite database
└── gt_assessment/
    ├── __init__.py
    └── ingest.py                 # Ingestion helper functions
```

---

## Data Transformations

### Input (enrolments.csv)
- **enrollment_id**: unique identifier
- **participant_id**: learner ID
- **participant_name**: learner name (may have inconsistencies)
- **course_id**: course identifier
- **course_date**: multiple date formats (DD/MM/YYYY, YYYY-MM-DD, DD Mon YYYY)
- **amount**: float (course fee)
- **subsidy**: float (government subsidy)
- **credits_used**: float (learning credits consumed)

### Processing
1. **Date normalization**: Parse multiple formats using `pd.to_datetime(..., dayfirst=True)`
2. **Numeric conversion**: Convert amount, subsidy, credits_used to REAL (float)
3. **Validation**: Drop rows with missing enrollment_id, participant_id, or course_id
4. **Type casting**: Ensure enrollment_id and course_id are integers

### Output (SQLite enrolments table)
```sql
CREATE TABLE enrolments (
    enrollment_id INTEGER PRIMARY KEY,
    participant_id TEXT NOT NULL,
    participant_name TEXT NOT NULL,
    course_id INTEGER NOT NULL,
    course_date DATE,
    amount REAL,
    subsidy REAL,
    credits_used REAL
);
```

---

## Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'gt_assessment'`
**Solution**: Ensure you've run `uv pip install -e .` in the activated virtual environment.

### Issue: `FileNotFoundError: data/enrolments.csv`
**Solution**: Verify the CSV file exists in `data/enrolments.csv` and that you're running from the project root.

### Issue: `uv` command not found
**Solution**: Install uv globally:
```powershell
pip install uv
# or on macOS/Linux
brew install uv
```

### Issue: `.venv\Scripts\Activate.ps1` execution policy error
**Solution**: Update PowerShell execution policy:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue: Jupyter notebook kernel error
**Solution**: Ensure jupyter is installed in the venv:
```powershell
uv pip install jupyter
jupyter kernel install --user --name python3 --display-name "Python 3"
```

---

## Next Steps

After completing Section 1 ingestion:
1. **Section 2**: Design Bronze/Silver/Gold data architecture (see `SECTION2.md`)
2. **Section 3**: Write SQL to detect prerequisite violations (see `SECTION3.md`)
3. **Section 4**: Optimize SageMaker pipeline for 200M records (see `SECTION4.md`)

---

## Additional Resources

- [Pandas documentation](https://pandas.pydata.org/)
- [SQLite3 Python module](https://docs.python.org/3/library/sqlite3.html)
- [uv package manager](https://docs.astral.sh/uv/)
- [Jupyter Notebook](https://jupyter.org/)
