import speech_recognition as sr
import subprocess
import os
import atexit

process = None

def cleanup():
    if process is not None:
        process.kill()
        process.wait()

    if os.path.exists('./temp'):
        # remove temp folder and its contents
        for file in os.listdir('./temp'):
            os.remove(f'./temp/{file}')
        os.rmdir('./temp')


def transcribe_audio(audio_file, start, end, language) -> str:
    if not os.path.exists('./temp'):
        raise Exception("Temp folder does not exist")

    command = [
        'ffmpeg',
        '-ss', str(start),
        '-to', str(end),
        '-i', audio_file,
        '-loglevel', 'error',
        '-y', './temp/temp.wav'
    ]

    lang_dict = {
        "english" : "en-US",
        "german" : "de-DE",
    }
    language = lang_dict.get(language, "en-IN")

    global process

    process = subprocess.Popen(command, shell=False)
    process.wait()

    r = sr.Recognizer()

    # transcribe audio file
    with sr.AudioFile('./temp/temp.wav') as source:
        audio = r.record(source)
        try:
            text = r.recognize_google(audio, language = language, show_all = False)
        except sr.UnknownValueError:
            text = "-"
    return text


def main():
    print("Transcribing audio...")
    audio_file = "./audio/all_systems_red.m4b"
    start = 0
    end = 3
    text = transcribe_audio(audio_file, start, end, "english")
    print(text)


if __name__ == "__main__":
    main()

atexit.register(cleanup)