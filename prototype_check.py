import os, time, threading, struct, sys
import numpy as np
import tkinter as tk
import pyaudio, pvporcupine, webbrowser, speech_recognition as sr
from elevenlabs import generate, save, set_api_key
from playsound import playsound

# === YOUR KEYS & SETTINGS ===
ACCESS_KEY = "8hWTmdQehf7pif1T3dfbXelKluS/tIVDCZAijNOu9B22m6FcIKWI2w=="
WAKE_WORD_PATH = "hey-Gwen_en_windows_v3_0_0.ppn"
ELEVEN_API_KEY = "sk_654f711d85fae6dab6593f9cb1f0d5bed1639be12639ad6c"
VOICE_ID = "Vara1IkEw7vh5Hr5dT3C"
set_api_key(ELEVEN_API_KEY)

# === Global State ===
assistant_running = True
listening = False
glow_radius = 10
glow_direction = 1

# === GUI Window ===
root = tk.Tk()
root.overrideredirect(True)  # Remove window border
root.geometry("400x150+100+100")
root.configure(bg="white")
root.attributes("-topmost", True)
root.withdraw()

canvas = tk.Canvas(root, width=400, height=150, bg="white", highlightthickness=0)
canvas.pack()

# === Waveform Animation ===
def animate_waveform():
    global listening
    CHUNK = 512
    RATE = 44100
    pa = pyaudio.PyAudio()
    stream = pa.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)

    def update():
        if not listening:
            stream.stop_stream()
            stream.close()
            pa.terminate()
            root.withdraw()
            return

        data = np.frombuffer(stream.read(CHUNK, exception_on_overflow=False), dtype=np.int16)
        volume = np.abs(data).mean() / 500

        canvas.delete("wave")
        points = []
        for x in range(0, 400, 4):
            y = 75 + np.sin(x * 0.04 + time.time() * 5) * volume * 30
            points.append((x, y))

        for i in range(1, len(points)):
            canvas.create_line(points[i-1], points[i], fill="deepskyblue", width=2, tags="wave")

        root.after(30, update)

    update()

# === Glowing Aura Animation ===
def animate_glow():
    global glow_radius, glow_direction
    if not listening:
        return

    glow_radius += glow_direction * 2
    if glow_radius >= 30:
        glow_direction = -1
    elif glow_radius <= 10:
        glow_direction = 1

    canvas.delete("glow")
    center_x, center_y = 200, 75
    canvas.create_oval(
        center_x - (70 + glow_radius), center_y - (30 + glow_radius),
        center_x + (70 + glow_radius), center_y + (30 + glow_radius),
        fill="deepskyblue", outline="", tags="glow"
    )

    root.after(60, animate_glow)

def show_waveform():
    global listening
    listening = True
    root.deiconify()
    threading.Thread(target=animate_waveform, daemon=True).start()
    root.after(0, animate_glow)

def hide_waveform():
    global listening
    listening = False
    canvas.delete("glow")

# === Speak Function ===
def speak(text):
    print("Assistant:", text)
    output_file = "output.mp3"
    try:
        audio = generate(text=text, voice=VOICE_ID, model="eleven_monolingual_v1")
        if os.path.exists(output_file):
            try:
                os.remove(output_file)
            except:
                time.sleep(0.5)
                os.remove(output_file)

        save(audio, output_file)
        playsound(output_file)
        try:
            os.remove(output_file)
        except:
            pass

    except Exception as e:
        print("⚠️ ElevenLabs failed:", e)

# === Listen to Command ===
def listen_command():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        show_waveform()
        speak("Yes Peter, how can I help you?")
        audio = recognizer.listen(source)
    hide_waveform()
    try:
        return recognizer.recognize_google(audio).lower()
    except sr.UnknownValueError:
        speak("Sorry, I didn't get that.")
    except sr.RequestError:
        speak("Speech recognition service is down.")
    return ""

# === Command Handler ===
def execute_command(command):
    if "open notepad" in command:
        os.system("start notepad")
        speak("Opening Notepad")
    elif "give your speech" in command:
        speak("It's easy to feel hopeful on a beautiful day like today, but there will be dark days ahead...")
    elif "open youtube" in command:
        webbrowser.open("https://www.youtube.com")
        speak("Opening YouTube")
    elif "shutdown" in command:
        speak("Shutting down your system.")
        os.system("shutdown /s /t 1")
    elif "exit" in command:
        speak("Goodbye!")
        stop_assistant(force_exit=True)
    else:
        speak("Sorry, I can't do that yet.")

# === Main Voice Assistant Loop ===
def assistant_loop():
    porcupine = pvporcupine.create(access_key=ACCESS_KEY, keyword_paths=[WAKE_WORD_PATH])
    pa = pyaudio.PyAudio()
    stream = pa.open(rate=porcupine.sample_rate, channels=1, format=pyaudio.paInt16, input=True, frames_per_buffer=porcupine.frame_length)
    try:
        while assistant_running:
            pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
            result = porcupine.process(pcm)
            if result >= 0:
                print("🎙️ Wake word detected!")
                command = listen_command()
                execute_command(command)
    except Exception as e:
        print("Error in assistant loop:", e)
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()
        porcupine.delete()

# === Stop ===
def stop_assistant(force_exit=False):
    global assistant_running
    assistant_running = False
    if force_exit:
        root.destroy()
        os._exit(0)

# === Run ===
if __name__ == "__main__":
    threading.Thread(target=assistant_loop, daemon=True).start()
    root.mainloop()
