from garminconnect import Garmin
from datetime import datetime, timedelta
import json
import os

# === Auth with base64 token
TOKENSTORE = os.path.expanduser("~/.garminconnect")
client = Garmin()
client.login(tokenstore=TOKENSTORE)

# === Pick date (yesterday if before 6AM)
date_str = "2025-03-27"

# === Fetch helpers
def try_fetch(fetcher, fallback):
    try:
        return fetcher()
    except Exception as e:
        print(f"⚠️  Could not fetch {fetcher.__name__}: {e}")
        return fallback

# === Fetch wellness data
steps = try_fetch(lambda: client.get_steps_data(date_str), [])
sleep = try_fetch(lambda: client.get_sleep_data(date_str), {})
rhr = try_fetch(lambda: client.get_rhr_day(date_str), {})
bb = try_fetch(lambda: client.get_body_battery(date_str), [])
activity = try_fetch(lambda: client.get_activities(0, 1), [])

# === Build export
export = {
    "steps": {
        "totalSteps": steps[0].get("steps", 0) if steps else 0,
        "dailyStepGoal": steps[0].get("dailyStepGoal", 10000) if steps else 10000
    },
    "sleep": {
        "sleepTimeSeconds": sleep.get("sleepTimeSeconds", 0),
        "deepSleepSeconds": sleep.get("deepSleepSeconds", 0),
        "lightSleepSeconds": sleep.get("lightSleepSeconds", 0),
        "remSleepSeconds": sleep.get("remSleepSeconds", 0),
        "awakeSleepSeconds": sleep.get("awakeSleepSeconds", 0)
    },
    "rhr": {
        "restingHeartRate": rhr.get("restingHeartRate", 0)
    },
    "body_battery": bb,  # This is raw, useful for advanced summaries
    "workout": [
        {
            "activityName": act.get("activityName"),
            "startTimeLocal": act.get("startTimeLocal"),
            "duration": act.get("duration"),
            "distance": act.get("distance"),
            "calories": act.get("calories")
        }
        for act in activity
    ]
}

# === Save export
with open("garmin_export.json", "w") as f:
    json.dump(export, f, indent=2)

print(f"✅ Garmin data exported to garmin_export.json for {date_str}")
