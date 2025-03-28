import os
import json
from openai import OpenAI
from twilio.rest import Client as TwilioClient

# === Environment Variables ===
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
TWILIO_ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]
TWILIO_WHATSAPP_FROM = os.environ["TWILIO_WHATSAPP_FROM"]
TWILIO_WHATSAPP_TO = os.environ["TWILIO_WHATSAPP_TO"]

# === File Paths ===
COMPACT_PATH = "garmin_export/compact.json"

# === Load Garmin Compact JSON ===
if not os.path.exists(COMPACT_PATH):
    raise FileNotFoundError("❌ compact.json not found. Run garmin_export_full.py first.")

with open(COMPACT_PATH, "r") as f:
    data = json.load(f)

# === Validate Key Garmin Data ===
sleep_summary = data.get("sleep_summary", {})
steps_data = data.get("steps", {})
rhr_value = data.get("resting_hr", None)

if not sleep_summary and not steps_data.get("total") and not rhr_value:
    error_message = (
        "⚠️ Garmin data is missing or not synced.\n\n"
        "Please open your Garmin app and ensure your watch synced for the latest day."
    )
    print(error_message)

    # Notify via WhatsApp
    twilio = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    twilio.messages.create(
        body=error_message,
        from_=TWILIO_WHATSAPP_FROM,
        to=TWILIO_WHATSAPP_TO
    )
    exit("❌ Exiting due to missing Garmin data.")

# === OpenAI Client Setup ===
client = OpenAI(api_key=OPENAI_API_KEY)

# === Summarize Garmin Data ===
summary_prompt = f"""Summarize the following Garmin health data for {data['date']}:
- Sleep duration and quality
- Resting heart rate
- Stress and body battery levels
- Calories spent
- Workout activity insights

Be brief, insightful, and helpful.

Garmin Data:
{json.dumps(data)}"""

try:
    summary_response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": summary_prompt}]
    )
    summary = summary_response.choices[0].message.content.strip()
except Exception as e:
    print(f"❌ OpenAI summarization failed: {e}")
    exit(1)

# === Save OpenAI Summary to File ===
summary_path = f"garmin_export/summary_{data['date']}.txt"
with open(summary_path, "w") as f:
    f.write(summary)

print("\n🧠 OpenAI Summary:\n")
print(summary)

# === Coaching Message (GPT-4) ===
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

try:
    insight_response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are the most performance-driven sprinting coach."},
            {"role": "user", "content": insight_prompt}
        ],
        temperature=0.6,
        max_tokens=300
    )
    message_body = insight_response.choices[0].message.content.strip()
except Exception as e:
    print(f"❌ GPT-4 coaching generation failed: {e}")
    exit(1)

# === Send WhatsApp Coaching Message ===
twilio = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
twilio.messages.create(
    body=message_body,
    from_=TWILIO_WHATSAPP_FROM,
    to=TWILIO_WHATSAPP_TO
)

print("\n✅ WhatsApp message sent!\n")
print(message_body)
