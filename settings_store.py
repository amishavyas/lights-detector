import os
import requests
from datetime import datetime, timezone

FIREBASE_URL = os.environ.get("FIREBASE_DB_URL")
FIREBASE_SECRET = os.environ.get("FIREBASE_DB_SECRET")

DEFAULT_SETTINGS = {
    "elevated_alert_enabled": True,
    "high_alert_enabled": True,
    "bz_alert_enabled": True,

    "elevated_threshold": 40,
    "high_threshold": 50,

    "bz_threshold": -1.0,
    "bz_sustained_minutes": 15,
    "bz_min_samples": 4,

    "alert_start_time": "20:00",
    "alert_stop_time": "04:00",

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
            return DEFAULT_SETTINGS.copy()

        return {
            **DEFAULT_SETTINGS,
            **data,
        }

    except Exception as exc:
        print(
            f"Failed to load settings, "
            f"using defaults: {exc}"
        )
        return DEFAULT_SETTINGS.copy()


def save_settings(settings, updated_by=None):
    settings = settings.copy()

    settings["last_updated"] = (
        datetime.now(timezone.utc).isoformat()
    )
    settings["updated_by"] = (
        updated_by or "anonymous"
    )

    response = requests.put(
        f"{FIREBASE_URL}/settings.json",
        params={"auth": FIREBASE_SECRET},
        json=settings,
        timeout=10,
    )

    response.raise_for_status()

    return settings
