from garminconnect import Garmin
from datetime import datetime, timedelta
import json, os, statistics

# === Auth
TOKENSTORE = os.path.expanduser("~/.garminconnect")
client = Garmin()
client.login(tokenstore=TOKENSTORE)

# === Date Setup
now = datetime.now()
yesterday = now - timedelta(days=1)
date_str = yesterday.strftime("%Y-%m-%d")
sleep_start = yesterday.replace(hour=20).isoformat()
sleep_end = now.isoformat()

# === Safe Fetch
def safe(fetch_func, default):
    try:
        return fetch_func()
    except Exception as e:
        print(f"⚠️ {fetch_func.__name__} failed: {e}")
        return default

# === Summarizers
def summarize_dict_list(data, key):
    values = [d.get(key) for d in data if d.get(key) is not None]
    return {
        "min": min(values, default=0),
        "max": max(values, default=0),
        "average": round(statistics.mean(values), 2) if values else 0
    }

def summarize_hr(hr_list):
    values = [v[1] for v in hr_list if isinstance(v, list) and len(v) == 2]
    return {
        "min": min(values, default=0),
        "max": max(values, default=0),
        "avg": round(statistics.mean(values), 2) if values else 0
    }

# === Fetch data
data = {
    "date": date_str,
    "steps": safe(lambda: client.get_steps_data(date_str), []),
    "sleep": safe(lambda: client.get_sleep_data(date_str), {}),
    "rhr": safe(lambda: client.get_rhr_day(date_str), {}),
    "hr_day": safe(lambda: client.get_heart_rates(date_str), []),
    "hr_sleep": safe(lambda: client.get_heart_rates(sleep_start, sleep_end), []),
    "activities": safe(lambda: client.get_activities_by_date(date_str, date_str), []),
    "early_today": safe(lambda: client.get_activities_by_date(now.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d")), []),
    "stress": safe(lambda: client.get_stress_data(date_str), []),
    "calories": safe(lambda: client.get_stats(date_str), {}),
    "body_battery": safe(lambda: client.get_body_battery(date_str), [])
}

# === Filter early activities
early_workouts = [
    a for a in data["early_today"]
    if a.get("startTimeLocal") and datetime.fromisoformat(a["startTimeLocal"]) < now.replace(hour=7, minute=45)
]

# === Build compact export
export = {
    "date": data["date"],
    "steps": {
        "total": data["steps"][0].get("steps", 0) if data["steps"] else 0,
        "goal": data["steps"][0].get("dailyStepGoal", 10000) if data["steps"] else 10000
    },
    "sleep_summary": {
        "duration": data["sleep"].get("dailySleepDTO", {}).get("durationInSeconds", 0),
        "efficiency": data["sleep"].get("dailySleepDTO", {}).get("sleepEfficiency", 0),
        "hr_summary": summarize_hr(data["sleep"].get("sleepHeartRate", [])),
        "movement_summary": summarize_dict_list(data["sleep"].get("sleepMovement", []), "activityLevel")
    },
    "resting_hr": data["rhr"].get("restingHeartRate", 0),
    "heart_rate_day": summarize_hr(data["hr_day"]),
    "heart_rate_sleep": summarize_hr(data["hr_sleep"]),
    "stress": summarize_dict_list(data["stress"], "stressLevel"),
    "calories": {
        "total": data["calories"].get("totalKilocalories", 0),
        "active": data["calories"].get("activeKilocalories", 0),
        "bmr": data["calories"].get("bmrKilocalories", 0)
    },
    "body_battery": summarize_dict_list(data["body_battery"], "batteryLevel"),
    "workouts": [
        {
            "name": a.get("activityName"),
            "duration_min": round(a.get("duration", 0) / 60, 1),
            "calories": a.get("calories"),
            "distance_km": round(a.get("distance", 0) / 1000, 2)
        } for a in data["activities"]
    ],
    "early_workouts_today": [
        {
            "name": a.get("activityName"),
            "start": a.get("startTimeLocal"),
            "duration_min": round(a.get("duration", 0) / 60, 1)
        } for a in early_workouts
    ]
}

# === Save
os.makedirs("garmin_export", exist_ok=True)
with open("garmin_export/compact.json", "w") as f:
    json.dump(export, f, indent=2)

print("✅ Saved compact.json")
