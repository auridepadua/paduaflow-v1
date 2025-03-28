import shutil
import os

token_folder = os.path.expanduser("~/.garminconnect")
tokens = ["oauth1_token.json", "oauth2_token.json"]

for filename in tokens:
    src_file = os.path.join(token_folder, filename)
    dst_file = os.path.join(token_folder, filename)
    
    if os.path.exists(src_file):
        if os.path.abspath(src_file) != os.path.abspath(dst_file):
            shutil.copy(src_file, dst_file)
            print(f"✅ Copied {filename}")
        else:
            print(f"✅ Token {filename} already in place")
    else:
        print(f"⚠️ Token file {filename} not found")

print("✅ Token check complete")
