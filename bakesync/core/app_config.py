"""Loads secrets (e.g. SMTP credentials) from environment variables or an
untracked config.local.json next to the app. Nothing secret lives in source."""
import json
import os

from bakesync.paths import CONFIG_FILE


def _load_file():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def get_setting(name, default=""):
    """Environment variable wins, then config.local.json, then `default`."""
    value = os.environ.get(name)
    if value:
        return value
    return str(_load_file().get(name, default) or default)
