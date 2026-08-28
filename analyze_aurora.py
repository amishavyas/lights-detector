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


BZ_THRESHOLD = -5.0
BZ_SUSTAINED_MINUTES = 15
MIN_BZ_SAMPLES = 15

# Store (timestamp, bz)
bz_history = deque()


def get_bz():
    """Return the most recent valid Bz value in nT from source SOLAR1."""
    data = _get_json(MAG_URL)

    for row in data:  # newest-first
        if row.get("source") != "SOLAR1":
            continue

        value = row.get("bz_gsm")
        if value is None:
            continue

        try:
            return float(value)
        except (TypeError, ValueError):
            continue

    return None


def evaluate_sustained_negative_bz(
    threshold=BZ_THRESHOLD,
    minutes=BZ_SUSTAINED_MINUTES,
    min_samples=MIN_BZ_SAMPLES,
):
    """
    Return True when Bz has stayed <= threshold
    for the entire requested duration.
    """

    bz = get_bz()

    if bz is None:
        return False

    now = time.time()
    cutoff = now - (minutes * 60)

    bz_history.append((now, bz))

    # Keep one sample immediately before the cutoff.
    while (
        len(bz_history) > 1
        and bz_history[1][0] <= cutoff
    ):
        bz_history.popleft()

    # Need enough samples.
    if len(bz_history) < min_samples:
        return False

    # Need history covering the full 15-minute window.
    if bz_history[0][0] > cutoff:
        return False

    # Every reading in the window must be <= -5 nT.
    for timestamp, value in bz_history:
        if value > threshold:
            return False

    return True


