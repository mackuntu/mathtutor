"""Config loading for the Pi print-button service."""

import re
import stat
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

TOKEN_PATTERN = re.compile(r"mt_[A-Za-z0-9_-]+")  # prefix + token_urlsafe
LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})
_GROUP_OTHER_BITS = stat.S_IRWXG | stat.S_IRWXO


class ConfigError(Exception):
    """Raised when the config file or token file is invalid."""


@dataclass(frozen=True)
class ButtonConfig:
    kid: str
    child_id: str
    button_pin: int
    led_pin: int


@dataclass(frozen=True)
class Config:
    site_url: str
    token: str = field(repr=False)
    printer: str
    buttons: tuple[ButtonConfig, ...]
    print_timeout_s: float = 120
    error_flash_s: float = 5
    site_timeout_s: float = 30


def _require(table: dict, key: str, where: str = "config"):
    if key not in table:
        raise ConfigError(f"{where}: missing key '{key}'")
    return table[key]


def _read_token(token_path: Path) -> str:
    try:
        mode = token_path.stat().st_mode
        if mode & _GROUP_OTHER_BITS:
            raise ConfigError(
                f"token file {token_path} must be mode 0600 or stricter"
            )
        token = token_path.read_text().strip()
    except OSError as exc:
        raise ConfigError(f"cannot read token file {token_path}: {exc.strerror}")
    except UnicodeDecodeError:
        raise ConfigError(f"token file {token_path} is not valid text") from None
    if not TOKEN_PATTERN.fullmatch(token):
        raise ConfigError(f"token in {token_path} has an invalid format")
    return token


def _check_site_url(url: str) -> str:
    parts = urlsplit(url)
    secure = parts.scheme == "https" and bool(parts.hostname)
    loopback = parts.scheme == "http" and parts.hostname in LOOPBACK_HOSTS
    if not (secure or loopback):
        raise ConfigError("site_url must be https:// (http:// only for loopback)")
    return url


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _positive_number(key: str, value):
    ok = isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0
    if not ok:
        raise ConfigError(f"config: '{key}' must be a number > 0")
    return value


def _pin(raw: dict, key: str, where: str) -> int:
    value = _require(raw, key, where)
    if not _is_int(value) or value < 0:
        raise ConfigError(f"{where}: '{key}' (pin) must be an integer >= 0")
    return value


def _parse_button(raw: dict, index: int) -> ButtonConfig:
    where = f"buttons[{index}]"
    try:
        return ButtonConfig(
            kid=str(_require(raw, "kid", where)),
            child_id=str(_require(raw, "child_id", where)),
            button_pin=_pin(raw, "button_pin", where),
            led_pin=_pin(raw, "led_pin", where),
        )
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"{where}: invalid value ({exc})")


def _check_unique(buttons: tuple[ButtonConfig, ...]) -> None:
    kids = [b.kid for b in buttons]
    if len(set(kids)) != len(kids):
        raise ConfigError("duplicate kid names in buttons")
    pins = [p for b in buttons for p in (b.button_pin, b.led_pin)]
    if len(set(pins)) != len(pins):
        raise ConfigError("duplicate pin across buttons/leds")


def load_config(path: Path) -> Config:
    path = Path(path)
    try:
        with path.open("rb") as fh:
            raw = tomllib.load(fh)
    except OSError as exc:
        raise ConfigError(f"cannot read config {path}: {exc.strerror}")
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"invalid TOML in {path}: {exc}")

    token = _read_token(Path(_require(raw, "token_file")))
    raw_buttons = raw.get("buttons") or []
    if not raw_buttons:
        raise ConfigError("config: at least one [[buttons]] entry is required")
    buttons = tuple(_parse_button(b, i) for i, b in enumerate(raw_buttons))
    _check_unique(buttons)

    optional = {
        k: _positive_number(k, raw[k]) for k in ("print_timeout_s", "error_flash_s", "site_timeout_s")
        if k in raw
    }
    return Config(
        site_url=_check_site_url(str(_require(raw, "site_url"))),
        token=token,
        printer=str(_require(raw, "printer")),
        buttons=buttons,
        **optional,
    )
