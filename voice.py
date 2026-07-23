import subprocess
import tempfile
import os
from faster_whisper import WhisperModel

model = WhisperModel("small", device="cuda", compute_type="int8")

MIC_SOURCE = "alsa_input.pci-0000_00_1f.3-platform-skl_hda_dsp_generic.HiFi__Mic1__source"

def listen(duration=6) -> str:
    print(f"🎤 Listening for {duration} seconds... Speak now!")

    tmp_path = tempfile.mktemp(suffix=".wav")

    try:
        rec = subprocess.Popen(
            ["pw-record", "--target", MIC_SOURCE, tmp_path]
        )
        import time
        time.sleep(duration)
        rec.terminate()
        rec.wait()
    except Exception as e:
        print(f"❌ Recording failed: {e}")
        return ""

    print("✅ Recording done. Transcribing...")

    try:
        segments, _ = model.transcribe(tmp_path, language="en")
        text = " ".join(seg.text.strip() for seg in segments).strip()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    print(f"📝 You said: '{text}'")
    return text