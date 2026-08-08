"""
setup_eda.py — Phase 1 #3 Pre-flight: validate everything before running the EDA notebook.

Checks:
  1. All required Python packages are importable
  2. MySQL DB is reachable and has the expected tables + row counts
  3. ipl_batting_stats and ipl_bowling_stats exist (ipl_transform.py was run)
  4. Registers a Jupyter kernel so run_eda.py can execute the notebook

Usage:
    python setup_eda.py
Then run the notebook:
    python run_eda.py
"""

import sys
import subprocess
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Colour helpers (no extra deps) ───────────────────────────────────────────
OK   = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
WARN = "\033[93m⚠\033[0m"
SEP  = "─" * 55

def ok(msg):   print(f"  {OK}  {msg}")
def fail(msg): print(f"  {FAIL}  {msg}"); return False
def warn(msg): print(f"  {WARN}  {msg}")

# ── 1. Package check ──────────────────────────────────────────────────────────
def check_packages() -> bool:
    print(f"\n{SEP}")
    print("1. Python package availability")
    print(SEP)

    required = {
        "pandas":           "pandas",
        "numpy":            "numpy",
        "matplotlib":       "matplotlib",
        "seaborn":          "seaborn",
        "sqlalchemy":       "sqlalchemy",
        "mysql.connector":  "mysql-connector-python",
        "nbformat":         "nbformat",
        "nbconvert":        "nbconvert",
        "dotenv":           "python-dotenv",
    }

    missing = []
    for module, pkg in required.items():
        try:
            __import__(module)
            ok(f"{module}")
        except ImportError:
            fail(f"{module}  →  run: pip install \"{pkg}>=0\"")
            missing.append(pkg)

    # Check ipykernel separately — needed only for run_eda.py
    try:
        __import__("ipykernel")
        ok("ipykernel  (Jupyter kernel)")
    except ImportError:
        warn("ipykernel not found — installing now …")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "ipykernel", "--quiet"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            ok("ipykernel installed")
        else:
            missing.append("ipykernel")
            fail("ipykernel install failed — run: pip install ipykernel")

    if missing:
        print(f"\n  Install missing packages:")
        print(f"  pip install -r requirements.txt")
        return False
    return True


# ── 2. Jupyter kernel registration ───────────────────────────────────────────
def register_kernel() -> bool:
    print(f"\n{SEP}")
    print("2. Jupyter kernel registration")
    print(SEP)

    result = subprocess.run(
        [sys.executable, "-m", "ipykernel", "install", "--user",
         "--name", "python3", "--display-name", "Python 3 (cricket-companion)"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        ok("Kernel 'python3' registered for this Python environment")
        return True
    else:
        fail(f"Kernel registration failed:\n{result.stderr.strip()}")
        return False


# ── 3. DB connectivity ────────────────────────────────────────────────────────
def check_db() -> bool:
    print(f"\n{SEP}")
    print("3. MySQL database connectivity")
    print(SEP)

    try:
        import mysql.connector
    except ImportError:
        return fail("mysql-connector-python not installed")

    cfg = {
        "host":     os.getenv("DB_HOST", "localhost"),
        "user":     os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "cricket_companion"),
        "port":     int(os.getenv("DB_PORT", 3306)),
    }

    if not cfg["password"]:
        import getpass
        cfg["password"] = getpass.getpass(
            f"  MySQL password for {cfg['user']}@{cfg['host']}: "
        )
        # Persist for the notebook run (set env var for this process)
        os.environ["DB_PASSWORD"] = cfg["password"]

    try:
        conn = mysql.connector.connect(**cfg)
        ok(f"Connected to {cfg['database']}@{cfg['host']}")
    except mysql.connector.Error as e:
        return fail(f"Connection failed: {e}")

    cursor = conn.cursor()

    # ── Table existence + row counts ──
    EXPECTED = {
        "teams":              ("load_ipl_data.py",    1),
        "players":            ("load_ipl_data.py",    1),
        "series":             ("load_ipl_data.py",    1),
        "matches":            ("load_ipl_data.py",    1),
        "scorecards":         ("load_ipl_data.py",    1),
        "ipl_batting_stats":  ("ipl_transform.py",    100),
        "ipl_bowling_stats":  ("ipl_transform.py",    100),
    }

    all_ok = True
    print()
    for table, (source, min_rows) in EXPECTED.items():
        try:
            cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
            (n,) = cursor.fetchone()
            if n >= min_rows:
                ok(f"{table:<24} {n:>8,} rows")
            else:
                warn(f"{table:<24} {n:>8,} rows  ← run {source} first")
                all_ok = False
        except mysql.connector.Error:
            fail(f"{table:<24} TABLE MISSING  ← run {source} first")
            all_ok = False

    cursor.close()
    conn.close()
    return all_ok


# ── 4. Notebook file check ────────────────────────────────────────────────────
def check_files() -> bool:
    print(f"\n{SEP}")
    print("4. Required files")
    print(SEP)

    files = {
        "ipl_eda.ipynb":   "EDA notebook (source)",
        "run_eda.py":      "Notebook runner",
        "ipl_data_raw/":   "Raw Kaggle data folder",
        ".env":            "DB credentials file",
    }

    all_ok = True
    for path, desc in files.items():
        if Path(path).exists():
            ok(f"{path:<22} {desc}")
        else:
            warn(f"{path:<22} NOT FOUND  ← {desc}")
            if path in ("ipl_eda.ipynb", "run_eda.py"):
                all_ok = False   # hard requirement

    return all_ok


# ── 5. SQLAlchemy engine test ─────────────────────────────────────────────────
def check_sqlalchemy() -> bool:
    print(f"\n{SEP}")
    print("5. SQLAlchemy engine (used by notebook)")
    print(SEP)

    try:
        from sqlalchemy import create_engine, text
        user = os.getenv("DB_USER", "root")
        pw   = os.getenv("DB_PASSWORD", "")
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "3306")
        db   = os.getenv("DB_NAME", "cricket_companion")

        engine = create_engine(
            f"mysql+mysqlconnector://{user}:{pw}@{host}:{port}/{db}",
            echo=False,
        )
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM ipl_batting_stats"))
            (n,) = result.fetchone()
        ok(f"SQLAlchemy engine OK  ({n:,} batting stat rows reachable)")
        engine.dispose()
        return True
    except Exception as e:
        fail(f"SQLAlchemy test failed: {e}")
        warn("The notebook uses SQLAlchemy — fix this before running run_eda.py")
        return False


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  Phase 1 #3 — EDA Pre-flight Check")
    print("=" * 55)

    results = []
    results.append(("Packages",    check_packages()))
    results.append(("Kernel",      register_kernel()))
    results.append(("Database",    check_db()))
    results.append(("Files",       check_files()))
    results.append(("SQLAlchemy",  check_sqlalchemy()))

    print(f"\n{'=' * 55}")
    print("  Summary")
    print("=" * 55)
    all_passed = True
    for name, passed in results:
        status = OK if passed else FAIL
        print(f"  {status}  {name}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("  ✅ All checks passed! Run the notebook with:")
        print()
        print("      python run_eda.py")
        print()
        print("  This produces:")
        print("    • ipl_eda_executed.ipynb  — notebook with all outputs")
        print("    • ipl_eda_report.html     — shareable HTML report")
    else:
        print("  ⚠️  Fix the issues above, then re-run setup_eda.py")
        sys.exit(1)


if __name__ == "__main__":
    main()
