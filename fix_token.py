import base64
import json
import os

# === Paths
token_file = os.path.expanduser("~/.garminconnect_base64")
token_dir = os.path.expanduser("~/.garminconnect")

# === Decode token string
with open(token_file, "r") as f:
    encoded = f.read().strip()

decoded = base64.b64decode(encoded).decode("utf-8")
tokens = json.loads(decoded)

# === Save each token to expected path
os.makedirs(token_dir, exist_ok=True)
with open(os.path.join(token_dir, "oauth1_token.json"), "w") as f:
    json.dump(tokens[0], f)

with open(os.path.join(token_dir, "oauth2_token.json"), "w") as f:
    json.dump(tokens[1], f)

print(f"✅ Token files extracted to {token_dir}")
