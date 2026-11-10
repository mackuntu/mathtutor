import os
from pathlib import Path

import pytest

from mathtutor_pi.config import (
    ButtonConfig,
    Config,
    ConfigError,
    check_child_ids,
    load_config,
)

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


@pytest.mark.parametrize("token", ["mt_a\nb", "mt_caf\u00e9", "mt_a b", "mt_"])
def test_malformed_token_rejected_without_leak(tmp_path, token):
    with pytest.raises(ConfigError) as e:
        load_config(write(tmp_path, BUTTONS, token=token))
    assert token.strip() not in str(e.value) and "caf" not in str(e.value)


def test_undecodable_token_file_raises(tmp_path):
    path = write(tmp_path, BUTTONS)
    (tmp_path / "token").write_bytes(b"mt_\xff\xfe")
    with pytest.raises(ConfigError) as e:
        load_config(path)
    assert "xff" not in str(e.value)


@pytest.mark.parametrize(
    "url",
    ["http://example.test", "ftp://x", "example.test", "http://localhost.evil.com"],
)
def test_insecure_site_url_rejected(tmp_path, url):
    path = write(tmp_path, BUTTONS)
    path.write_text(path.read_text().replace("https://example.test", url))
    with pytest.raises(ConfigError, match="site_url"):
        load_config(path)


@pytest.mark.parametrize(
    "url", ["http://localhost:8080", "http://127.0.0.1:5000", "http://[::1]:80"]
)
def test_loopback_http_allowed(tmp_path, url):
    path = write(tmp_path, BUTTONS)
    path.write_text(path.read_text().replace("https://example.test", url))
    assert load_config(path).site_url == url


@pytest.mark.parametrize(
    "line",
    [
        "site_timeout_s = 0",
        "site_timeout_s = true",
        'site_timeout_s = "5"',
        "print_timeout_s = -1",
    ],
)
def test_bad_timeouts_rejected(tmp_path, line):
    with pytest.raises(ConfigError, match="_s"):
        load_config(write(tmp_path, line + "\n" + BUTTONS))


@pytest.mark.parametrize("bad", ["true", "-1", "1.5", '"17"'])
def test_bad_pin_rejected(tmp_path, bad):
    with pytest.raises(ConfigError, match="pin"):
        load_config(
            write(tmp_path, BUTTONS.replace("button_pin = 17", f"button_pin = {bad}"))
        )


def test_placeholder_child_id_is_rejected_naming_kid(tmp_path):
    body = BUTTONS.replace('"c2"', '"REPLACE-WITH-SUDO-CHILD-ID"')
    cfg = load_config(write(tmp_path, body))

    with pytest.raises(ConfigError, match="child_id for Sudo.*children"):
        check_child_ids(cfg)


def test_real_child_ids_pass_check(tmp_path):
    check_child_ids(load_config(write(tmp_path, BUTTONS)))


def test_example_config_placeholders_start_with_replace():
    example = Path(__file__).parents[1] / "config.example.toml"
    ids = [
        line.split("=", 1)[1].strip().strip('"')
        for line in example.read_text().splitlines()
        if line.startswith("child_id")
    ]
    assert ids and all(i.startswith("REPLACE-") for i in ids)
