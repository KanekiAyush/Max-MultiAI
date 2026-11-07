import queue
import sounddevice as sd
import vosk
import sys

# Model ka path apne hisaab se check kar lena
MODEL_PATH = "models/vosk-model-small-en-us-0.15"

# Apne wake words yahan daal (sirf lowercase mein)
WAKE_WORDS = ["hey max", "ok max", "max", "shravu"]

q = queue.Queue()

def callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

try:
    model = vosk.Model(MODEL_PATH)
    # Chhota model use kar rahe hain, isliye sample rate 16000 hi rakho
    rec = vosk.KaldiRecognizer(model, 16000)

    print("🎤 Sun raha hoon... 'Hey MAX' ya 'Shravu' bol ke dekho.")

    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=callback):
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = rec.Result()
                text = result.lower()
                print(f"🗣️ Suna: {text}")

                # Check kar ki koi wake word mila ya nahi
                if any(word in text for word in WAKE_WORDS):
                    print("✅ WAKE WORD DETECTED! (Ab yahan apna action likhna)")
                    # Yahan tu apna function call kar sakta hai
                    # jaise: activate_max()

except KeyboardInterrupt:
    print("\n👋 Band kar raha hoon...")
except Exception as e:
    print(f"❌ Error: {e}")