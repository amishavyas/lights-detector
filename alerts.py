import time
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

from analyze_aurora import hemispheric_power_above_threshold
from settings_store import load_settings


NTFY_TOPIC = "WEE_WOO"
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"

CHECK_INTERVAL_SECONDS = 60 * 5
ALERT_COOLDOWN_SECONDS = 60 * 60 * 2

HP_WARNING_THRESHOLD = 40
HP_HIGH_THRESHOLD = 50

EASTERN_TZ = ZoneInfo("America/New_York")


last_alert_times = {
    "elevated": None,
    "high": None,
}


def send_alarm(message, title, priority=5, tags="rotating_light"):
    response = requests.put(
        NTFY_URL,
        data=message.encode("utf-8"),
        headers={
            "Title": title,
            "Priority": str(priority),
            "Tags": tags,
        },
        timeout=30,
    )

    response.raise_for_status()


def cooldown_expired(alert_level, now):
    last_alert = last_alert_times[alert_level]

    return (
        last_alert is None
        or now - last_alert >= ALERT_COOLDOWN_SECONDS
    )


def alerts_allowed_now(settings):
    start = settings.get("alert_start_time", "20:00")
    stop = settings.get("alert_stop_time", "04:00")

    current = datetime.now(EASTERN_TZ).strftime("%H:%M")

    # Handles windows that cross midnight,
    # like 20:00 -> 04:00
    if start > stop:
        return current >= start or current < stop

    return start <= current < stop


def monitor_aurora():
    while True:
        try:
            settings = load_settings()

            elevated_threshold = float(
                settings.get(
                    "elevated_threshold",
                    HP_WARNING_THRESHOLD,
                )
            )

            high_threshold = float(
                settings.get(
                    "high_threshold",
                    HP_HIGH_THRESHOLD,
                )
            )

            hp, _ = hemispheric_power_above_threshold(
                elevated_threshold
            )

            hp = float(hp)
            now = time.time()

            print(
                f"HP: {hp} GW | "
                f"Alerts: "
                f"{'ON' if alerts_allowed_now(settings) else 'OFF'}"
            )

            if not alerts_allowed_now(settings):
                time.sleep(CHECK_INTERVAL_SECONDS)
                continue

            if (
                settings.get("high_alert_enabled", True)
                and hp >= high_threshold
                and cooldown_expired("high", now)
            ):
                send_alarm(
                    title="STRONG AURORA ACTIVITY",
                    message=(
                        f"Hemispheric Power has reached "
                        f"{hp} GW."
                    ),
                )

                last_alert_times["high"] = now

            elif (
                settings.get("elevated_alert_enabled", True)
                and hp >= elevated_threshold
                and cooldown_expired("elevated", now)
            ):
                send_alarm(
                    title="AURORA ACTIVITY ELEVATED",
                    message=(
                        f"Hemispheric Power has reached "
                        f"{hp} GW."
                    ),
                )

                last_alert_times["elevated"] = now

        except Exception as exc:
            print(f"Aurora monitor error: {exc}")

        time.sleep(CHECK_INTERVAL_SECONDS)
