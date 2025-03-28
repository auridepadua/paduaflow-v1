import os
import json
from openai import OpenAI
from twilio.rest import Client as TwilioClient

# === Helper to clean null/empty data ===
def clean_data(obj):
    if isinstance(obj, dict):
        return {
            k: clean_data(v)
            for k, v in obj.items()
            if v not in (None, [], {}, "") and clean_data(v) not in (None, [], {}, "")
        }
    elif isinstance(obj, list):
        return [clean_data(i) for i in obj if i not in (None, [], {}, "")]
    else:
        return obj

# === Environment variables
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
TWILIO_ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]
TWILIO_WHATSAPP_FROM = os.environ["TWILIO_WHATSAPP_FROM"]
TWILIO_WHATSAPP_TO = os.environ["TWILIO_WHATSAPP_TO"]

# === Load Garmin data
with open("garmin_export_all.json", "r") as f:
    garmin_data = json.load(f)

# === Check for blank data
sleep_data = garmin_data.get("sleep", {}).get("dailySleepDTO", {})
steps_data = garmin_data.get("steps", {})
rhr_data = garmin_data.get("rhr", {})

is_blank = not sleep_data and not steps_data.get("totalSteps") and not rhr_data.get("restingHeartRate")

if is_blank:
    error_message = (
        "⚠️ Garmin data appears to be missing or not synced.\n\n"
        "Please open your Garmin app and make sure your device has synced for the latest day."
    )
    print(error_message)

    # Optional: Send WhatsApp error message
    twilio = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    twilio.messages.create(
        body=error_message,
        from_=TWILIO_WHATSAPP_FROM,
        to=TWILIO_WHATSAPP_TO
    )
    exit("❌ Garmin data is blank — exiting early.")

# === Print raw cleaned data for debug
print("📦 Garmin Raw Export:")
print(json.dumps(clean_data(garmin_data), indent=2))

# === OpenAI Client
client = OpenAI(api_key=OPENAI_API_KEY)

# === Create trimmed Garmin payload for summarization
summary_payload = {
    "date": garmin_data.get("date"),
    "steps": garmin_data.get("steps"),
    "sleep": garmin_data.get("sleep"),
    "rhr": garmin_data.get("rhr"),
    "body_battery": garmin_data.get("body_battery"),
    "workout": garmin_data.get("workout"),
    "heart_rate": garmin_data.get("heart_rate"),
    "stress": garmin_data.get("stress"),
    "respiration": garmin_data.get("respiration"),
    "hydration": garmin_data.get("hydration"),
    "spo2": garmin_data.get("spo2"),
    "training_readiness": garmin_data.get("training_readiness"),
    "calories": garmin_data.get("calories")
}

# === Step 1: Summarize Garmin data with GPT-3.5
summary_prompt = f"""
You're a personal health assistant. Summarize the user's Garmin data into key highlights.

Be detailed on:
- Sleep data (quality, total hours, light/deep/REM)
- Resting heart rate trends
- Activity, steps, and calories
- Stress or recovery patterns
- HRV if available

Raw Garmin export:
{json.dumps(clean_data(garmin_data))}
"""

summary_response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You the most performance-driven sprinting coach."},
        {"role": "user", "content": summary_prompt}
    ],
    temperature=0.4,
    max_tokens=1500
)

summary = summary_response.choices[0].message.content.strip()

# === Step 2: Generate WhatsApp-style coaching using GPT-4
insight_prompt = f"""
You're my pro personal coach. Based on this Garmin data summary, write a short WhatsApp-style message.

Rules:
- Start with: "Hello Aurelio 👋"
- Focus on recovery, sleep, and heart rate
- Give actionable advice in 2–3 sentences max
- Suggest if I should train PM today
- Add a short diet tip
- Keep it fierce and strong

Garmin summary:
{summary}
"""

insight_response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You the most performance-driven sprinting coach."},
        {"role": "user", "content": insight_prompt}
    ],
    temperature=0.6,
    max_tokens=300
)

message_body = insight_response.choices[0].message.content.strip()

# === Send WhatsApp message
twilio = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
twilio.messages.create(
    body=message_body,
    from_=TWILIO_WHATSAPP_FROM,
    to=TWILIO_WHATSAPP_TO
)

print("✅ Summary sent to WhatsApp!")
