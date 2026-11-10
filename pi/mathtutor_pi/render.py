"""Render worksheet HTML to PDF with headless Chromium."""

import subprocess
import tempfile
from pathlib import Path

DEFAULT_CHROMIUM = "chromium-headless-shell"

# Flags for unattended, display-less rendering. Confirm against the installed
# binary on the Pi (Task 7) and adjust here.
CHROMIUM_FLAGS = (
    "--headless",
    "--disable-gpu",
    "--no-pdf-header-footer",
)


class RenderError(Exception):
    """HTML could not be rendered to a PDF. Messages are short reasons."""


def render_pdf(
    html: str,
    out_pdf: Path,
    *,
    timeout_s: float = 60,
    run=subprocess.run,
    chromium: str = DEFAULT_CHROMIUM,
) -> None:
    out_pdf = Path(out_pdf)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        suffix=".html",
        dir=out_pdf.parent,
        delete=False,
    ) as handle:
        handle.write(html)
        tmp_html = Path(handle.name)
    try:
        _run_chromium(tmp_html, out_pdf, timeout_s, run, chromium)
    finally:
        tmp_html.unlink(missing_ok=True)


def _run_chromium(tmp_html: Path, out_pdf: Path, timeout_s, run, chromium) -> None:
    args = [
        chromium,
        *CHROMIUM_FLAGS,
        f"--print-to-pdf={out_pdf}",
        tmp_html.resolve().as_uri(),
    ]
    try:
        result = run(
            args, timeout=timeout_s, capture_output=True, text=True, check=False
        )
    except subprocess.TimeoutExpired:
        raise RenderError("render timeout") from None
    except FileNotFoundError:
        raise RenderError("chromium not found") from None
    if result.returncode != 0:
        raise RenderError(f"chromium exited {result.returncode}")
    if not out_pdf.exists() or out_pdf.stat().st_size == 0:
        raise RenderError("chromium produced empty pdf")
