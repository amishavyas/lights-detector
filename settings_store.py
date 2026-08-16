import os
import requests
from datetime import datetime, timezone

FIREBASE_URL = os.environ.get("FIREBASE_DB_URL")
FIREBASE_SECRET = os.environ.get("FIREBASE_DB_SECRET")

DEFAULT_SETTINGS = {
    "elevated_alert_enabled": True,
    "high_alert_enabled": True,
    "elevated_threshold": 40,
    "high_threshold": 50,
    "last_updated": None,
    "updated_by": None,
}


def load_settings():
    try:
        response = requests.get(
            f"{FIREBASE_URL}/settings.json",
            params={"auth": FIREBASE_SECRET},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        if not data:
            return DEFAULT_SETTINGS
        # Fill in any missing keys with defaults (handles old data / new fields)
        merged = {**DEFAULT_SETTINGS, **data}
        return merged
    except Exception as exc:
        print(f"Failed to load settings, using defaults: {exc}")
        return DEFAULT_SETTINGS


def save_settings(settings, updated_by=None):
    settings["last_updated"] = datetime.now(timezone.utc).isoformat()
    settings["updated_by"] = updated_by or "anonymous"

    requests.put(
        f"{FIREBASE_URL}/settings.json",
        params={"auth": FIREBASE_SECRET},
        json=settings,
        timeout=10,
    )
    return settings
