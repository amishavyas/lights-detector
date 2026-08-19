import os

from flask import Flask, jsonify, render_template, request

from aurora_data import (
    get_hemispheric_power,
    get_bz,
    get_solar_wind_speed,
    get_proton_density,
)
from alerts import send_alarm
from settings_store import load_settings, save_settings


app = Flask(__name__, static_folder="static")

ALERT_CONFIG_PASSWORD = os.environ.get("ALERT_CONFIG_PASSWORD")


@app.route("/")
def index():
    boosts_folder = os.path.join(app.static_folder, "boosts")
    boosts = []

    if os.path.isdir(boosts_folder):
        boosts = [
            filename
            for filename in os.listdir(boosts_folder)
            if filename.lower().endswith(
                (".png", ".jpg", ".jpeg", ".gif", ".webp")
            )
        ]

    boosts.sort()

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
        return jsonify({"error": str(exc)}), 500


@app.route("/api/settings", methods=["GET"])
def get_settings():
    return jsonify(load_settings())


@app.route("/api/settings", methods=["POST"])
def update_settings():
    data = request.get_json()

    if not ALERT_CONFIG_PASSWORD:
        return jsonify({
            "error": "Settings password is not configured"
        }), 500

    if data.get("password") != ALERT_CONFIG_PASSWORD:
        return jsonify({"error": "Incorrect password"}), 403

    settings = load_settings()

    try:
        settings["elevated_alert_enabled"] = data[
            "elevated_alert_enabled"
        ]
        settings["high_alert_enabled"] = data[
            "high_alert_enabled"
        ]

        settings["elevated_threshold"] = float(
            data["elevated_threshold"]
        )
        settings["high_threshold"] = float(
            data["high_threshold"]
        )

    except (KeyError, TypeError, ValueError):
        return jsonify({
            "error": "Invalid settings"
        }), 400

    if settings["high_threshold"] <= settings["elevated_threshold"]:
        return jsonify({
            "error": "Strong threshold must be higher than warning threshold"
        }), 400

    updated_by = data.get("updated_by", "").strip() or "anonymous"

    settings = save_settings(
        settings,
        updated_by=updated_by,
    )

    return jsonify(settings)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False,
    )
