import requests

MAG_URL = "https://services.swpc.noaa.gov/json/rtsw/rtsw_mag_1m.json"
PLASMA_URL = "https://services.swpc.noaa.gov/json/rtsw/rtsw_wind_1m.json"
HP_URL = "https://services.swpc.noaa.gov/text/aurora-nowcast-hemi-power.txt"

TIMEOUT = 10


def _get_json(url):
    """Fetch a NOAA endpoint and return the JSON response."""
    response = requests.get(url, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def _get_text(url):
    """Fetch a NOAA endpoint and return the response as text."""
    response = requests.get(url, timeout=TIMEOUT)
    response.raise_for_status()
    return response.text


def get_bz():
    """Return the most recent valid Bz value in nT."""
    data = _get_json(MAG_URL)
    for row in reversed(data):
        value = row.get("bz_gsm")

        if value is None:
            continue

        try:
            return float(value)
        except (TypeError, ValueError):
            continue

    return None


def get_bt():
    """Return the most recent valid total IMF strength (Bt) in nT."""
    data = _get_json(MAG_URL)

    for row in reversed(data):
        value = row.get("bt")

        if value is None:
            continue

        try:
            return float(value)
        except (TypeError, ValueError):
            continue

    return None


def get_solar_wind_speed():
    """Return the most recent valid proton speed in km/s."""
    data = _get_json(PLASMA_URL)

    for row in reversed(data):
        value = row.get("proton_speed")

        if value is None:
            continue

        try:
            return float(value)
        except (TypeError, ValueError):
            continue

    return None


def get_proton_density():
    """Return the most recent valid proton density in particles/cm³."""
    data = _get_json(PLASMA_URL)

    for row in data:
        if not row.get("active"):
            continue

        value = row.get("proton_density")

        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                continue

    return None


def get_hemispheric_power(hemisphere="north"):
    """Return the latest northern or southern hemispheric power in GW."""
    if hemisphere not in ("north", "south"):
        raise ValueError("hemisphere must be 'north' or 'south'")

    text = _get_text(HP_URL)
    rows = []

    for line in text.splitlines():
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        numbers = []

        for item in line.split():
            try:
                numbers.append(float(item))
            except ValueError:
                continue

        if len(numbers) >= 2:
            rows.append(numbers)

    if not rows:
        return None

    latest = rows[-1]

    if hemisphere == "north":
        return latest[-2]

    return latest[-1]
