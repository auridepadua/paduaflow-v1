from garminconnect import Garmin
from datetime import datetime
import os

TOKENSTORE = os.path.expanduser("~/.garminconnect")
client = Garmin()
client.login(tokenstore=TOKENSTORE)

print("\n📋 Garmin Quick Test Menu")
print("1 - Sleep")
print("2 - Steps")
print("3 - Resting Heart Rate")
print("4 - Body Battery")
print("5 - Last Workout")
print("q - Quit")

date = input("\n📅 Enter date (YYYY-MM-DD, default today): ").strip()
if not date:
    date = datetime.now().strftime("%Y-%m-%d")

while True:
    choice = input("\n🧭 Select option: ").strip().lower()

    if choice == "1":
        print(client.get_sleep_data(date))
    elif choice == "2":
        print(client.get_steps_data(date))
    elif choice == "3":
        print(client.get_rhr_day(date))
    elif choice == "4":
        print(client.get_body_battery(date))
    elif choice == "5":
        print(client.get_activities(0, 1))
    elif choice == "q":
        print("👋 Done!")
        break
    else:
        print("❓ Unknown option")
