import os
from pathlib import Path

import pytest

from mathtutor_pi.config import ButtonConfig, Config, ConfigError, load_config

TOKEN = "mt_secret123"

BUTTONS = """
[[buttons]]
kid = "Philip"
child_id = "c1"
button_pin = 17
led_pin = 27

[[buttons]]
kid = "Sudo"
child_id = "c2"
button_pin = 22
led_pin = 23
"""


def write(tmp_path: Path, body: str, token: str = TOKEN, mode: int = 0o600) -> Path:
    token_file = tmp_path / "token"
    token_file.write_text(token + "\n")
    token_file.chmod(mode)
    cfg = tmp_path / "config.toml"
    cfg.write_text(
        f'site_url = "https://example.test"\ntoken_file = "{token_file}"\n'
        f'printer = "P"\n{body}'
    )
    return cfg


def test_valid_config_loads(tmp_path):
    cfg = load_config(write(tmp_path, BUTTONS))
    assert cfg.site_url == "https://example.test"
    assert cfg.token == TOKEN
    assert cfg.printer == "P"
    assert cfg.buttons[0] == ButtonConfig("Philip", "c1", 17, 27)
    assert len(cfg.buttons) == 2
    assert (cfg.print_timeout_s, cfg.error_flash_s, cfg.site_timeout_s) == (120, 5, 30)


def test_optional_timeouts_override(tmp_path):
    cfg = load_config(write(tmp_path, "site_timeout_s = 7\n" + BUTTONS))
    assert cfg.site_timeout_s == 7


def test_example_config_parses(tmp_path):
    example = Path(__file__).parent.parent / "config.example.toml"
    text = example.read_text()
    token_file = tmp_path / "token"
    token_file.write_text(TOKEN)
    token_file.chmod(0o600)
    local = tmp_path / "c.toml"
    local.write_text(text.replace("/etc/mathtutor-pi/token", str(token_file)))
    cfg = load_config(local)
    assert [(b.kid, b.button_pin, b.led_pin) for b in cfg.buttons] == [
        ("Philip", 17, 27),
        ("Sudo", 22, 23),
    ]


def test_repr_hides_token(tmp_path):
    cfg = load_config(write(tmp_path, BUTTONS))
    assert TOKEN not in repr(cfg)


def test_missing_key_raises(tmp_path):
    path = write(tmp_path, BUTTONS)
    path.write_text(path.read_text().replace('printer = "P"\n', ""))
    with pytest.raises(ConfigError, match="printer"):
        load_config(path)


def test_missing_file_raises(tmp_path):
    with pytest.raises(ConfigError):
        load_config(tmp_path / "nope.toml")


def test_empty_buttons_raises(tmp_path):
    with pytest.raises(ConfigError, match="buttons"):
        load_config(write(tmp_path, ""))


def test_button_missing_field_raises(tmp_path):
    body = '[[buttons]]\nkid = "A"\nchild_id = "c"\nbutton_pin = 1\n'
    with pytest.raises(ConfigError, match="led_pin"):
        load_config(write(tmp_path, body))


def test_duplicate_pins_raise(tmp_path):
    body = BUTTONS.replace("button_pin = 22", "button_pin = 27")
    with pytest.raises(ConfigError, match="pin"):
        load_config(write(tmp_path, body))


def test_duplicate_kid_raises(tmp_path):
    with pytest.raises(ConfigError, match="kid"):
        load_config(write(tmp_path, BUTTONS.replace("Sudo", "Philip")))


def test_token_prefix_enforced(tmp_path):
    with pytest.raises(ConfigError) as e:
        load_config(write(tmp_path, BUTTONS, token="badtoken"))
    assert "badtoken" not in str(e.value)


@pytest.mark.parametrize("mode", [0o640, 0o604, 0o644, 0o660])
def test_loose_token_file_mode_raises(tmp_path, mode):
    with pytest.raises(ConfigError, match="0600"):
        load_config(write(tmp_path, BUTTONS, mode=mode))


def test_stricter_token_mode_ok(tmp_path):
    assert load_config(write(tmp_path, BUTTONS, mode=0o400)).token == TOKEN


def test_missing_token_file_raises(tmp_path):
    path = write(tmp_path, BUTTONS)
    os.remove(tmp_path / "token")
    with pytest.raises(ConfigError):
        load_config(path)
