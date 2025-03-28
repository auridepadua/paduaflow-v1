from garminconnect import Garmin
from datetime import datetime, timedelta
import json
import os

# === Config
TOKENSTORE = os.path.expanduser("~/.garminconnect")
client = Garmin()
client.login(tokenstore=TOKENSTORE)

# === Dates
today = datetime.now()
start_day = today.replace(day=1)
days_to_fetch = (today - start_day).days + 1

# === Helper
def safe(fetch_fn, default):
    try:
        return fetch_fn()
    except Exception:
        return default

# === Collect per-day data
monthly_data = {}

for i in range(days_to_fetch):
    day = start_day + timedelta(days=i)
    date_str = day.strftime("%Y-%m-%d")
    print(f"📅 Fetching {date_str}...")

    data = {
        "steps": safe(lambda: client.get_steps_data(date_str), []),
        "sleep": safe(lambda: client.get_sleep_data(date_str), {}),
        "rhr": safe(lambda: client.get_rhr_day(date_str), {}),
        "body_battery": safe(lambda: client.get_body_battery(date_str), []),
        "workout": safe(lambda: client.get_activities(0, 1), [])
    }

    monthly_data[date_str] = data

# === Save
with open("garmin_monthly_export.json", "w") as f:
    json.dump(monthly_data, f, indent=2)

print("✅ Export complete: garmin_monthly_export.json")
