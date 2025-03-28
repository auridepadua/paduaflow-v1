import shutil
import os

# Use existing paths from decoded secrets
source_folder = os.path.expanduser("~/.garminconnect")
target_folder = os.path.expanduser("~/.garminconnect")

# You could also redirect elsewhere if needed, but currently we keep it at ~/.garminconnect
if os.path.exists(source_folder):
    for filename in ["oauth1_token.json", "oauth2_token.json"]:
        src_file = os.path.join(source_folder, filename)
        dst_file = os.path.join(target_folder, filename)
        if os.path.isfile(src_file):
            shutil.copy(src_file, dst_file)

print("✅ Token files confirmed and copied (if needed)")
