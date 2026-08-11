"""
run_eda.py — Execute the IPL EDA notebook and export it as HTML.

Usage:
    python run_eda.py

Outputs:
    ipl_eda_executed.ipynb   — fully-executed notebook with all outputs
    ipl_eda_report.html      — self-contained HTML export (for sharing)
"""

import sys
import subprocess
import logging
from pathlib import Path

# Force UTF-8 console output on Windows so log lines with box-drawing chars work
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)

NOTEBOOK_IN  = Path("ipl_eda.ipynb")
NOTEBOOK_OUT = Path("ipl_eda_executed.ipynb")
HTML_OUT     = Path("ipl_eda_report.html")


def _run(cmd: list, label: str) -> subprocess.CompletedProcess:
    """
    Run a subprocess, capturing stdout/stderr as raw bytes and decoding with
    errors='replace' so non-UTF-8 bytes (e.g. Windows font data in matplotlib
    output) never raise a UnicodeDecodeError.
    """
    result = subprocess.run(cmd, capture_output=True)
    result.stdout_text = (result.stdout or b"").decode("utf-8", errors="replace")
    result.stderr_text = (result.stderr or b"").decode("utf-8", errors="replace")
    return result


def run_notebook():
    """Execute all notebook cells using nbconvert --execute."""
    log.info("Executing notebook: %s", NOTEBOOK_IN)

    result = _run(
        [
            sys.executable, "-m", "nbconvert",
            "--to", "notebook",
            "--execute",
            "--ExecutePreprocessor.timeout=600",
            "--ExecutePreprocessor.kernel_name=python3",
            "--output", NOTEBOOK_OUT.name,
            "--output-dir", str(NOTEBOOK_OUT.parent.resolve()),
            str(NOTEBOOK_IN),
        ],
        label="notebook execute",
    )

    if result.returncode != 0:
        log.error("Notebook execution FAILED (exit %d):\n%s",
                  result.returncode, result.stderr_text[-4000:])
        sys.exit(1)

    log.info("Notebook executed successfully -> %s", NOTEBOOK_OUT)
    if result.stderr_text.strip():
        # nbconvert writes progress to stderr; log at DEBUG so it's not noisy
        log.debug("nbconvert stderr:\n%s", result.stderr_text[-2000:])


def export_html():
    """Convert the executed notebook to a self-contained HTML report."""
    log.info("Exporting HTML report: %s", HTML_OUT)

    base_cmd = [
        sys.executable, "-m", "nbconvert",
        "--to", "html",
        "--output", HTML_OUT.name,
        "--output-dir", str(HTML_OUT.parent.resolve()),
    ]

    # Try clean report (no code cells) first; fall back to full if unsupported
    for extra, attempt in [([" --no-input"], "clean"), ([], "full")]:
        cmd = base_cmd + (["--no-input"] if attempt == "clean" else []) + [str(NOTEBOOK_OUT)]
        result = _run(cmd, label=f"html export ({attempt})")

        if result.returncode == 0:
            log.info("HTML report saved -> %s  (%s)", HTML_OUT, _human_size(HTML_OUT))
            return

        log.warning("HTML export (%s) failed (exit %d), retrying…",
                    attempt, result.returncode)
        log.debug("stderr: %s", result.stderr_text[-2000:])

    log.error("HTML export failed on all attempts.")
    sys.exit(1)


def _human_size(path: Path) -> str:
    b = path.stat().st_size
    for unit in ("B", "KB", "MB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} GB"


if __name__ == "__main__":
    if not NOTEBOOK_IN.exists():
        log.error("Notebook not found: %s", NOTEBOOK_IN.resolve())
        sys.exit(1)

    run_notebook()
    export_html()
    log.info("Done! Open in browser: %s", HTML_OUT.resolve())
