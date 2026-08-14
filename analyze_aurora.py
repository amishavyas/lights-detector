import numpy as np
from scipy.stats import linregress
import time
from collections import deque

from aurora_data import (
    get_hemispheric_power,
    get_bz,
    get_bt,
    get_solar_wind_speed,
    get_proton_density,
)


HP_THRESHOLD = 30

def hemispheric_power_above_threshold(
    threshold=HP_THRESHOLD,
):
    """
    Return True if the current hemispheric power is greater than
    the specified threshold, otherwise return False.
    """

    hp = get_hemispheric_power()

    if hp is None:
        return False

    return hp, hp >= threshold



MIN_BZ_SAMPLES = 5
BZ_THRESHOLD = -5.0
BZ_TREND_WINDOW_MINUTES = 5

# Store (timestamp, bz)
bz_history = deque()

def evaluate_bz_state_derivative(
    bz,
    minutes=BZ_TREND_WINDOW_MINUTES,
    derivative_threshold=0.5,
    min_samples=MIN_BZ_SAMPLES,
):
    """
    Evaluate the mean Bz rate of change over BZ_DURATION_MINUTES.

    Rate is measured in nT/min.

    Returns:
        "INSUFFICIENT_DATA"
        "TRENDING_NEGATIVE"
        "STABLE"
        "TRENDING_POSITIVE"
    """

    if bz is None:
        return "INSUFFICIENT_DATA"

    now = time.time()
    cutoff = now - (minutes * 60)

    bz_history.append((now, bz))

    # Keep one sample immediately before the start
    # of the requested duration.
    while (
        len(bz_history) > 1
        and bz_history[1][0] <= cutoff
    ):
        bz_history.popleft()

    if len(bz_history) < min_samples:
        return "INSUFFICIENT_DATA"

    # Make sure history covers the full duration.
    if bz_history[0][0] > cutoff:
        return "INSUFFICIENT_DATA"

    start_time, start_bz = bz_history[0]
    end_time, end_bz = bz_history[-1]

    elapsed_minutes = (end_time - start_time) / 60

    if elapsed_minutes <= 0:
        return "INSUFFICIENT_DATA"

    # Mean rate of change over the entire duration.
    mean_rate = (end_bz - start_bz) / elapsed_minutes

    print(f"Bz mean rate: {mean_rate:.2f} nT/min")

    if mean_rate <= -derivative_threshold:
        return "TRENDING_NEGATIVE"

    if mean_rate >= derivative_threshold:
        return "TRENDING_POSITIVE"

    return "STABLE"


if __name__ == "__main__":
    bz_history.clear()

    test_values = [
        -2.0,
        -3.0,
        -4.0,
        -5.0,
        -6.0,
        -7.0,
        -8.0,
        -9.0,
        -10,
        -11,
        -130
    ]

    for bz in test_values:
        state = evaluate_bz_state_derivative(
            bz,
            minutes=5 / 60,   # 5 seconds
            min_samples=5,
        )

        print(f"Bz: {bz:5.1f} | State: {state}")
        time.sleep(1)
