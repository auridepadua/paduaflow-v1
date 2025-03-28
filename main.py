from datetime import datetime, timedelta
import json
import os
from openai import OpenAI
from twilio.rest import Client

# === Configuration from Environment ===
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
TWILIO_ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]
TWILIO_WHATSAPP_FROM = os.environ["TWILIO_WHATSAPP_FROM"]
TWILIO_WHATSAPP_TO = os.environ["TWILIO_WHATSAPP_TO"]

# === Setup clients ===
openai_client = OpenAI(api_key=OPENAI_API_KEY)
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# === Load JSON data ===
with open("garmin_export_all.json") as f:
    today_data = json.load(f)

# Load previous day data for comparison (if exists)
date_format = "%Y-%m-%d"
d1 = today_data["date"]
d2 = (datetime.strptime(d1, date_format) - timedelta(days=1)).strftime(date_format)

prev_data_path = f"garmin_export/{d2}.json"
prev_data = {}
if os.path.exists(prev_data_path):
    with open(prev_data_path) as f:
        prev_data = json.load(f)

# === Build prompt for OpenAI ===
prompt = f"""
You are a health assistant creating short, actionable summaries for a daily wellness dashboard.

User's name: Aurelio  
Date: {today_data['date']}

Today's sleep (in seconds):
- Deep: {today_data['sleep'].get('dailySleepDTO', {}).get('deepSleepSeconds', 0)}
- Light: {today_data['sleep'].get('dailySleepDTO', {}).get('lightSleepSeconds', 0)}
- Awake: {today_data['sleep'].get('dailySleepDTO', {}).get('awakeSleepSeconds', 0)}

Resting HR: {today_data['rhr'].get("restingHeartRate", "N/A")}
Steps: {today_data['steps'].get("totalSteps", 0)}
Training Readiness Score: {today_data.get("training_readiness", [{}])[0].get("trainingReadinessScore", "N/A")}

Calories: {today_data.get("calories", {}).get("totalKilocalories", "N/A")}

Workouts: {len(today_data.get("workout", []))} session(s)
{[w['activityName'] for w in today_data.get("workout", [])]}

Previous day ({d2}) resting HR: {prev_data.get("rhr", {}).get("restingHeartRate", "N/A")}
Previous day sleep total: {prev_data.get("sleep", {}).get("dailySleepDTO", {}).get("sleepTimeSeconds", "N/A")}

Generate a SHORT daily summary. Use this structure:
1. Greet Aurelio
2. Summarize key insights
3. Give actionable suggestions for training or recovery (e.g. “Train hard PM”, “Take it light”)
4. Add one diet tip for today (e.g. “Increase hydration”)

Always output in English. Be friendly and concise.
"""

# === Run OpenAI ===
response = openai_client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a personal health assistant."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.7,
)

summary_text = response.choices[0].message.content.strip()
print("✅ Summary Generated:\n", summary_text)

# === Send via WhatsApp ===
message = twilio_client.messages.create(
    from_=TWILIO_WHATSAPP_FROM,
    body=summary_text,
    to=TWILIO_WHATSAPP_TO
)

print("📬 WhatsApp Message SID:", message.sid)
