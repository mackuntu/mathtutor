"""Render worksheet HTML to PDF with headless Chromium."""

import os
import shutil
import signal
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
    popen=subprocess.Popen,
    chromium: str = DEFAULT_CHROMIUM,
) -> None:
    out_pdf = Path(out_pdf)
    out_pdf.unlink(missing_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        # BOM: the page has no charset and file:// has no HTTP header, so this
        # is how Chromium learns it is UTF-8 (U+2212, x). No doctype: quirks
        # mode layout must stay.
        encoding="utf-8-sig",
        suffix=".html",
        dir=out_pdf.parent,
        delete=False,
    ) as handle:
        handle.write(html)
        tmp_html = Path(handle.name)
    profile = Path(tempfile.mkdtemp(prefix="chromium-profile-", dir=out_pdf.parent))
    try:
        _run_chromium(tmp_html, out_pdf, profile, timeout_s, popen, chromium)
    except RenderError:
        out_pdf.unlink(missing_ok=True)
        raise
    finally:
        tmp_html.unlink(missing_ok=True)
        shutil.rmtree(profile, ignore_errors=True)


def _run_chromium(
    tmp_html: Path, out_pdf: Path, profile: Path, timeout_s, popen, chromium
) -> None:
    args = [
        chromium,
        *CHROMIUM_FLAGS,
        f"--user-data-dir={profile}",
        f"--print-to-pdf={out_pdf}",
        tmp_html.resolve().as_uri(),
    ]
    try:
        # Own session so the whole process tree can be killed; no inherited
        # pipes so orphaned children can never block us.
        proc = popen(
            args,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except FileNotFoundError:
        raise RenderError("chromium not found") from None
    except OSError:
        raise RenderError("chromium launch failed") from None
    try:
        proc.wait(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        _kill_group(proc)
        raise RenderError("render timeout") from None
    if proc.returncode != 0:
        raise RenderError(f"chromium exited {proc.returncode}")
    if not out_pdf.exists() or out_pdf.stat().st_size == 0:
        raise RenderError("chromium produced empty pdf")


def _kill_group(proc) -> None:
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    proc.wait()
