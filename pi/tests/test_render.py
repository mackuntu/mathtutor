import subprocess
from pathlib import Path

import pytest

from mathtutor_pi.render import RenderError, render_pdf


def _ok_run(calls):
    def run(args, **kwargs):
        calls.append((args, kwargs))
        for arg in args:
            if arg.startswith("--print-to-pdf="):
                Path(arg.split("=", 1)[1]).write_bytes(b"%PDF-1.4 data")
        return subprocess.CompletedProcess(args, 0, "", "")

    return run


def test_render_invokes_chromium_and_removes_temp_html(tmp_path):
    calls = []
    out = tmp_path / "ws.pdf"

    render_pdf("<html></html>", out, run=_ok_run(calls))

    args, kwargs = calls[0]
    assert args[0] == "chromium-headless-shell"
    assert "--headless" in args
    assert "--no-pdf-header-footer" in args
    assert f"--print-to-pdf={out}" in args
    assert args[-1].startswith("file://")
    assert kwargs["timeout"] == 60
    assert kwargs["check"] is False
    assert out.read_bytes().startswith(b"%PDF")
    assert [p.name for p in tmp_path.iterdir()] == ["ws.pdf"]


def test_render_nonzero_exit_raises(tmp_path):
    def run(args, **kwargs):
        return subprocess.CompletedProcess(args, 1, "", "boom")

    with pytest.raises(RenderError):
        render_pdf("<html></html>", tmp_path / "ws.pdf", run=run)
    assert list(tmp_path.iterdir()) == []


def test_render_timeout_raises_and_cleans_up(tmp_path):
    def run(args, **kwargs):
        raise subprocess.TimeoutExpired(args, 60)

    with pytest.raises(RenderError, match="timeout"):
        render_pdf("<html></html>", tmp_path / "ws.pdf", run=run)
    assert list(tmp_path.iterdir()) == []


def test_render_missing_binary_raises(tmp_path):
    def run(args, **kwargs):
        raise FileNotFoundError(args[0])

    with pytest.raises(RenderError, match="not found"):
        render_pdf("<html></html>", tmp_path / "ws.pdf", run=run)
    assert list(tmp_path.iterdir()) == []


def test_render_empty_pdf_raises(tmp_path):
    def run(args, **kwargs):
        for arg in args:
            if arg.startswith("--print-to-pdf="):
                Path(arg.split("=", 1)[1]).write_bytes(b"")
        return subprocess.CompletedProcess(args, 0, "", "")

    with pytest.raises(RenderError, match="empty"):
        render_pdf("<html></html>", tmp_path / "ws.pdf", run=run)


def test_render_missing_pdf_raises(tmp_path):
    def run(args, **kwargs):
        return subprocess.CompletedProcess(args, 0, "", "")

    with pytest.raises(RenderError, match="empty"):
        render_pdf("<html></html>", tmp_path / "ws.pdf", run=run)
