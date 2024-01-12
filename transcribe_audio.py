import speech_recognition as sr
import subprocess
import os
import sys


def sigint_handler(signal, frame):
    print("Removing temp file...")
    if os.path.exists('temp.wav'):
        os.remove('temp.wav')
    sys.exit(0)

def transcribe_audio(audio_file, start, end, language) -> str:
    command = [
        'ffmpeg',
        '-i', audio_file,
        '-ss', str(start),
        '-to', str(end),
        '-c:a', 'pcm_s16le',
        '-ac', '1',
        '-ar', '16000',
        '-loglevel', 'error',
        '-y', 'temp.wav'
    ]

    lang_dict = {
        "english" : "en-US",
        "german" : "de-DE",
    }
    language = lang_dict.get(language, "en-IN")

    process = subprocess.Popen(command)
    process.wait()

    r = sr.Recognizer()

    # transcribe audio file
    with sr.AudioFile('temp.wav') as source:
        audio = r.record(source)
        try:
            text = r.recognize_google(audio, language = language, show_all = False)
        except sr.UnknownValueError:
            text = "-"
        # print(text)

    os.remove('temp.wav')
    return text


def main():
    print("Transcribing audio...")
    audio_file = "./audio/all_systems_red.m4b"
    start = 0
    end = 3
    transcribe_audio(audio_file, start, end)


if __name__ == "__main__":
    main()