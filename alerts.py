import time
import requests

from analyze_aurora import hemispheric_power_above_threshold

NTFY_TOPIC = "WEE_WOO"
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"


# Monitoring
CHECK_INTERVAL_SECONDS = 60 * 5
ALERT_COOLDOWN_SECONDS = 60 * 60 * 2  # 2 hours

HP_WARNING_THRESHOLD = 40
HP_HIGH_THRESHOLD = 50


last_alert_times = {
    40: None,
    50: None,
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


def cooldown_expired(threshold, now):
    last_alert = last_alert_times[threshold]

    return (
        last_alert is None
        or now - last_alert >= ALERT_COOLDOWN_SECONDS
    )


def monitor_aurora():
    """
    Continuously monitor hemispheric power.

    Alert levels:
      >= 40 GW: elevated aurora activity
      >= 50 GW: strong aurora activity

    Each alert level has its own 2-hour cooldown.
    """

    while True:
        hp, _ = hemispheric_power_above_threshold(
            HP_WARNING_THRESHOLD
        )

        now = time.time()

        print(f"Hemispheric Power: {hp} GW")

        # Strong alert
        if hp >= HP_HIGH_THRESHOLD:

            if cooldown_expired(HP_HIGH_THRESHOLD, now):
                send_alarm(
                    title="STRONG AURORA ACTIVITY",
                    message=(
                        f"Hemispheric Power has reached "
                        f"{hp} GW (≥ {HP_HIGH_THRESHOLD} GW)."
                    ),
                    priority=5,
                    tags="rotating_light",
                )

                last_alert_times[HP_HIGH_THRESHOLD] = now

        # Elevated alert
        elif hp >= HP_WARNING_THRESHOLD:

            if cooldown_expired(HP_WARNING_THRESHOLD, now):
                send_alarm(
                    title="AURORA ACTIVITY ELEVATED",
                    message=(
                        f"Hemispheric Power has reached "
                        f"{hp} GW (≥ {HP_WARNING_THRESHOLD} GW)."
                    ),
                    priority=5,
                    tags="rotating_light",
                )

                last_alert_times[HP_WARNING_THRESHOLD] = now

        time.sleep(CHECK_INTERVAL_SECONDS)
