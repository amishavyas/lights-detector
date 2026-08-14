import os

from flask import Flask, jsonify, render_template
import requests

from aurora_data import (
    get_hemispheric_power,
    get_bz,
    get_bt,
    get_solar_wind_speed,
    get_proton_density,
)


app = Flask(__name__, static_folder="static")

NTFY_TOPIC = "WEE_WOO"
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"


def send_alarm():
    # with open("marmot.jpeg", "rb") as image:
    response = requests.put(
        NTFY_URL,
        # data=image,
        headers={
            "Title": "GO MARMOT MODE",
            "Priority": "5",
            "Tags": "rotating_light",
            # "Filename": "marmot.jpeg",
            "Message": "Northern lights alarm test!",
        },
        timeout=30,
    )

    response.raise_for_status()


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
    app.run(debug=True, port=5001)
