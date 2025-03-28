import os
import json
import datetime
import openai
from twilio.rest import Client as TwilioClient
from openai import OpenAI

# === Load secrets
openai.api_key = os.environ["OPENAI_API_KEY"]
TWILIO_SID = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]
TWILIO_WHATSAPP_FROM = os.environ["TWILIO_WHATSAPP_FROM"]
TWILIO_WHATSAPP_TO = os.environ["TWILIO_WHATSAPP_TO"]

# === Dates
today = datetime.date.today()
d1 = today - datetime.timedelta(days=1)
d2 = today - datetime.timedelta(days=2)

# === Load JSON
def load_data(date):
    path = f"garmin_export/{date}.json"
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}

today_data = load_data(d1.isoformat())
yesterday_data = load_data(d2.isoformat())

# === Comparison helpers
def safe_get(d, keys, default="N/A"):
    for key in keys:
        if isinstance(d, dict) and key in d:
            d = d[key]
        else:
            return default
    return d

def compare(val1, val2):
    if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
        diff = val1 - val2
        return f"{val1} ({'+' if diff >= 0 else ''}{diff})"
    return str(val1)

# === Extract metrics
sleep_d1 = safe_get(today_data, ["sleep", "dailySleepDTO", "sleepTimeSeconds"], 0)
sleep_d2 = safe_get(yesterday_data, ["sleep", "dailySleepDTO", "sleepTimeSeconds"], 0)

rhr_d1 = safe_get(today_data, ["rhr", "restingHeartRate"], 0)
rhr_d2 = safe_get(yesterday_data, ["rhr", "restingHeartRate"], 0)

readiness_data = today_data.get("training_readiness", [])
training_readiness_score = readiness_data[0].get("trainingReadinessScore", "N/A") if readiness_data else "N/A"

# === Prompt
prompt = f"""
Hello Aurelio, here's your Garmin summary for {d1}:

✅ Sleep: {compare(sleep_d1 // 3600, sleep_d2 // 3600)} hours
💓 Resting HR: {compare(rhr_d1, rhr_d2)} bpm
🎯 Training Readiness Score: {training_readiness_score}

Based on this data, give:
1. A short summary of yesterday's recovery
2. Whether to train this afternoon (PM) or not
3. One actionable tip for performance or nutrition today
"""

# === OpenAI chat completion
client = OpenAI(api_key=openai.api_key)
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {
            "role": "system",
            "content": "You are a helpful performance coach. Keep messages short, clear, and practical."
        },
        {
            "role": "user",
            "content": prompt
        }
    ]
)

summary = response.choices[0].message.content.strip()
print(summary)

# === Twilio send
twilio = TwilioClient(TWILIO_SID, TWILIO_TOKEN)
twilio.messages.create(
    body=summary,
    from_=TWILIO_WHATSAPP_FROM,
    to=TWILIO_WHATSAPP_TO
)
