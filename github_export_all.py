from garminconnect import Garmin
from datetime import datetime
import json
import os

# === Auth using GitHub Secrets
email = os.environ["GARMIN_EMAIL"]
password = os.environ["GARMIN_PASSWORD"]
client = Garmin(email, password)
client.login()

# === Set date
date_str = "2025-03-28"

# === Safe fetch wrapper
def try_fetch(fetcher, fallback):
    try:
        return fetcher()
    except Exception as e:
        print(f"⚠️ Could not fetch {fetcher.__name__}: {e}")
        return fallback

# === Data collectors
steps_data = try_fetch(lambda: client.get_steps_data(date_str), [])
sleep_data = try_fetch(lambda: client.get_sleep_data(date_str), {})
rhr_data = try_fetch(lambda: client.get_rhr_day(date_str), {})
body_battery_data = try_fetch(lambda: client.get_body_battery(date_str), [])
activities = try_fetch(lambda: client.get_activities_by_date(date_str, date_str), [])

heart_rates = try_fetch(lambda: client.get_heart_rates(date_str), [])
stress_data = try_fetch(lambda: client.get_stress_data(date_str), [])
respiration_data = try_fetch(lambda: client.get_respiration_data(date_str), [])
hydration_data = try_fetch(lambda: client.get_hydration_data(date_str), {})
training_readiness = try_fetch(lambda: client.get_training_readiness(date_str), {})
spo2_data = try_fetch(lambda: client.get_spo2_data(date_str), {})
calories_data = try_fetch(lambda: client.get_stats(date_str), {})

# === Final JSON export
export = {
    "date": date_str,
    "steps": {
        "totalSteps": steps_data[0].get("steps", 0) if steps_data else 0,
        "dailyStepGoal": steps_data[0].get("dailyStepGoal", 10000) if steps_data else 10000
    },
    "sleep": sleep_data,
    "rhr": {
        "restingHeartRate": rhr_data.get("restingHeartRate", 0)
    },
    "body_battery": body_battery_data,
    "workout": [
        {
            "activityName": act.get("activityName"),
            "startTimeLocal": act.get("startTimeLocal"),
            "duration": act.get("duration"),
            "distance": act.get("distance"),
            "calories": act.get("calories")
        }
        for act in activities
    ],
    "heart_rate": heart_rates,
    "stress": stress_data,
    "respiration": respiration_data,
    "hydration": hydration_data,
    "spo2": spo2_data,
    "training_readiness": training_readiness,
    "calories": calories_data
}

# === Ensure directory exists
os.makedirs("garmin_export", exist_ok=True)

# === Save file to correct place
filename = f"garmin_export/{date_str}.json"
with open(filename, "w") as f:
    json.dump(export, f, indent=2)
print(f"✅ Full Garmin data exported to {filename} for {date_str}")
