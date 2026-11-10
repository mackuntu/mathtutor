"""One kid's button: press -> fetch worksheet -> render PDF -> print."""

import logging
import threading
import time
import uuid
from pathlib import Path

from mathtutor_pi.light import Light
from mathtutor_pi.printer import PrintError
from mathtutor_pi.render import RenderError
from mathtutor_pi.site_client import SiteError

log = logging.getLogger("mathtutor_pi")

_EXPECTED_ERRORS = (SiteError, RenderError, PrintError)


class KidButton:
    """Runs at most one print job at a time for one kid.

    `on_press` is safe to call from any thread (gpiozero callbacks). Presses
    while a job runs are ignored. Only the render step holds `render_lock`,
    which is shared between kids so Chromium renders never overlap.
    """

    def __init__(
        self,
        kid: str,
        child_id: str,
        light: Light,
        *,
        site,
        render,
        printer,
        render_lock: threading.Lock,
        print_timeout_s: float,
        error_flash_s: float,
        workdir: Path,
        sleep=time.sleep,
    ):
        self._kid = kid
        self._child_id = child_id
        self._light = light
        self._site = site
        self._render = render
        self._printer = printer
        self._render_lock = render_lock
        self._print_timeout_s = print_timeout_s
        self._error_flash_s = error_flash_s
        self._workdir = Path(workdir)
        self._sleep = sleep
        self._busy = threading.Lock()
        self._thread: threading.Thread | None = None
        self._light.steady()

    def on_press(self) -> bool:
        if not self._busy.acquire(blocking=False):
            log.info("%s: busy, press ignored", self._kid)
            return False
        log.info("%s: pressed", self._kid)
        thread = threading.Thread(
            target=self._run, name=f"print-{self._kid}", daemon=True
        )
        try:
            thread.start()
        except BaseException:
            self._busy.release()
            raise
        self._thread = thread
        return True

    def run_once(self) -> bool:
        """Run one job synchronously. False if busy or the job failed."""
        if not self._busy.acquire(blocking=False):
            log.info("%s: busy, run ignored", self._kid)
            return False
        return self._run()

    def join(self, timeout: float | None = None) -> None:
        thread = self._thread
        if thread is not None:
            thread.join(timeout)

    def _run(self) -> bool:
        """Run the job; the caller must hold `_busy`, released here."""
        pdf = self._workdir / f"{uuid.uuid4().hex}.pdf"
        succeeded = False
        try:
            try:
                self._print_one(pdf)
                succeeded = True
            except _EXPECTED_ERRORS as exc:
                log.warning("%s: failed: %s", self._kid, exc)
                self._show_failure()
            except Exception as exc:
                log.exception("%s: failed: %s: %s", self._kid, type(exc).__name__, exc)
                self._show_failure()
            finally:
                self._remove(pdf)
                self._set_light("steady")
        finally:
            self._busy.release()
        return succeeded

    def _print_one(self, pdf: Path) -> None:
        self._light.blink()
        worksheet = self._site.new_worksheet(self._child_id)
        with self._render_lock:
            self._render(worksheet.html, pdf)
        job_id = self._printer.submit(pdf, f"{self._kid} {worksheet.serial}")
        self._printer.wait_done(job_id, self._print_timeout_s)
        log.info("%s: printed %s", self._kid, worksheet.serial)

    def _show_failure(self) -> None:
        self._set_light("flash")
        try:
            self._sleep(self._error_flash_s)
        except Exception:
            log.exception("%s: error-flash sleep failed", self._kid)

    def _set_light(self, state: str) -> None:
        try:
            getattr(self._light, state)()
        except Exception:
            log.exception("%s: light %s failed", self._kid, state)

    def _remove(self, pdf: Path) -> None:
        try:
            pdf.unlink(missing_ok=True)
        except OSError as exc:
            log.warning("%s: could not remove %s: %s", self._kid, pdf.name, exc)
