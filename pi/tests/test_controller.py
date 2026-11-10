import logging
import threading
from pathlib import Path

import pytest

from mathtutor_pi.controller import KidButton
from mathtutor_pi.printer import PrintError
from mathtutor_pi.render import RenderError
from mathtutor_pi.site_client import PrintableWorksheet, SiteError

WAIT = 5  # seconds; only reached if a test is broken


class FakeLight:
    def __init__(self):
        self.calls = []

    def steady(self):
        self.calls.append("steady")

    def blink(self):
        self.calls.append("blink")

    def flash(self):
        self.calls.append("flash")


class FakeSite:
    def __init__(self, gate=None, error=None):
        self.gate = gate
        self.error = error
        self.calls = []
        self.entered = threading.Event()

    def new_worksheet(self, child_id):
        self.calls.append(child_id)
        self.entered.set()
        if self.gate is not None:
            assert self.gate.wait(WAIT)
        if self.error is not None:
            raise self.error
        return PrintableWorksheet(serial=f"S-{child_id}", html="<p>secret html</p>")


class FakeRender:
    def __init__(self, error_for=None):
        self.error_for = error_for
        self.calls = []
        self.active = 0
        self.max_active = 0
        self._lock = threading.Lock()

    def __call__(self, html, pdf):
        with self._lock:
            self.active += 1
            self.max_active = max(self.max_active, self.active)
        try:
            self.calls.append((html, pdf))
            Path(pdf).write_bytes(b"%PDF")
            threading.Event().wait(0.02)  # widen any overlap window
            if self.error_for is not None and self.error_for in html:
                raise RenderError("chromium failed")
        finally:
            with self._lock:
                self.active -= 1


class FakePrinter:
    def __init__(self, error=None):
        self.error = error
        self.submitted = []
        self.waited = []

    def submit(self, pdf, title):
        self.submitted.append((Path(pdf), title))
        assert Path(pdf).exists()
        return f"job-{len(self.submitted)}"

    def wait_done(self, job_id, timeout_s, poll_s=2):
        self.waited.append((job_id, timeout_s))
        if self.error is not None:
            raise self.error


class FakeSleep:
    def __init__(self):
        self.calls = []

    def __call__(self, seconds):
        self.calls.append(seconds)


def _button(
    tmp_path,
    kid="Philip",
    *,
    site=None,
    render=None,
    printer=None,
    light=None,
    render_lock=None,
    sleep=None,
):
    return KidButton(
        kid,
        f"id-{kid}",
        light or FakeLight(),
        site=site or FakeSite(),
        render=render or FakeRender(),
        printer=printer or FakePrinter(),
        render_lock=render_lock or threading.Lock(),
        print_timeout_s=120,
        error_flash_s=3,
        workdir=tmp_path,
        sleep=sleep or FakeSleep(),
    )


def _press_and_wait(button):
    assert button.on_press() is True
    button.join(WAIT)


def test_light_is_steady_on_construction(tmp_path):
    light = FakeLight()
    _button(tmp_path, light=light)
    assert light.calls == ["steady"]


def test_press_prints_and_returns_to_steady(tmp_path, caplog):
    caplog.set_level(logging.INFO, logger="mathtutor_pi")
    light, site, printer = FakeLight(), FakeSite(), FakePrinter()
    render = FakeRender()
    button = _button(tmp_path, light=light, site=site, render=render, printer=printer)

    _press_and_wait(button)

    assert light.calls == ["steady", "blink", "steady"]
    assert site.calls == ["id-Philip"]
    assert render.calls[0][0] == "<p>secret html</p>"
    pdf, title = printer.submitted[0]
    assert title == "Philip S-id-Philip"
    assert pdf.parent == tmp_path
    assert printer.waited == [("job-1", 120)]
    assert not pdf.exists()
    assert "Philip: pressed" in caplog.messages
    assert "Philip: printed S-id-Philip" in caplog.messages
    assert "secret html" not in caplog.text


def test_presses_while_busy_are_ignored(tmp_path, caplog):
    caplog.set_level(logging.INFO, logger="mathtutor_pi")
    gate = threading.Event()
    site = FakeSite(gate=gate)
    light = FakeLight()
    button = _button(tmp_path, site=site, light=light)

    assert button.on_press() is True
    assert site.entered.wait(WAIT)
    assert button.on_press() is False
    assert button.on_press() is False
    gate.set()
    button.join(WAIT)

    assert site.calls == ["id-Philip"]
    assert caplog.messages.count("Philip: busy, press ignored") == 2
    assert light.calls == ["steady", "blink", "steady"]


