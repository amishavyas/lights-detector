import time
import requests

from analyze_aurora import hemispheric_power_above_threshold
from settings_store import load_settings

NTFY_TOPIC = "WEE_WOO"
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"

CHECK_INTERVAL_SECONDS = 60 * 5
ALERT_COOLDOWN_SECONDS = 60 * 60 * 2

HP_WARNING_THRESHOLD = 40
HP_HIGH_THRESHOLD = 50


last_alert_times = {
    "elevated": None,
    "high": None,
}


def send_alarm(
    message="Manual test alarm",
    title="GO MARMOT MODE!",
    priority=5,
    tags="rotating_light",
):
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


def monitor_aurora():
    """
    Continuously monitor hemispheric power.

    Thresholds and enabled/disabled states are loaded from
    Firebase each monitoring cycle.
    """

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
                f"Hemispheric Power: {hp} GW | "
                f"Elevated: {elevated_threshold} GW | "
                f"High: {high_threshold} GW"
            )

            if (
                settings.get("high_alert_enabled", True)
                and hp >= high_threshold
            ):
                if cooldown_expired("high", now):
                    send_alarm(
                        title="STRONG AURORA ACTIVITY",
                        message=(
                            f"Hemispheric Power has reached "
                            f"{hp} GW "
                            f"(≥ {high_threshold} GW)."
                        ),
                        priority=5,
                        tags="rotating_light",
                    )

                    last_alert_times["high"] = now

            elif (
                settings.get(
                    "elevated_alert_enabled",
                    True,
                )
                and hp >= elevated_threshold
            ):
                if cooldown_expired("elevated", now):
                    send_alarm(
                        title="AURORA ACTIVITY ELEVATED",
                        message=(
                            f"Hemispheric Power has reached "
                            f"{hp} GW "
                            f"(≥ {elevated_threshold} GW)."
                        ),
                        priority=5,
                        tags="rotating_light",
                    )

                    last_alert_times["elevated"] = now

        except Exception as exc:
            print(f"Aurora monitor error: {exc}")

        time.sleep(CHECK_INTERVAL_SECONDS)
