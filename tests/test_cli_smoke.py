import subprocess
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
MAIN_CLI = PROJECT_DIR / "main_cli.py"


def test_cli_help_works():
    r = subprocess.run([sys.executable, str(MAIN_CLI), "--help"], capture_output=True, text=True)
    assert r.returncode == 0
    assert "--list-profiles" in r.stdout


def test_cli_list_profiles_works():
    r = subprocess.run([sys.executable, str(MAIN_CLI), "--list-profiles"], capture_output=True, text=True)
    assert r.returncode == 0
    assert "pylon_lv_rs485" in r.stdout
