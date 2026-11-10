import os
import subprocess
import time
from pathlib import Path

import pytest

from mathtutor_pi.render import RenderError, render_pdf


class FakeProc:
    def __init__(self, returncode=0):
        self.pid = 0
        self.returncode = returncode

    def wait(self, timeout=None):
        return self.returncode


def _fake_popen(returncode=0, pdf=b"%PDF-1.4 data", calls=None):
    def popen(args, **kwargs):
        if calls is not None:
            calls.append((args, kwargs))
        if pdf is not None:
            for arg in args:
                if arg.startswith("--print-to-pdf="):
                    Path(arg.split("=", 1)[1]).write_bytes(pdf)
        return FakeProc(returncode)

    return popen


def test_render_invokes_chromium_and_removes_temp_html(tmp_path):
    calls = []
    out = tmp_path / "ws.pdf"

    render_pdf("<html></html>", out, popen=_fake_popen(calls=calls))

    args, kwargs = calls[0]
    assert args[0] == "chromium-headless-shell"
    assert "--headless" in args
    assert "--no-pdf-header-footer" in args
    assert f"--print-to-pdf={out}" in args
    assert args[-1].startswith("file://")
    assert kwargs["stdout"] == subprocess.DEVNULL
    assert kwargs["stderr"] == subprocess.DEVNULL
    assert kwargs["start_new_session"] is True
    assert out.read_bytes().startswith(b"%PDF")
    assert [p.name for p in tmp_path.iterdir()] == ["ws.pdf"]


def test_render_nonzero_exit_raises(tmp_path):
    with pytest.raises(RenderError):
        render_pdf("<html></html>", tmp_path / "ws.pdf", popen=_fake_popen(1))
    assert list(tmp_path.iterdir()) == []


def test_render_missing_binary_raises(tmp_path):
    def popen(args, **kwargs):
        raise FileNotFoundError(args[0])

    with pytest.raises(RenderError, match="not found"):
        render_pdf("<html></html>", tmp_path / "ws.pdf", popen=popen)
    assert list(tmp_path.iterdir()) == []


def test_render_launch_oserror_raises(tmp_path):
    def popen(args, **kwargs):
        raise PermissionError(args[0])

    with pytest.raises(RenderError, match="launch"):
        render_pdf("<html></html>", tmp_path / "ws.pdf", popen=popen)
    assert list(tmp_path.iterdir()) == []


def test_render_empty_pdf_raises_and_removes_it(tmp_path):
    out = tmp_path / "ws.pdf"
    with pytest.raises(RenderError, match="empty"):
        render_pdf("<html></html>", out, popen=_fake_popen(pdf=b""))
    assert list(tmp_path.iterdir()) == []


def test_render_removes_stale_pdf_before_running(tmp_path):
    out = tmp_path / "ws.pdf"
    out.write_bytes(b"%PDF stale")

    with pytest.raises(RenderError):
        render_pdf("<html></html>", out, popen=_fake_popen(pdf=None))

    assert not out.exists()


@pytest.mark.skipif(os.name != "posix", reason="needs POSIX process groups")
def test_render_timeout_kills_whole_process_group(tmp_path):
    pid_file = tmp_path / "child.pid"
    script = tmp_path / "fake-chromium"
    script.write_text(f"#!/bin/sh\nsleep 30 &\necho $! > {pid_file}\nsleep 30\n")
    script.chmod(0o755)
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    started = time.monotonic()
    with pytest.raises(RenderError, match="timeout"):
        render_pdf(
            "<html></html>", out_dir / "ws.pdf", timeout_s=0.5, chromium=str(script)
        )

    assert time.monotonic() - started < 3
    assert list(out_dir.iterdir()) == []
    child_pid = int(pid_file.read_text())
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        try:
            os.kill(child_pid, 0)
        except ProcessLookupError:
            break
        time.sleep(0.05)
    with pytest.raises(ProcessLookupError):
        os.kill(child_pid, 0)
