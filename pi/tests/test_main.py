import sys
from pathlib import Path

import pytest

from mathtutor_pi import main as main_mod
from mathtutor_pi.config import ButtonConfig, Config, ConfigError
from mathtutor_pi.site_client import SiteError

SECRET = "mt_supersecrettoken"


def _config() -> Config:
    return Config(
        site_url="https://example.test",
        token=SECRET,
        printer="Q",
        buttons=(
            ButtonConfig("Philip", "cid-p", 17, 27),
            ButtonConfig("Sudo", "cid-s", 22, 23),
        ),
    )


class FakeKid:
    def __init__(self, ok=True):
        self.ok = ok
        self.runs = 0

    def run_once(self):
        self.runs += 1
        return self.ok


@pytest.fixture(autouse=True)
def no_gpiozero(monkeypatch):
    monkeypatch.setitem(sys.modules, "gpiozero", None)  # import would raise


@pytest.fixture
def patched(monkeypatch):
    monkeypatch.setattr(main_mod, "load_config", lambda path: _config())
    kids = {}

    def build(config, button, light, workdir):
        kids[button.kid] = FakeKid()
        return kids[button.kid]

    monkeypatch.setattr(main_mod, "build_kid_button", build)
    return kids


def test_print_success_exit_0(patched):
    assert main_mod.main(["print", "Philip", "--config", "c.toml"]) == 0
    assert patched["Philip"].runs == 1
    assert "Sudo" not in patched


def test_print_failure_exit_1(patched, monkeypatch):
    monkeypatch.setattr(main_mod, "build_kid_button", lambda *a, **k: FakeKid(ok=False))
    assert main_mod.main(["print", "Philip", "--config", "c.toml"]) == 1


def test_print_kid_name_case_insensitive(patched):
    assert main_mod.main(["print", "philip", "--config", "c.toml"]) == 0


def test_print_unknown_kid_exit_1(patched, capsys):
    assert main_mod.main(["print", "Nobody", "--config", "c.toml"]) == 1
    err = capsys.readouterr().err
    assert "Nobody" in err and "Philip" in err and "Traceback" not in err


def test_config_error_is_one_line_exit_1(monkeypatch, capsys):
    def boom(path):
        raise ConfigError("cannot read config x")

    monkeypatch.setattr(main_mod, "load_config", boom)
    assert main_mod.main(["print", "Philip", "--config", "c.toml"]) == 1
    err = capsys.readouterr().err
    assert err.strip() == "error: cannot read config x"


def test_children_prints_name_and_id(monkeypatch, capsys):
    monkeypatch.setattr(main_mod, "load_config", lambda path: _config())

    class FakeSiteClient:
        def __init__(self, base_url, token, timeout_s):
            pass

        def children(self):
            return [{"id": "abc", "name": "Philip", "age": 8, "grade": 3}]

    monkeypatch.setattr(main_mod, "SiteClient", FakeSiteClient)

    assert main_mod.main(["children", "--config", "c.toml"]) == 0
    out = capsys.readouterr()
    assert out.out == "Philip  abc\n"
    assert SECRET not in out.out + out.err


def test_children_site_error_exit_1(monkeypatch, capsys):
    monkeypatch.setattr(main_mod, "load_config", lambda path: _config())

    class FakeSiteClient:
        def __init__(self, *a):
            pass

        def children(self):
            raise SiteError("unauthorized")

    monkeypatch.setattr(main_mod, "SiteClient", FakeSiteClient)

    assert main_mod.main(["children", "--config", "c.toml"]) == 1
    assert capsys.readouterr().err.strip() == "error: unauthorized"


def test_missing_subcommand_is_usage_error():
    with pytest.raises(SystemExit) as exc:
        main_mod.main([])
    assert exc.value.code == 2


def test_run_without_gpiozero_fails_cleanly(monkeypatch, capsys):
    monkeypatch.setattr(main_mod, "load_config", lambda path: _config())
    assert main_mod.main(["run", "--config", "c.toml"]) == 1
    assert "gpiozero" in capsys.readouterr().err


def test_console_light_logs(caplog):
    caplog.set_level("INFO", logger="mathtutor_pi")
    light = main_mod.ConsoleLight("Philip")
    light.steady()
    light.blink()
    light.flash()
    assert [r.getMessage() for r in caplog.records] == [
        "Philip light: steady",
        "Philip light: blink",
        "Philip light: flash",
    ]


def test_default_config_path_is_etc():
    assert main_mod.DEFAULT_CONFIG == Path("/etc/mathtutor-pi/config.toml")
