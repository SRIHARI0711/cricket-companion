"""
run_eda.py — Execute the IPL EDA notebook and export it as HTML.

Usage:
    python run_eda.py

Outputs:
    ipl_eda_executed.ipynb   — fully-executed notebook with all outputs
    ipl_eda_report.html      — self-contained HTML export (for sharing)
"""

import sys
import os

# Force UTF-8 console output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

NOTEBOOK_IN  = Path("ipl_eda.ipynb")
NOTEBOOK_OUT = Path("ipl_eda_executed.ipynb")
HTML_OUT     = Path("ipl_eda_report.html")

def run_notebook():
    """Execute notebook cells using nbconvert --execute."""
    log.info("Executing notebook: %s", NOTEBOOK_IN)
    result = subprocess.run(
        [
            sys.executable, "-m", "nbconvert",
            "--to", "notebook",
            "--execute",
            "--ExecutePreprocessor.timeout=600",
            "--ExecutePreprocessor.kernel_name=python3",
            "--output", str(NOTEBOOK_OUT.name),
            "--output-dir", str(NOTEBOOK_OUT.parent),
            str(NOTEBOOK_IN),
        ],
        capture_output=True, text=True, encoding="utf-8",
    )
    if result.returncode != 0:
        log.error("Notebook execution failed:\n%s", result.stderr[-3000:])
        sys.exit(1)
    log.info("Notebook executed successfully -> %s", NOTEBOOK_OUT)


def export_html():
    """Convert the executed notebook to a self-contained HTML file."""
    log.info("Exporting to HTML: %s", HTML_OUT)
    result = subprocess.run(
        [
            sys.executable, "-m", "nbconvert",
            "--to", "html",
            "--no-input",          # hide code cells for a clean report view
            "--output", str(HTML_OUT),
            str(NOTEBOOK_OUT),
        ],
        capture_output=True, text=True, encoding="utf-8",
    )
    if result.returncode != 0:
        # Try with input shown if --no-input fails on older nbconvert
        log.warning("Retrying HTML export with code cells visible …")
        result2 = subprocess.run(
            [
                sys.executable, "-m", "nbconvert",
                "--to", "html",
                "--output", str(HTML_OUT),
                str(NOTEBOOK_OUT),
            ],
            capture_output=True, text=True, encoding="utf-8",
        )
        if result2.returncode != 0:
            log.error("HTML export failed:\n%s", result2.stderr[-3000:])
            sys.exit(1)
    log.info("HTML report saved -> %s  (%s)", HTML_OUT, _human_size(HTML_OUT))


def _human_size(path: Path) -> str:
    b = path.stat().st_size
    for unit in ("B", "KB", "MB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} GB"


if __name__ == "__main__":
    run_notebook()
    export_html()
    log.info("Done!  Open %s in any browser.", HTML_OUT.resolve())
