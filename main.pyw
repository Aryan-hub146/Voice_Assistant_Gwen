import pvporcupine
import pyaudio
import struct
import speech_recognition as sr
import os
import webbrowser
import time
from elevenlabs import generate, save, set_api_key
from playsound import playsound  # 🔇 plays mp3 silently

# === Settings ===
ACCESS_KEY = "8hWTmdQehf7pif1T3dfbXelKluS/tIVDCZAijNOu9B22m6FcIKWI2w=="
WAKE_WORD_PATH = "hey-Gwen_en_windows_v3_0_0.ppn"

ELEVEN_API_KEY = "sk_654f711d85fae6dab6593f9cb1f0d5bed1639be12639ad6c"
VOICE_ID = "RgJi5TqVYLDEHFYlU8vP"

# === ElevenLabs Setup ===
set_api_key(ELEVEN_API_KEY)

def speak(text):
    print("Assistant:", text)
    output_file = "output.mp3"
    try:
        audio = generate(
            text=text,
            voice=VOICE_ID,
            model="eleven_monolingual_v1"
        )

        # 🧹 Clean up old file if it exists
        if os.path.exists(output_file):
            try:
                os.remove(output_file)
            except PermissionError:
                print("⚠️ Waiting for locked file to release...")
                time.sleep(0.5)
                os.remove(output_file)

        save(audio, output_file)
        playsound(output_file)

        # Optional cleanup
        try:
            os.remove(output_file)
        except:
            pass

    except Exception as e:
        print("⚠️ ElevenLabs failed:", e)
        print("Falling back to text output only.")

# === Listen and Convert Voice to Text ===
def listen_command():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        speak("yes peter, how can i help you?")
        audio = recognizer.listen(source)
    try:
        command = recognizer.recognize_google(audio).lower()
        print("You said:", command)
        return command
    except sr.UnknownValueError:
        speak("Sorry, I didn't get that.")
        return ""
    except sr.RequestError:
        speak("Speech recognition service is down.")
        return ""

# === Execute Recognized Command ===
def execute_command(command):
    if "open notepad" in command:
        os.system("start notepad")
        speak("Opening Notepad")
    elif "give your speech" in command:
        speak("It's easy to feel hopeful on a beautiful day like today, but there will be dark days ahead of us too. There will be days where you feel all alone, and that's when hope is needed most. No matter how buried it gets, or how lost you feel, you must promise me that you will hold on to hope and keep it alive. We have to be greater than what we suffer.")
    elif "open youtube" in command:
        webbrowser.open("https://www.youtube.com")
        speak("Opening YouTube")
    elif "shutdown" in command:
        speak("Shutting down your system.")
        os.system("shutdown /s /t 1")
    elif "exit" in command:
        speak("Goodbye!")
        
    else:
        speak("Sorry, I can't do that yet.")

# === Wake Word Detection Setup ===
porcupine = pvporcupine.create(
    access_key=ACCESS_KEY,
    keyword_paths=[WAKE_WORD_PATH]
)

pa = pyaudio.PyAudio()
stream = pa.open(
    rate=porcupine.sample_rate,
    channels=1,
    format=pyaudio.paInt16,
    input=True,
    frames_per_buffer=porcupine.frame_length
)

print("🕵️ Waiting for 'hey Gwen'...")

# === Main Loop ===
try:
    while True:
        pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
        pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

        result = porcupine.process(pcm)
        if result >= 0:
            print("🎙️ Wake word detected!")
            command = listen_command()
            execute_command(command)

except KeyboardInterrupt:
    print("🛑 Stopping assistant...")
finally:
    stream.stop_stream()
    stream.close()
    pa.terminate()
    porcupine.delete()
