import os
import json
from openai import OpenAI
from twilio.rest import Client as TwilioClient

# === Load environment variables ===
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
TWILIO_ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]
TWILIO_WHATSAPP_FROM = os.environ["TWILIO_WHATSAPP_FROM"]
TWILIO_WHATSAPP_TO = os.environ["TWILIO_WHATSAPP_TO"]

# === Load Garmin data
with open("garmin_export_all.json", "r") as f:
    garmin_data = json.load(f)

# === Build the prompt
prompt = f"""
You're my personal performance assistant. Based on yesterday's Garmin data below, write me a short WhatsApp-style update.

- Always greet me like: "Hello Aurelio 👋"
- Provide *actionable insights only*
- Avoid repeating raw data unless important
- Mention training suggestion for PM session based on recovery, HRV, stress, sleep
- Include a small diet tip based on training or recovery needs
- End with a motivating tone

Garmin data (JSON):
{json.dumps(garmin_data)}
"""

# === Get OpenAI response
client = OpenAI(api_key=OPENAI_API_KEY)
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You're a personal training and recovery assistant."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.7,
    max_tokens=400
)

summary = response.choices[0].message.content

# === Send to WhatsApp
twilio = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
message = twilio.messages.create(
    body=summary,
    from_=TWILIO_WHATSAPP_FROM,
    to=TWILIO_WHATSAPP_TO
)

print("✅ Message sent!")
