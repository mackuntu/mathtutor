"""Submit PDFs to a CUPS printer and wait for the job to finish."""

import re
import subprocess
import time
from pathlib import Path

_REQUEST_ID = re.compile(r"request id is (\S+)")


class PrintError(Exception):
    """Printing failed. Messages are short reasons."""


class CupsPrinter:
    def __init__(
        self, name: str, run=subprocess.run, sleep=time.sleep, clock=time.monotonic
    ):
        self._name = name
        self._run = run
        self._sleep = sleep
        self._clock = clock

    def submit(self, pdf: Path, title: str) -> str:
        """Run `lp` and return the CUPS job id (e.g. `Brother-17`)."""
        out = self._cups(["lp", "-d", self._name, "-t", title, str(pdf)], "lp")
        match = _REQUEST_ID.search(out)
        if match is None:
            raise PrintError("could not parse job id")
        return match.group(1)

    def wait_done(self, job_id: str, timeout_s: float, poll_s: float = 2) -> None:
        """Poll `lpstat -W completed -o <printer>` until `job_id` is listed.

        The job counts as done once its id is the first token of a line in the
        completed-jobs list. On timeout the job is cancelled and PrintError
        raised.
        """
        deadline = self._clock() + timeout_s
        while True:
            out = self._cups(["lpstat", "-W", "completed", "-o", self._name], "lpstat")
            if any(line.split()[:1] == [job_id] for line in out.splitlines()):
                return
            if self._clock() >= deadline:
                break
            self._sleep(poll_s)
        self._cancel(job_id)
        raise PrintError("printer timeout")

    def _cancel(self, job_id: str) -> None:
        try:
            self._run(
                ["cancel", job_id],
                timeout=30,
                capture_output=True,
                text=True,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            pass  # best effort; the timeout error is what matters

    def _cups(self, args: list[str], label: str) -> str:
        try:
            result = self._run(
                args, timeout=30, capture_output=True, text=True, check=False
            )
        except FileNotFoundError:
            raise PrintError(f"{label} not found") from None
        except subprocess.TimeoutExpired:
            raise PrintError(f"{label} timeout") from None
        if result.returncode != 0:
            raise PrintError(f"{label} exited {result.returncode}")
        return result.stdout or ""
