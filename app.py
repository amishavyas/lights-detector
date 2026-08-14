import os

from flask import Flask, jsonify, render_template
import requests
from threading import Thread
from aurora_data import (
    get_hemispheric_power,
    get_bz,
    get_bt,
    get_solar_wind_speed,
    get_proton_density,
)

from alerts import monitor_aurora 

app = Flask(__name__, static_folder="static")

NTFY_TOPIC = "WEE_WOO"
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"


@app.route("/")
def index():
    boosts_folder = os.path.join(app.static_folder, "boosts")

    boosts = []

    if os.path.isdir(boosts_folder):
        for filename in os.listdir(boosts_folder):
            if filename.lower().endswith(
                (".png", ".jpg", ".jpeg", ".gif", ".webp")
            ):
                boosts.append(filename)

    boosts.sort()

    print("BOOSTS FOUND:", boosts)

    return render_template("index.html", boosts=boosts)


@app.route("/api/test-alarm", methods=["POST"])
def test_alarm():
    try:
        send_alarm()

        return jsonify({
            "success": True,
            "message": "Notification sent",
        })

    except Exception as exc:
        return jsonify({
            "success": False,
            "error": str(exc),
        }), 500


@app.route("/api/aurora-status")
def aurora_status():
    try:
        return jsonify({
            "hemispheric_power": get_hemispheric_power("north"),
            "bz": get_bz(),
            "solar_wind_speed": get_solar_wind_speed(),
            "proton_density": get_proton_density(),
        })

    except Exception as exc:
        return jsonify({
            "error": str(exc),
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False,
    )
