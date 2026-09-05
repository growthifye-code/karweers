"""Generate a short, corporate-style INSTRUMENTAL music intro (no voice) for the podcast."""
import subprocess, wave
import numpy as np

SR = 44100
TOTAL = 6.5


def synth():
    n = int(SR * TOTAL); t = np.arange(n) / SR
    cents = lambda f, c: f * 2 ** (c / 1200)

    def pad_voice(freq):
        sig = np.zeros(n)
        for c in (-8, 0, 7):
            f = cents(freq, c); ph = np.random.rand() * 2 * np.pi
            for h, amp in [(1, 1.0), (2, 0.5), (3, 0.25), (4, 0.12)]:
                sig += amp * np.sin(2 * np.pi * f * h * t + ph)
        return sig

    # Uplifting corporate progression: Cadd9 -> G -> Am7 -> Fadd9 (2 bars over 6.5s)
    chords = [
        [130.81, 196.00, 261.63, 392.00, 587.33],   # Cadd9
        [196.00, 246.94, 392.00, 587.33],            # G
        [220.00, 261.63, 329.63, 523.25],            # Am7
        [174.61, 261.63, 349.23, 523.25],            # Fadd9
    ]
    seg = TOTAL / len(chords)
    pad = np.zeros(n)
    for i, notes in enumerate(chords):
        s = int(i * seg * SR); e = int((i + 1) * seg * SR)
        env = np.ones(e - s)
        a = int(0.15 * SR); env[:a] = np.linspace(0, 1, a)
        d = int(0.25 * SR); env[-d:] = np.linspace(1, 0.6, d)
        chunk = sum(pad_voice(f) for f in notes)[s:e]
        chunk = chunk / (np.max(np.abs(chunk)) + 1e-9) * env
        pad[s:e] += chunk

    # Bright plucked arpeggio (modern corporate) — staccato notes across the bars
    arp = np.zeros(n)
    step = 0.325  # note every ~0.325s
    arp_notes = [523.25, 659.25, 784.00, 659.25, 587.33, 784.00, 880.00, 784.00,
                 659.25, 784.00, 880.00, 1046.50, 880.00, 784.00, 659.25, 523.25,
                 587.33, 784.00, 1046.50, 880.00]
    for k, f in enumerate(arp_notes):
        st = k * step
        if st + 0.3 > TOTAL:
            break
        i0 = int(st * SR); L = int(0.3 * SR)
        tt = np.arange(L) / SR
        env = np.exp(-tt * 9)  # plucky decay
        note = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * f * 2 * tt)) * env
        arp[i0:i0 + L] += note * 0.5

    # Soft sub-bass root pulse per bar
    bass = np.zeros(n)
    roots = [65.41, 98.00, 110.00, 87.31]
    for i, rf in enumerate(roots):
        s = int(i * seg * SR); e = int((i + 1) * seg * SR)
        tt = np.arange(e - s) / SR
        env = np.exp(-tt * 1.2)
        bass[s:e] += np.sin(2 * np.pi * rf * tt) * env * 0.6

    mono = pad * 0.5 + arp * 0.6 + bass * 0.5
    mono /= np.max(np.abs(mono)) + 1e-9
    # gentle global fade in/out
    fin = int(0.3 * SR); mono[:fin] *= np.linspace(0, 1, fin)
    fout = int(1.6 * SR); mono[-fout:] *= np.linspace(1, 0, fout)
    mono *= 0.9
    # light stereo widening
    dd = int(SR * 0.009); L = mono.copy(); R = np.zeros(n); R[dd:] = mono[:-dd]
    st = np.stack([L, R], axis=1); st /= np.max(np.abs(st)) + 1e-9; st *= 0.92
    return (st * 32767).astype(np.int16)


with wave.open("/tmp/corp_music.wav", "w") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(synth().tobytes())

# Reverb + tone polish, then encode to mp3.
subprocess.check_call([
    "ffmpeg", "-y", "-i", "/tmp/corp_music.wav",
    "-af", "aecho=0.8:0.85:45|70:0.25|0.15,highpass=f=60,lowpass=f=13000,alimiter=limit=0.95",
    "-c:a", "libmp3lame", "-b:a", "192k", "/tmp/corp_intro.mp3",
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
import os
print("DONE", os.path.getsize("/tmp/corp_intro.mp3"), "bytes")
