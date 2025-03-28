import os
import json
from openai import OpenAI
from twilio.rest import Client as TwilioClient

# === Environment variables
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
TWILIO_ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]
TWILIO_WHATSAPP_FROM = os.environ["TWILIO_WHATSAPP_FROM"]
TWILIO_WHATSAPP_TO = os.environ["TWILIO_WHATSAPP_TO"]

# === Load Garmin data
with open("garmin_export_all.json", "r") as f:
    garmin_data = json.load(f)

# === Load previous context (if available)
try:
    with open("context_last_day.json", "r") as f:
        previous_data = json.load(f)
except FileNotFoundError:
    previous_data = None

print("📦 Full Garmin data:")
print(json.dumps(garmin_data, indent=2))
    
# === Prepare required data variables before use
steps_data = garmin_data.get("steps", {})
sleep_data = garmin_data.get("sleep", {}).get("dailySleepDTO", {})
rhr_data = garmin_data.get("rhr", {})

# === Trimmed key values
date = garmin_data.get("date")
steps = garmin_data.get("steps", {})
sleep = garmin_data.get("sleep", {}).get("dailySleepDTO", {})
hrv = garmin_data.get("rhr", {})
stress = garmin_data.get("stress", [])
readiness = garmin_data.get("training_readiness", {})
activities = garmin_data.get("workout", [])
calories = garmin_data.get("calories", {})

# === Build a short summary for the prompt
summary_data = {
    "date": date,
    "steps": steps_data,
    "sleep": {
        "sleepTimeSeconds": sleep_data.get("sleepTimeSeconds"),
        "deepSleepSeconds": sleep_data.get("deepSleepSeconds"),
        "lightSleepSeconds": sleep_data.get("lightSleepSeconds"),
        "awakeSleepSeconds": sleep_data.get("awakeSleepSeconds")
    },
    "restingHeartRate": rhr_data.get("restingHeartRate"),
    "stressSamples": len(stress),
    "trainingReadinessScore": readiness[0].get("trainingReadinessScore") if isinstance(readiness, list) and readiness else None,
    "activities": activities,
    "calories": calories.get("totalKilocalories", 0)
}

# === Optional comparison (trends)
recovery_trend = ""
if previous_data:
    prev_rhr = previous_data.get("restingHeartRate", 0)
    curr_rhr = summary_data.get("restingHeartRate", 0)
    prev_sleep = previous_data.get("sleep", {}).get("sleepTimeSeconds", 0)
    curr_sleep = summary_data.get("sleep", {}).get("sleepTimeSeconds", 0)

    rhr_diff = curr_rhr - prev_rhr
    sleep_diff = curr_sleep - prev_sleep

    recovery_trend = f"""
Recovery Trend:
- Resting HR: {'↑' if rhr_diff > 0 else '↓'} {abs(rhr_diff)} bpm vs. yesterday
- Sleep: {'↑' if sleep_diff > 0 else '↓'} {abs(sleep_diff // 60)} min vs. yesterday
"""

# === DEBUG: print data going into OpenAI
print("\n📦 Summary data sent to OpenAI:")
print(json.dumps(summary_data, indent=2))

# === Prompt for OpenAI
prompt = f"""
You're my personal coach. Based on the data below, give me a short WhatsApp-style message.

- Start with: "Hello Aurelio 👋"
- Include Sleep stats and HRV stats
- Include only actionable insights (1–3 sentences max)
- Recommend type of trainingn (strentgh or sprinting) I should train PM based on recovery, sleep, stress
- Be fierce and motivating

Full Garmin export JSON:
{json.dumps(garmin_data, indent=2)}

{recovery_trend}
"""
# === OpenAI Client
client = OpenAI(api_key=OPENAI_API_KEY)

response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You're a training and health assistant."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.6,
    max_tokens=350
)

message_body = response.choices[0].message.content.strip()

# === Twilio WhatsApp
twilio = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
twilio.messages.create(
    body=message_body,
    from_=TWILIO_WHATSAPP_FROM,
    to=TWILIO_WHATSAPP_TO
)
print("✅ Summary sent to WhatsApp!")

# === Save context for tomorrow's comparison
with open("context_last_day.json", "w") as f:
    json.dump(summary_data, f, indent=2)
