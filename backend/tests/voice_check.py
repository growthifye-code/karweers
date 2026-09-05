"""Quick ElevenLabs voice-clone tone check — synthesizes a short Hinglish snippet."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
import podcast

SNIPPET = (
    "I'm Sudarshan Karweer, and this is The SK Strategy Brief. "
    "देखिए, आज एक simple सवाल से शुरू करते हैं — क्या आपका business cash पर चल रहा है या hope पर? "
    "Look, honestly, ज़्यादातर founders यहीं पर फँसते हैं। "
    "The real question is not how fast you grow, but whether your unit economics can carry that growth. "
    "सच कहूँ तो, clarity beats ambition, every single time."
)

if __name__ == "__main__":
    audio = podcast._elevenlabs_tts(SNIPPET)
    out = "/tmp/voice_check.mp3"
    with open(out, "wb") as f:
        f.write(audio)
    print(f"OK ElevenLabs bytes={len(audio)} -> {out}")
