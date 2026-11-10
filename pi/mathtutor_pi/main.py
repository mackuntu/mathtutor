"""Command line entrypoint: `run` (GPIO service), `print <kid>`, `children`."""

import argparse
import logging
import signal
import sys
import tempfile
import threading
from pathlib import Path

from mathtutor_pi.config import (
    ButtonConfig,
    Config,
    ConfigError,
    check_child_ids,
    load_config,
)
from mathtutor_pi.controller import KidButton
from mathtutor_pi.printer import CupsPrinter
from mathtutor_pi.render import render_pdf
from mathtutor_pi.site_client import SiteClient, SiteError

log = logging.getLogger("mathtutor_pi")

DEFAULT_CONFIG = Path("/etc/mathtutor-pi/config.toml")
BUTTON_BOUNCE_S = 0.05
BLINK_S = 0.4
FLASH_S = 0.1


class ConsoleLight:
    """Light stand-in for `print`: logs instead of driving a LED."""

    def __init__(self, kid: str):
        self._kid = kid

    def steady(self) -> None:
        log.info("%s light: steady", self._kid)

    def blink(self) -> None:
        log.info("%s light: blink", self._kid)

    def flash(self) -> None:
        log.info("%s light: flash", self._kid)


class GpioLight:
    """Light backed by a gpiozero LED."""

    def __init__(self, led):
        self._led = led

    def steady(self) -> None:
        self._led.on()

    def blink(self) -> None:
        self._led.blink(BLINK_S, BLINK_S)

    def flash(self) -> None:
        self._led.blink(FLASH_S, FLASH_S)


def build_kid_button(
    config: Config,
    button: ButtonConfig,
    light,
    workdir: Path,
    render_lock=None,
) -> KidButton:
    return KidButton(
        button.kid,
        button.child_id,
        light,
        site=SiteClient(config.site_url, config.token, config.site_timeout_s),
        render=render_pdf,
        printer=CupsPrinter(config.printer),
        render_lock=render_lock or threading.Lock(),
        print_timeout_s=config.print_timeout_s,
        error_flash_s=config.error_flash_s,
        workdir=workdir,
    )


def _cmd_print(args, config: Config) -> int:
    wanted = args.kid.casefold()
    button = next((b for b in config.buttons if b.kid.casefold() == wanted), None)
    if button is None:
        known = ", ".join(b.kid for b in config.buttons)
        print(f"error: unknown kid '{args.kid}' (configured: {known})", file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory(prefix="mathtutor-pi-") as workdir:
        kid = build_kid_button(config, button, ConsoleLight(button.kid), Path(workdir))
        return 0 if kid.run_once() else 1


def _cmd_children(args, config: Config) -> int:
    client = SiteClient(config.site_url, config.token, config.site_timeout_s)
    try:
        lines = [f"{child['name']}  {child['id']}" for child in client.children()]
    except (KeyError, TypeError):
        raise SiteError("unexpected response from /api/children") from None
    for line in lines:
        print(line)
    return 0


def _exit_on_sigterm(signum, frame) -> None:
    sys.exit(0)


def _cmd_run(args, config: Config) -> int:
    try:
        from gpiozero import LED, Button  # only the service needs GPIO
    except ImportError as exc:
        print(f"error: gpiozero is not available ({exc})", file=sys.stderr)
        return 1

    if not CupsPrinter(config.printer).exists():
        log.warning("printer queue '%s' not found; prints will fail", config.printer)
    signal.signal(signal.SIGTERM, _exit_on_sigterm)  # let gpiozero close pins

    workdir = Path(tempfile.mkdtemp(prefix="mathtutor-pi-"))
    render_lock = threading.Lock()
    hardware = []  # keep references so gpiozero devices are not collected
    for button in config.buttons:
        led = LED(button.led_pin)
        kid = build_kid_button(config, button, GpioLight(led), workdir, render_lock)
        switch = Button(button.button_pin, pull_up=True, bounce_time=BUTTON_BOUNCE_S)
        switch.when_pressed = kid.on_press
        hardware.append((led, switch, kid))
        log.info(
            "%s: button GPIO%d, LED GPIO%d",
            button.kid,
            button.button_pin,
            button.led_pin,
        )
    log.info("ready: %d button(s)", len(hardware))
    signal.pause()
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mathtutor_pi")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, handler in (
        ("run", _cmd_run),
        ("print", _cmd_print),
        ("children", _cmd_children),
    ):
        cmd = sub.add_parser(name)
        if name == "print":
            cmd.add_argument("kid")
        cmd.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
        cmd.set_defaults(handler=handler)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO, stream=sys.stderr, format="%(levelname)s %(message)s"
    )
    try:
        config = load_config(args.config)
        if args.command != "children":
            check_child_ids(config)
        return args.handler(args, config)
    except (ConfigError, SiteError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
