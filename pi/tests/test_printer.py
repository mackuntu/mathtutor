import subprocess
from pathlib import Path

import pytest

from mathtutor_pi.printer import CupsPrinter, PrintError

NAME = "Brother_HL_L2340DW"
JOB = f"{NAME}-17"


class FakeRun:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []
        self.envs = []

    def __call__(self, args, **kwargs):
        self.calls.append(args)
        self.envs.append(kwargs.get("env"))
        response = self.responses(args)
        if isinstance(response, Exception):
            raise response
        code, out = response
        return subprocess.CompletedProcess(args, code, out, "")


class FakeTime:
    def __init__(self):
        self.now = 0.0

    def sleep(self, seconds):
        self.now += seconds

    def clock(self):
        return self.now


def _printer(run, fake_time=None):
    fake_time = fake_time or FakeTime()
    return CupsPrinter(NAME, run=run, sleep=fake_time.sleep, clock=fake_time.clock)


def test_submit_parses_job_id():
    run = FakeRun(lambda a: (0, f"request id is {JOB} (1 file(s))\n"))

    assert _printer(run).submit(Path("/tmp/a.pdf"), "Philip WS-1") == JOB
    assert run.calls[0] == ["lp", "-d", NAME, "-t", "Philip WS-1", "/tmp/a.pdf"]


def test_submit_failure_raises_print_error():
    run = FakeRun(lambda a: (1, ""))
    with pytest.raises(PrintError):
        _printer(run).submit(Path("a.pdf"), "t")


def test_submit_unparsable_output_raises():
    run = FakeRun(lambda a: (0, "something odd"))
    with pytest.raises(PrintError, match="job id"):
        _printer(run).submit(Path("a.pdf"), "t")


def test_submit_missing_binary_raises():
    run = FakeRun(lambda a: FileNotFoundError("lp"))
    with pytest.raises(PrintError, match="not found"):
        _printer(run).submit(Path("a.pdf"), "t")


def test_wait_done_returns_when_completed():
    seen = []

    def responses(args):
        seen.append(args)
        done = len(seen) >= 3
        return (0, f"{JOB}  martin 1024  Mon\n" if done else "")

    run = FakeRun(responses)
    _printer(run).wait_done(JOB, timeout_s=60)

    assert len(run.calls) == 3
    assert run.calls[0] == ["lpstat", "-W", "completed", "-o", NAME]


def test_wait_done_ignores_other_job_with_same_prefix():
    run = FakeRun(lambda a: (0, f"{JOB}0  martin 1  Mon\n"))
    with pytest.raises(PrintError, match="timeout"):
        _printer(run).wait_done(JOB, timeout_s=5)


def test_wait_done_timeout_cancels_job():
    run = FakeRun(lambda a: (0, ""))

    with pytest.raises(PrintError, match="printer timeout"):
        _printer(run).wait_done(JOB, timeout_s=10, poll_s=2)

    assert run.calls[-1] == ["cancel", JOB]


def test_wait_done_lpstat_always_failing_cancels_and_raises():
    def responses(args):
        return (0, "") if args[0] == "cancel" else (1, "")

    run = FakeRun(responses)
    with pytest.raises(PrintError):
        _printer(run).wait_done(JOB, timeout_s=10)
    assert run.calls[-1] == ["cancel", JOB]


def test_wait_done_tolerates_transient_lpstat_failure():
    state = {"n": 0}

    def responses(args):
        state["n"] += 1
        return (1, "") if state["n"] == 1 else (0, f"{JOB}  martin 1  Mon\n")

    run = FakeRun(responses)
    _printer(run).wait_done(JOB, timeout_s=10)
    assert all(call[0] != "cancel" for call in run.calls)


def test_commands_run_with_c_locale():
    run = FakeRun(lambda a: (0, f"request id is {JOB} (1 file(s))\n"))
    _printer(run).submit(Path("a.pdf"), "t")
    assert run.envs[0]["LC_ALL"] == "C"


def test_cancel_runs_with_c_locale():
    run = FakeRun(lambda a: (0, ""))
    with pytest.raises(PrintError):
        _printer(run).wait_done(JOB, timeout_s=2)
    assert run.envs[-1]["LC_ALL"] == "C"


def test_submit_launch_oserror_raises():
    run = FakeRun(lambda a: PermissionError("lp"))
    with pytest.raises(PrintError, match="launch"):
        _printer(run).submit(Path("a.pdf"), "t")


def test_exists_true_when_lpstat_succeeds():
    run = FakeRun(lambda a: (0, f"device for {NAME}: ipp://x\n"))

    assert _printer(run).exists() is True
    assert run.calls[0] == ["lpstat", "-v", NAME]
    assert run.envs[0]["LC_ALL"] == "C"


def test_exists_false_when_lpstat_fails():
    run = FakeRun(lambda a: (1, ""))

    assert _printer(run).exists() is False


def test_exists_false_when_lpstat_missing_or_times_out():
    missing = FakeRun(lambda a: FileNotFoundError())
    slow = FakeRun(lambda a: subprocess.TimeoutExpired(a, 10))

    assert _printer(missing).exists() is False
    assert _printer(slow).exists() is False
