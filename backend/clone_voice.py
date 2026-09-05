"""Create ElevenLabs IVC of Sudarshan Karweer via the REST API directly."""
import os, json, requests
from dotenv import load_dotenv
load_dotenv()

key = os.environ["ELEVENLABS_API_KEY"]
with open("/tmp/sk_voice.m4a", "rb") as f:
    r = requests.post(
        "https://api.elevenlabs.io/v1/voices/add",
        headers={"xi-api-key": key},
        data={"name": "Sudarshan Karweer", "labels": json.dumps({})},
        files={"files": ("sk_voice.m4a", f, "audio/mp4")},
        timeout=60,
    )
print("status:", r.status_code)
print("body:", r.text[:500])
