import os
import json
from datetime import datetime, timedelta
from garminconnect import Garmin
from openai import OpenAI
from twilio.rest import Client
from dotenv import load_dotenv

# === Load environment variables
load_dotenv()

# === Setup Garmin auth
TOKENSTORE = os.path.expanduser("~/.garminconnect")
client = Garmin()
client.login(tokenstore=TOKENSTORE)

# === Set target date (yesterday in São Paulo time)
now = datetime.now()
target_day = now - timedelta(days=1)
date_str = target_day.strftime("%Y-%m-%d")

# === Fetch helpers
def try_fetch(fetcher, fallback):
    try:
        return fetcher()
    except Exception as e:
        print(f"⚠️  Could not fetch {fetcher.__name__}: {e}")
        return fallback

# === Gather data
steps = try_fetch(lambda: client.get_steps_data(date_str), [])
sleep = try_fetch(lambda: client.get_sleep_data(date_str), {})
rhr = try_fetch(lambda: client.get_rhr_day(date_str), {})
bb = try_fetch(lambda: client.get_body_battery(date_str), [])
activity = try_fetch(lambda: client.get_activities(0, 1), [])

# === Structure export
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
    "body_battery": bb,
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

# === Save to JSON
os.makedirs("garmin_export", exist_ok=True)
export_path = f"garmin_export/garmin_export_all.json"
with open(export_path, "w") as f:
    json.dump(export, f, indent=2)
print(f"✅ Garmin data exported to {export_path} for {date_str}")

# === Ask OpenAI for summary
openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
system_prompt = "You are a helpful wellness assistant generating daily summaries of health data for your user."

user_prompt = f"""
Here is my wellness data for {date_str}. Give me a friendly summary in under 120 words.
If steps are over 10k or workout is logged, acknowledge that positively.
If resting heart rate is low (under 50), mention that.
{json.dumps(export)}
"""

completion = openai.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
)

summary = completion.choices[0].message.content.strip()
print(f"\n📄 OpenAI Summary:\n{summary}")

# === Send WhatsApp message with Twilio
twilio_sid = os.getenv("TWILIO_SID")
twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_from = os.getenv("TWILIO_FROM_NUMBER")
twilio_to = os.getenv("TWILIO_TO_NUMBER")

client_twilio = Client(twilio_sid, twilio_token)

msg = client_twilio.messages.create(
    from_=f"whatsapp:{twilio_from}",
    to=f"whatsapp:{twilio_to}",
    body=f"🧠 Wellness Summary for {date_str}:\n\n{summary}"
)

print(f"📬 Sent WhatsApp message to {twilio_to} with SID {msg.sid}")