def test_simultaneous_presses_start_one_job(tmp_path):
    gate = threading.Event()
    site = FakeSite(gate=gate)
    button = _button(tmp_path, site=site)
    start = threading.Barrier(8)
    results = []

    def press():
        start.wait(WAIT)
        results.append(button.on_press())

    threads = [threading.Thread(target=press) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(WAIT)
    gate.set()
    button.join(WAIT)

    assert results.count(True) == 1
    assert site.calls == ["id-Philip"]


def test_two_kids_run_independently(tmp_path):
    gate = threading.Event()
    philip_site = FakeSite(gate=gate)
    sudo_printer = FakePrinter()
    lock = threading.Lock()
    philip = _button(tmp_path, "Philip", site=philip_site, render_lock=lock)
    sudo = _button(tmp_path, "Sudo", printer=sudo_printer, render_lock=lock)

    assert philip.on_press() is True
    assert philip_site.entered.wait(WAIT)
    _press_and_wait(sudo)

    assert [title for _, title in sudo_printer.submitted] == ["Sudo S-id-Sudo"]
    gate.set()
    philip.join(WAIT)


def test_renders_are_serialized(tmp_path):
    render = FakeRender()
    lock = threading.Lock()
    printer = FakePrinter()
    buttons = [
        _button(tmp_path, kid, render=render, render_lock=lock, printer=printer)
        for kid in ("Philip", "Sudo")
    ]

    for b in buttons:
        assert b.on_press() is True
    for b in buttons:
        b.join(WAIT)

    assert len(render.calls) == 2
    assert render.max_active == 1
    assert len({pdf for _, pdf in render.calls}) == 2


def test_print_failure_flashes_then_ready(tmp_path, caplog):
    light, sleep = FakeLight(), FakeSleep()
    printer = FakePrinter(error=PrintError("printer timeout"))
    button = _button(tmp_path, light=light, printer=printer, sleep=sleep)

    _press_and_wait(button)

    assert light.calls == ["steady", "blink", "flash", "steady"]
    assert sleep.calls == [3]
    assert "Philip: failed: printer timeout" in caplog.messages
    assert list(tmp_path.iterdir()) == []


def test_site_error_flashes_and_logs_reason(tmp_path, caplog):
    light = FakeLight()
    site = FakeSite(error=SiteError("unauthorized"))
    printer = FakePrinter()
    button = _button(tmp_path, light=light, site=site, printer=printer)

    _press_and_wait(button)

    assert light.calls == ["steady", "blink", "flash", "steady"]
    assert "Philip: failed: unauthorized" in caplog.messages
    assert printer.submitted == []


def test_unexpected_exception_flashes_and_logs_type(tmp_path, caplog):
    light = FakeLight()
    site = FakeSite(error=ValueError("boom"))
    button = _button(tmp_path, light=light, site=site)

    _press_and_wait(button)

    assert light.calls == ["steady", "blink", "flash", "steady"]
    assert any(
        "Philip: failed:" in m and "ValueError" in m and "boom" in m
        for m in caplog.messages
    )
    assert button.on_press() is True
    button.join(WAIT)


def test_render_lock_released_after_failure(tmp_path):
    render = FakeRender(error_for="secret")
    lock = threading.Lock()
    philip_light = FakeLight()
    philip = _button(
        tmp_path, "Philip", render=render, render_lock=lock, light=philip_light
    )
    _press_and_wait(philip)
    assert philip_light.calls == ["steady", "blink", "flash", "steady"]
    assert not lock.locked()
    assert list(tmp_path.iterdir()) == []

    render.error_for = None
    sudo_printer = FakePrinter()
    sudo = _button(
        tmp_path, "Sudo", render=render, render_lock=lock, printer=sudo_printer
    )
    _press_and_wait(sudo)
    assert len(sudo_printer.submitted) == 1


def test_press_after_failure_works_again(tmp_path):
    light = FakeLight()
    site = FakeSite(error=SiteError("timeout"))
    button = _button(tmp_path, light=light, site=site)

    _press_and_wait(button)
    site.error = None
    _press_and_wait(button)

    assert light.calls == [
        "steady",
        "blink",
        "flash",
        "steady",
        "blink",
        "steady",
    ]
    assert site.calls == ["id-Philip", "id-Philip"]


def test_light_failure_does_not_leave_button_busy(tmp_path, caplog):
    class BrokenLight(FakeLight):
        def flash(self):
            raise RuntimeError("gpio gone")

    light = BrokenLight()
    site = FakeSite(error=SiteError("timeout"))
    button = _button(tmp_path, light=light, site=site)

    _press_and_wait(button)

    assert light.calls[-1] == "steady"
    assert button.on_press() is True
    button.join(WAIT)


def test_join_without_press_returns(tmp_path):
    _button(tmp_path).join(0.1)


@pytest.mark.parametrize("kid", ["Philip", "Sudo"])
def test_pdf_paths_unique_per_job(tmp_path, kid):
    render = FakeRender()
    button = _button(tmp_path, kid, render=render)
    _press_and_wait(button)
    _press_and_wait(button)
    first, second = (pdf for _, pdf in render.calls)
    assert first != second


def test_run_once_returns_true_on_success(tmp_path):
    light, printer = FakeLight(), FakePrinter()
    button = _button(tmp_path, light=light, printer=printer)

    assert button.run_once() is True

    assert light.calls == ["steady", "blink", "steady"]
    assert list(tmp_path.iterdir()) == []


def test_run_once_returns_false_on_failure_and_can_rerun(tmp_path):
    button = _button(tmp_path, printer=FakePrinter(error=PrintError("jammed")))

    assert button.run_once() is False
    assert button.run_once() is False  # busy lock was released


def test_run_once_returns_false_when_busy(tmp_path):
    button = _button(tmp_path)
    assert button._busy.acquire(blocking=False)

    assert button.run_once() is False
