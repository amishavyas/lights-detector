# Aurora Alarm Test

A minimal Flask + JavaScript test app that sends an urgent phone notification through ntfy.sh.

## 1. Phone setup

Install the ntfy app and subscribe to a unique topic.

## 2. Configure the topic

Open `app.py` and replace:

    CHANGE-ME-TO-A-UNIQUE-TOPIC

with the exact topic you subscribed to.

Alternatively, set the `NTFY_TOPIC` environment variable.

## 3. Install and run

    python -m venv venv

Activate the virtual environment, then:

    pip install -r requirements.txt
    python app.py

Open:

    http://localhost:5000

Press **Test Phone Alarm**.

## Next step

Once the notification path works, detector logic can call `send_alarm()` automatically when aurora conditions are detected.
# lights-detector
