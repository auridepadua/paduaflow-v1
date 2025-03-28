from garminconnect import Garmin
from datetime import datetime, timedelta
import json, os, statistics
import openai

# === Auth
TOKENSTORE = os.path.expanduser("~/.garminconnect")
client = Garmin()
client.login(tokenstore=TOKENSTORE)

# === OpenAI setup
openai.api_key = os.environ.get("OPENAI_API_KEY")

# === Date Setup
now = datetime.now()
yesterday = now - timedelta(days=1)
date_str = yesterday.strftime("%Y-%m-%d")
sleep_start = yesterday.replace(hour=20).isoformat()
sleep_end = now.isoformat()

# === Safe Fetch Helper
def safe(fetch_func, default):
    try:
        return fetch_func()
    except Exception as e:
        print(f"⚠️ {fetch_func.__name__} failed: {e}")
        return default

# === Summarizers
def summarize_list_of_dicts(data, key):
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

# === Fetch Core Data
steps = safe(lambda: client.get_steps_data(date_str), [])
sleep = safe(lambda: client.get_sleep_data(date_str), {})
rhr = safe(lambda: client.get_rhr_day(date_str), {})
hr_day = safe(lambda: client.get_heart_rates(date_str), [])
hr_sleep = safe(lambda: client.get_heart_rates(sleep_start, sleep_end), [])
activities = safe(lambda: client.get_activities_by_date(date_str, date_str), [])
today_acts = safe(lambda: client.get_activities_by_date(now.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d")), [])

# === New: Stress, Calories, Body Battery
stress = safe(lambda: client.get_stress_data(date_str), [])
calories = safe(lambda: client.get_stats(date_str), {})
body_battery = safe(lambda: client.get_body_battery(date_str), [])

early_today = [a for a in today_acts if a.get("startTimeLocal") and datetime.fromisoformat(a["startTimeLocal"]) < now.replace(hour=7, minute=45)]

# === Compact Export
export = {
    "date": date_str,
    "steps": {
        "total": steps[0].get("steps", 0) if steps else 0,
        "goal": steps[0].get("dailyStepGoal", 10000) if steps else 10000
    },
    "sleep_summary": {
        "duration": sleep.get("dailySleepDTO", {}).get("durationInSeconds", 0),
        "efficiency": sleep.get("dailySleepDTO", {}).get("sleepEfficiency", 0),
        "hr_summary": summarize_hr(sleep.get("sleepHeartRate", [])),
        "movement_summary": summarize_list_of_dicts(sleep.get("sleepMovement", []), "activityLevel")
    },
    "resting_hr": rhr.get("restingHeartRate", 0),
    "heart_rate_day": summarize_hr(hr_day),
    "heart_rate_sleep": summarize_hr(hr_sleep),
    "stress": summarize_list_of_dicts(stress, "stressLevel"),
    "calories": {
        "total": calories.get("totalKilocalories", 0),
        "active": calories.get("activeKilocalories", 0),
        "bmr": calories.get("bmrKilocalories", 0)
    },
    "body_battery": summarize_list_of_dicts(body_battery, "batteryLevel"),
    "workouts": [
        {
            "name": a.get("activityName"),
            "duration_min": round(a.get("duration", 0) / 60, 1),
            "calories": a.get("calories"),
            "distance_km": round(a.get("distance", 0) / 1000, 2)
        } for a in activities
    ],
    "early_workouts_today": [
        {
            "name": a.get("activityName"),
            "start": a.get("startTimeLocal"),
            "duration_min": round(a.get("duration", 0) / 60, 1)
        } for a in early_today
    ]
}

# === Save Compact File
os.makedirs("garmin_export", exist_ok=True)
compact_path = "garmin_export/compact.json"
with open(compact_path, "w") as f:
    json.dump(export, f, indent=2)

print("✅ Saved compact export to garmin_export/compact.json")

# === Auto-Summarize via OpenAI
summary_prompt = f"""Summarize the following Garmin health data for {date_str}.
Highlight sleep quality, heart rate, stress, calories, and workouts. Be brief and helpful.
\n\n{json.dumps(export, indent=2)}"""

summary = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": summary_prompt}]
)

print("\n🧠 OpenAI Summary:\n")
print(summary['choices'][0]['message']['content'])
