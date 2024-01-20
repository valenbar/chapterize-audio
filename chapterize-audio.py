import subprocess
import signal
import sys
import argparse
import os
import datetime
import json
from transcribe_audio import transcribe_audio, sigint_handler as transcribe_sigint_handler

MIN_FIRST_CHAPTER_DURATION = 5
MIN_LAST_CHAPTER_DURATION = 3
TRANSCRIPTION_START_SHIFT = -0.3

# Create the parser
parser = argparse.ArgumentParser(description="Generate chapters from detected silence in audio files")

# Add the arguments
parser.add_argument('-i', '--input_audio', type=str, required=False, help="The input audio file (default: m4b or mp3 file in current directory)")
parser.add_argument('-t', '--threshold', type=int, default=-30, help="The silence threshold in dB (default: -30)")
parser.add_argument('-d', '--duration', type=float, default=2.5, help="The minimum silence duration in seconds (default: 2.5)")
parser.add_argument('-l', '--label', type=str, default="Part", help="The label to prefix the chapter nr. (default: Part)")
parser.add_argument('-ls', '--label-start-index', type=int, default=1, help="The start index of the chapter nr. (default: 1)")
parser.add_argument('--transcription', action=argparse.BooleanOptionalAction, default=True, help="Enable transcribing of chapter entry (default: True)")
parser.add_argument('--language', type=str, default="english", help="The language to use for transcribing (default: english)");
parser.add_argument('--transcript-duration', type=float, default=3, help="The duration of the audio to transcribe (default: 3)")

args = parser.parse_args()

#Assign the arguments to variables
input_audio_file: str = args.input_audio
noise_threshold: int = args.threshold
duration: float = args.duration
label: str = args.label
label_start_index: int = args.label_start_index
transcribing: bool = args.transcription
language: str = args.language
transcript_duration: float = args.transcript_duration

# Global variable to store silence spots
silence_spots = []

transcript_labels = True


def prompt_yes_no(question, default="no"):
    valid = {"yes": True, "y": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


def sigint_handler(signal, frame):
    # if prompt_yes_no(question="Store intermediate results?", default="no"):
    #     export_to_cue(silence_spots, input_audio_file)
    #     export_to_json(silence_spots, input_audio_file)
    if transcribing:
        transcribe_sigint_handler(signal, frame)
    sys.exit(0)


# Set the SIGINT handler
signal.signal(signal.SIGINT, sigint_handler)


def convert_seconds_to_mm_ss_ff(seconds):
    seconds = seconds
    total_seconds = int(seconds)
    frames = int((seconds - total_seconds) * 75)
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes:02d}:{seconds:02d}:{frames:02d}"

def get_audio_duration(audio_file):
    # find total duration of audio file in seconds
    command = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        audio_file
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    process.wait()
    total_length = float(process.stdout.read().strip())
    return total_length

def detect_silence(input_file, noise_threshold, duration):
    command = [
        'ffmpeg',
        '-i', input_file,
        '-af', f'silencedetect=noise={noise_threshold}dB:d={duration}',
        '-f', 'null',
        '-'
    ]

    # Run FFmpeg command and capture output
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    # Transcribe beginning
    chapter_start = 0
    print(f"Chapter start: {str(datetime.timedelta(seconds=chapter_start)).split('.')[0]}", end='', flush=True)
    if transcribing:
        text = transcribe_audio(audio_file=input_audio_file, start=chapter_start, end=transcript_duration, language=language)
        print(f" - {text}")
    else:
        print(f" - {label} {label_start_index}")
        text = "-"

    silence_spots.append((chapter_start, text))

    total_length = get_audio_duration(input_file)
    for line in process.stdout:
        if 'silence_end' in line:
            chapter_start = float(line.split('silence_end: ')[1].split(' ')[0])
            if chapter_start < MIN_FIRST_CHAPTER_DURATION:
                # don't add chapter within 5 seconds of the initial chapter
                continue
            if chapter_start > total_length - MIN_LAST_CHAPTER_DURATION:
                break

            print(f"Chapter start: {str(datetime.timedelta(seconds=chapter_start)).split('.')[0]}", end='', flush=True)
            if transcribing:
                text = transcribe_audio(
                    audio_file=input_file,
                    start=chapter_start + TRANSCRIPTION_START_SHIFT,
                    end=chapter_start + transcript_duration,
                    language=language
                )
                print(f" - {text}")
            else:
                print(f" - {label} {len(silence_spots) + label_start_index}")
                text = "-"
            silence_spots.append((chapter_start, text))

    process.wait()


def export_to_cue(silence_spots, audio_file):
    output_file = audio_file.rsplit('.', 1)[0] + '.chapterized.cue'
    digits = len(str(len(silence_spots)))
    with open(output_file, 'w') as file:
        file.write(f"FILE \"{os.path.basename(audio_file)}\" MP3\n")  # Replace with your audio file name
        for track_num, (timestamp, text) in enumerate(silence_spots, start=label_start_index):
            track_num_str = str(track_num).zfill(digits)  # Add leading zeros
            file.write(f"  TRACK {track_num_str} AUDIO\n")
            if transcribing and transcript_labels:
                file.write(f"    TITLE \"{text}\"\n")
            else:
                file.write(f"    TITLE \"{label} {track_num_str}\"\n")
            file.write(f"    INDEX 01 {convert_seconds_to_mm_ss_ff(timestamp)}\n")
    print(f"Chapters exported to: {output_file}")

def export_to_json(silence_spots, audio_file):
    output_file = audio_file.rsplit('.', 1)[0] + '.chapterized.json'
    data = []
    total_length = get_audio_duration(audio_file)
    silence_spots.append((total_length, "-"))

    for i in range(len(silence_spots) - 1):
        window = silence_spots[i:i+2]
        prev = window[0]
        curr = window[1]
        prev_timestamp, prev_text = prev
        curr_timestamp, _ = curr

        if transcribing and transcript_labels:
            data.append({
                "id": i,
                "start": prev_timestamp,
                "end": curr_timestamp,
                "title": f"{prev_text}"
            })
        else:
            data.append({
                "id": i,
                "start": prev_timestamp,
                "end": curr_timestamp,
                "title": f"{label} {i + label_start_index}"
            })

    with open(output_file, 'w') as file:
        json.dump(data, file, separators=(',', ':'))
    print(f"Chapters exported to: {output_file}")

def audio_file_in_directory() -> str:
    for file in os.listdir("."):
        if file.endswith(".m4b") or file.endswith(".mp3"):
            return file
    return None

if __name__ == "__main__":
    if input_audio_file is None:
        # find m4b or mp3 file in current directory
        input_audio_file = audio_file_in_directory()
        if input_audio_file is None:
            print("No input audio file given and no m4b or mp3 file found in directory")
            sys.exit(1)
        else:
            print(f"Using: {input_audio_file} as input audio file\n")
    elif not os.path.isfile(input_audio_file):
        print("Given input audio file does not exist")
        sys.exit(1)

    detect_silence(input_audio_file, noise_threshold, duration)
    print(f"Total silence spots detected: {len(silence_spots)}")
    if transcribing:
        if not prompt_yes_no(question="Use transcriptions as chapter lables?", default="yes"):
            transcript_labels = False
    if prompt_yes_no(question="Store cue file?", default="yes"):
        export_to_cue(silence_spots, input_audio_file)
    if prompt_yes_no(question="Store chapter.json?", default="yes"):
        export_to_json(silence_spots, input_audio_file)
