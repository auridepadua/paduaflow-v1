import os
import base64

# Paths
HOME = os.path.expanduser("~")
TOKEN_DIR = os.path.join(HOME, ".garminconnect")
OAUTH1_PATH = os.path.join(TOKEN_DIR, "oauth1_token.json")
OAUTH2_PATH = os.path.join(TOKEN_DIR, "oauth2_token.json")

# Read from environment secrets
oauth1_b64 = os.environ.get("OAUTH1_B64")
oauth2_b64 = os.environ.get("OAUTH2_B64")

# Ensure target directory exists
os.makedirs(TOKEN_DIR, exist_ok=True)

# Decode and write token files
def decode_and_write(b64_str, path):
    if b64_str:
        with open(path, "wb") as f:
            f.write(base64.b64decode(b64_str))
        print(f"✅ Token written to {path}")
    else:
        print(f"❌ Missing base64 string for {path}")

decode_and_write(oauth1_b64, OAUTH1_PATH)
decode_and_write(oauth2_b64, OAUTH2_PATH)

print("✅ Token check complete")
