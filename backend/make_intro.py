"""Produce a branded podcast intro: warm cinematic pad + Onyx announcer welcome line."""
import asyncio, os, wave, subprocess
import numpy as np
from dotenv import load_dotenv
load_dotenv()
import podcast

SR = 44100
DELAY = 2.2   # music-only lead-in before the welcome line
TAIL = 2.6    # music tail after the line, then fade
LINE = "Welcome to your weekly dose of The SK Strategy Brief."


def synth_music(total):
    n = int(SR * total); t = np.arange(n) / SR
    cents = lambda f, c: f * 2 ** (c / 1200)
    def voice(freq):
        sig = np.zeros(n)
        for c in (-9, 0, 7):
            f = cents(freq, c); ph = np.random.rand() * 2 * np.pi
            for h, amp in [(1, 1.0), (2, 0.45), (3, 0.22), (4, 0.12), (5, 0.06)]:
                sig += amp * np.sin(2 * np.pi * f * h * t + ph)
        return sig
    Fadd9 = [87.31, 130.81, 174.61, 220.00, 261.63, 392.00]   # F2 C3 F3 A3 C4 G4
    Cadd9 = [130.81, 196.00, 261.63, 329.63, 392.00, 587.33]  # C3 G3 C4 E4 G4 D5
    chord = lambda notes: sum(voice(f) for f in notes) / len(notes)
    A, B = chord(Fadd9), chord(Cadd9)
    mid, xf = total * 0.5, 0.9
    envA = np.clip((mid + xf / 2 - t) / xf, 0, 1); envB = 1 - envA
    pad = A * envA + B * envB
    sub = (np.sin(2 * np.pi * (87.31 / 2) * t) * envA + np.sin(2 * np.pi * (130.81 / 2) * t) * envB) * 0.25
    shim = voice(1046.5) / 6 * (0.6 + 0.4 * np.sin(2 * np.pi * 0.5 * t))
    mono = pad + sub + shim * 0.3
    mono *= (0.85 + 0.15 * np.sin(2 * np.pi * 0.15 * t))
    atk = int(SR * 0.6); mono[:atk] *= np.linspace(0, 1, atk)
    mono /= np.max(np.abs(mono)) + 1e-9; mono *= 0.85
    d = int(SR * 0.008); L = mono.copy(); R = np.zeros(n); R[d:] = mono[:-d]
    st = np.stack([L, R], axis=1); st /= np.max(np.abs(st)) + 1e-9; st *= 0.9
    return (st * 32767).astype(np.int16)


def write_wav(path, data):
    with wave.open(path, "w") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(data.tobytes())


async def main():
    # 1) Onyx announcer VO
    audio = await podcast.synthesize(LINE)
    open("/tmp/vo.mp3", "wb").write(audio)
    dur = float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nk=1:nw=1", "/tmp/vo.mp3"]).strip())
    print(f"VO duration: {dur:.2f}s")

    # 2) Music sized to fit lead-in + VO + tail
    total = DELAY + dur + TAIL
    write_wav("/tmp/music.wav", synth_music(total))
    print(f"Music length: {total:.2f}s")

    # 3) Mix: reverbed pad, ducked under the delayed VO, fades + limiter
    delay_ms = int(DELAY * 1000)
    fade_st = max(0.0, total - 2.0)
    fc = (
        f"[0:a]aecho=0.8:0.88:55|90:0.3|0.2,lowpass=f=7600,highpass=f=55,aformat=channel_layouts=stereo:sample_rates={SR}[bg];"
        f"[1:a]aresample={SR},dynaudnorm=f=151:g=12,aecho=0.9:0.9:70:0.12,"
        f"adelay={delay_ms}|{delay_ms},aformat=channel_layouts=stereo,apad=whole_dur={total:.2f},asplit=2[voA][voB];"
        f"[bg][voA]sidechaincompress=threshold=0.035:ratio=7:attack=5:release=320[duck];"
        f"[duck][voB]amix=inputs=2:duration=longest:normalize=0,"
        f"afade=t=in:st=0:d=1.0,afade=t=out:st={fade_st:.2f}:d=2.0,alimiter=limit=0.95[out]"
    )
    subprocess.check_call([
        "ffmpeg", "-y", "-i", "/tmp/music.wav", "-i", "/tmp/vo.mp3",
        "-filter_complex", fc, "-map", "[out]",
        "-c:a", "libmp3lame", "-b:a", "192k", "/tmp/sk_intro_produced.mp3"
    ])
    out_dur = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nk=1:nw=1", "/tmp/sk_intro_produced.mp3"]).strip().decode()
    sz = os.path.getsize("/tmp/sk_intro_produced.mp3")
    print(f"DONE -> /tmp/sk_intro_produced.mp3  {out_dur}s  {sz} bytes")


asyncio.run(main())
