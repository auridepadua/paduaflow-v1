import openai
from twilio.rest import Client
import json
import os

# === CONFIGURATION ===
GARMIN_JSON_PATH = "garmin_export_all.json"

# === OpenAI Setup ===
openai.api_key = os.environ["OPENAI_API_KEY"]

# === Twilio Setup ===
TWILIO_ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]
FROM_WHATSAPP = os.environ["TWILIO_WHATSAPP_FROM"]
TO_WHATSAPP = os.environ["TWILIO_WHATSAPP_TO"]

# === Load Garmin JSON ===
with open(GARMIN_JSON_PATH, "r") as f:
    data = json.load(f)

# === OpenAI Prompt ===
prompt = f"""
Summarize the following Garmin health data for {data["date"]} in a concise format with:
- Sleep duration and quality
- Number of steps
- Calories burned
- Workouts
- Training readiness or body battery
Avoid repeating raw numbers, and instead synthesize insights.

{json.dumps(data, indent=2)}
"""

response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a health and performance assistant."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.7
)

summary = response["choices"][0]["message"]["content"]

# === Send via WhatsApp (Twilio) ===
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
message = client.messages.create(
    body=summary,
    from_=FROM_WHATSAPP,
    to=TO_WHATSAPP
)

print("✅ WhatsApp message sent.")
