"""One-off: create an ElevenLabs Instant Voice Clone of Sudarshan Karweer from his sample."""
import os
from dotenv import load_dotenv
load_dotenv()
from elevenlabs import ElevenLabs

client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])

with open("/tmp/sk_voice.m4a", "rb") as f:
    voice = client.voices.ivc.create(
        name="Sudarshan Karweer",
        description="Sudarshan Karweer — business coach & strategic advisor. Voice for The SK Strategy Brief podcast.",
        files=[f],
    )
print("VOICE_ID:", voice.voice_id)
