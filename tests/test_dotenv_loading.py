"""``.env`` must be loaded before any module reads configuration at import."""

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

PROBE = """
import os
import dotenv

def fake_load_dotenv(*args, **kwargs):
    os.environ.setdefault("GOOGLE_CLIENT_ID", "from-dotenv")
    os.environ.setdefault("TEST_BYPASS_KEY", "bypass-from-dotenv")
    return True

dotenv.load_dotenv = fake_load_dotenv

import src
from src import config
from src.routes import auth

print(config.OAUTH_PROVIDERS["google"]["client_id"])
print(auth.TEST_BYPASS_KEY)
"""


def test_dotenv_values_reach_import_time_config():
    env = {
        k: v
        for k, v in os.environ.items()
        if k not in ("GOOGLE_CLIENT_ID", "TEST_BYPASS_KEY")
    }

    result = subprocess.run(
        [sys.executable, "-c", PROBE],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stdout.split() == ["from-dotenv", "bypass-from-dotenv"]
