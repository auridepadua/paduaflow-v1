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
    "steps": steps,
    "sleep": {
        "sleepTimeSeconds": sleep.get("sleepTimeSeconds"),
        "deepSleepSeconds": sleep.get("deepSleepSeconds"),
        "lightSleepSeconds": sleep.get("lightSleepSeconds"),
        "awakeSleepSeconds": sleep.get("awakeSleepSeconds")
    },
    "restingHeartRate": hrv.get("restingHeartRate"),
    "stressSamples": len(stress),
    "trainingReadinessScore": readiness[0].get("trainingReadinessScore") if isinstance(readiness, list) and readiness else None,
    "activities": activities,
    "calories": calories.get("totalKilocalories", 0)
}

# === Prompt for OpenAI
prompt = f"""
You're my personal coach. Based on the data below, give me a short WhatsApp-style message.

- Start with: "Hello Aurelio 👋"
- Include only actionable insights (1–3 sentences max)
- Recommend if I should train PM based on recovery, sleep, stress
- Add a diet tip based on activity and calories
- Be friendly and motivating

Garmin key data:
{json.dumps(summary_data, indent=2)}
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
