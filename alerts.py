import time
from collections import deque
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

from analyze_aurora import hemispheric_power_above_threshold
from settings_store import load_settings
from aurora_data import get_bz


NTFY_TOPIC = "WEE_WOO"
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"

CHECK_INTERVAL_SECONDS = 60 * 5
ALERT_COOLDOWN_SECONDS = 60 * 60 * 2

HP_WARNING_THRESHOLD = 40
HP_HIGH_THRESHOLD = 50

BZ_THRESHOLD = -1.0
BZ_SUSTAINED_MINUTES = 15
BZ_MIN_SAMPLES = 4

EASTERN_TZ = ZoneInfo("America/New_York")

bz_history = deque()

last_alert_times = {
    "elevated": None,
    "high": None,
    "bz_sustained": None,
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

    if start > stop:
        return current >= start or current < stop

    return start <= current < stop


def get_thresholds(settings):
    elevated = float(
        settings.get(
            "elevated_threshold",
            HP_WARNING_THRESHOLD,
        )
    )

    high = float(
        settings.get(
            "high_threshold",
            HP_HIGH_THRESHOLD,
        )
    )

    return elevated, high


def sustained_negative_bz(
    bz,
    now,
    threshold=BZ_THRESHOLD,
    minutes=BZ_SUSTAINED_MINUTES,
    min_samples=BZ_MIN_SAMPLES,
):
    """
    Return True when Bz has stayed at or below
    the threshold for the full requested duration.
    """

    if bz is None:
        return False

    cutoff = now - (minutes * 60)

    bz_history.append((now, bz))

    # Keep one sample immediately before the cutoff.
    while (
        len(bz_history) > 1
        and bz_history[1][0] <= cutoff
    ):
        bz_history.popleft()

    if len(bz_history) < min_samples:
        return False

    # History must cover the full 15-minute window.
    if bz_history[0][0] > cutoff:
        return False

    return all(
        value <= threshold
        for _, value in bz_history
    )


def check_bz_alert(
    settings,
    bz,
    bz_sustained,
    now,
):
    if not settings.get("bz_alert_enabled", True):
        return

    if not bz_sustained:
        return

    if not cooldown_expired("bz_sustained", now):
        return

    send_alarm(
        title="SUSTAINED SOUTHWARD Bz",
        message=(
            f"Bz has remained at or below "
            f"{BZ_THRESHOLD:.1f} nT for at least "
            f"{BZ_SUSTAINED_MINUTES} minutes. "
            f"Current Bz: {bz:.1f} nT."
        ),
    )

    last_alert_times["bz_sustained"] = now


def check_hp_alerts(
    settings,
    hp,
    elevated_threshold,
    high_threshold,
    now,
):
    if (
        settings.get("high_alert_enabled", True)
        and hp >= high_threshold
        and cooldown_expired("high", now)
    ):
        send_alarm(
            title="STRONG AURORA ACTIVITY",
            message=(
                f"Hemispheric Power has reached "
                f"{hp:.1f} GW."
            ),
        )

        last_alert_times["high"] = now
        return

    if (
        settings.get("elevated_alert_enabled", True)
        and hp >= elevated_threshold
        and cooldown_expired("elevated", now)
    ):
        send_alarm(
            title="AURORA ACTIVITY ELEVATED",
            message=(
                f"Hemispheric Power has reached "
                f"{hp:.1f} GW."
            ),
        )

        last_alert_times["elevated"] = now


def print_status(
    hp,
    bz,
    bz_sustained,
    alerts_on,
):
    bz_display = (
        f"{bz:.1f}"
        if bz is not None
        else "N/A"
    )

    print(
        f"HP: {hp:.1f} GW | "
        f"Bz: {bz_display} nT | "
        f"Bz sustained: {bz_sustained} | "
        f"Alerts: {'ON' if alerts_on else 'OFF'}"
    )


def monitor_aurora():
    while True:
        try:
            settings = load_settings()
            now = time.time()

            elevated_threshold, high_threshold = get_thresholds(
                settings
            )

            hp, _ = hemispheric_power_above_threshold(
                elevated_threshold
            )

            hp = float(hp)
            bz = get_bz()

            bz_sustained = sustained_negative_bz(
                bz,
                now,
            )

            alerts_on = alerts_allowed_now(settings)

            print_status(
                hp,
                bz,
                bz_sustained,
                alerts_on,
            )

            if alerts_on:
                check_bz_alert(
                    settings,
                    bz,
                    bz_sustained,
                    now,
                )

                check_hp_alerts(
                    settings,
                    hp,
                    elevated_threshold,
                    high_threshold,
                    now,
                )

        except Exception as exc:
            print(f"Aurora monitor error: {exc}")

        time.sleep(CHECK_INTERVAL_SECONDS)
