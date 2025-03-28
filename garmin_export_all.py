from garminconnect import Garmin
from datetime import datetime, timedelta
import json
import os
import statistics

# === Auth
TOKENSTORE = os.path.expanduser("~/.garminconnect")
client = Garmin()
client.login(tokenstore=TOKENSTORE)

# === Define Dates
now = datetime.now()
yesterday = now - timedelta(days=1)
date_str = yesterday.strftime("%Y-%m-%d")
sleep_start = (yesterday.replace(hour=20, minute=0)).isoformat()
sleep_end = now.isoformat()

# === Safe fetch wrapper
def try_fetch(fetcher, fallback):
    try:
        return fetcher()
    except Exception as e:
        print(f"⚠️ Could not fetch {fetcher.__name__}: {e}")
        return fallback

# === Helpers
def average_movement(movements):
    if not movements:
        return 0
    return round(statistics.mean([m.get("activityLevel", 0) for m in movements]), 2)

def summarize_heart_rate(raw_values):
    if not raw_values:
        return {"min": None, "max": None, "average": None}

    bpm_values = [val[1] for val in raw_values if isinstance(val, list) and len(val) == 2]
    return {
        "min": min(bpm_values),
        "max": max(bpm_values),
        "average": round(sum(bpm_values) / len(bpm_values), 1)
    }

def summarize_hr(hr_list):
    values = [v[1] for v in hr_list if isinstance(v, list) and len(v) == 2]
    return {
        "min": min(values) if values else 0,
        "max": max(values) if values else 0,
        "avg": round(statistics.mean(values), 2) if values else 0
    }

# === Data collectors
steps_data = try_fetch(lambda: client.get_steps_data(date_str), [])
sleep_data = try_fetch(lambda: client.get_sleep_data(date_str), {})
rhr_data = try_fetch(lambda: client.get_rhr_day(date_str), {})
body_battery_data = try_fetch(lambda: client.get_body_battery(date_str), [])
activities = try_fetch(lambda: client.get_activities_by_date(date_str, date_str), [])

heart_rates_day = try_fetch(lambda: client.get_heart_rates(date_str), [])
heart_rates_sleep = try_fetch(lambda: client.get_heart_rates(sleep_start, sleep_end), [])
stress_data = try_fetch(lambda: client.get_stress_data(date_str), [])
respiration_data = try_fetch(lambda: client.get_respiration_data(date_str), [])
hydration_data = try_fetch(lambda: client.get_hydration_data(date_str), {})
training_readiness = try_fetch(lambda: client.get_training_readiness(date_str), {})
spo2_data = try_fetch(lambda: client.get_spo2_data(date_str), {})
calories_data = try_fetch(lambda: client.get_stats(date_str), {})
today_activities = try_fetch(lambda: client.get_activities_by_date(now.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d")), [])

# === Filter early activities
early_activities = [
    act for act in today_activities
    if act.get("startTimeLocal") and datetime.fromisoformat(act["startTimeLocal"]) < now.replace(hour=7, minute=45)
]

# === Final JSON export
export = {
    "date": date_str,
    "steps": {
        "totalSteps": steps_data[0].get("steps", 0) if steps_data else 0,
        "dailyStepGoal": steps_data[0].get("dailyStepGoal", 10000) if steps_data else 10000
    },
    "sleep": {
        "dailySleepDTO": sleep_data.get("dailySleepDTO", {}),
        "sleepMovementAvg": average_movement(sleep_data.get("sleepMovement", [])),
        "sleepHeartRateSummary": summarize_hr(sleep_data.get("sleepHeartRate", []))
    },
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
    "heart_rate_day": summarize_heart_rate(heart_rates_day),,
    "heart_rate_sleep_summary": summarize_hr(heart_rates_sleep),
    "stress": stress_data,
    "respiration": respiration_data,
    "hydration": hydration_data,
    "spo2": spo2_data,
    "training_readiness": training_readiness,
    "calories": calories_data,
    "early_activities_today": early_activities
}

# === Save to file
os.makedirs("garmin_export", exist_ok=True)
with open("garmin_export_all.json", "w") as f:
    json.dump(export, f, indent=2)

per_day_file = f"garmin_export/{date_str}.json"
with open(per_day_file, "w") as f:
    json.dump(export, f, indent=2)

print(f"✅ Full Garmin data exported to garmin_export_all.json for {date_str}")
print(f"✅ Per-day file also saved to {per_day_file}")
