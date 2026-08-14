import time
from analyze_aurora import hemispheric_power_above_threshold


CHECK_INTERVAL_SECONDS = 60 * 5
HP_ALERT_THRESHOLD = 50
ALERT_COOLDOWN_SECONDS = 60 * 60 * 2  # 2 hours

last_alert_time = None


def send_alarm(
    message="Manual test alarm",
    title="GO MARMOT MODE!",
    priority=5,
    tags="rotating_light",
):
    """
    Send a Northern Lights alert through ntfy.
    """

    response = requests.put(
        NTFY_URL,
        headers={
            "Title": title,
            "Priority": str(priority),
            "Tags": tags,
            "Message": message,
        },
        timeout=30,
    )

    response.raise_for_status()


def monitor_aurora():
    """
    Continuously monitor aurora conditions.

    Hemispheric power is checked every five minutes.
    An alert is sent when HP exceeds the specified threshold
    and the alert cooldown has expired.
    """

    last_alert_time = None

    while True:
        hp, hp_status = hemispheric_power_above_threshold(
            HP_ALERT_THRESHOLD
        )

        now = time.time()

        print(
            f"HP ({hp}) is above {HP_ALERT_THRESHOLD} GW: "
            f"{hp_status}"
        )

        if hp_status:
            cooldown_expired = (
                last_alert_time is None
                or now - last_alert_time >= ALERT_COOLDOWN_SECONDS
            )

            if cooldown_expired:
                send_alarm(
                    message=(
                        f"Hemispheric power is above "
                        f"{HP_ALERT_THRESHOLD} GW!"
                    )
                )

                last_alert_time = now

        time.sleep(CHECK_INTERVAL_SECONDS)
