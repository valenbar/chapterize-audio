import subprocess
import signal
import sys
import argparse
import os
import datetime
import json

# Create the parser
parser = argparse.ArgumentParser(description="Generate chapters from detected silence in audio files")

# Add the arguments
parser.add_argument('-i', '--input_audio', type=str, required=True, help="The input audio file")
parser.add_argument('-t', '--threshold', type=int, default=-30, help="The silence threshold in dB (default: -30)")
parser.add_argument('-d', '--duration', type=float, default=2.5, help="The minimum silence duration in seconds (default: 2.5)")

# Parse the arguments
args = parser.parse_args()

# Assign the arguments to variables
input_audio_file = args.input_audio
noise_threshold = args.threshold
duration = args.duration

# Global variable to store silence spots
silence_spots = []


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
    if prompt_yes_no(question="Store intermediate results?", default="no"):
        export_to_cue(silence_spots, input_audio_file)
        export_to_json(silence_spots, input_audio_file)
    sys.exit(0)


# Set the SIGINT handler
signal.signal(signal.SIGINT, sigint_handler)


def convert_seconds_to_mm_ss_ff(seconds):
    seconds = seconds
    total_seconds = int(seconds)
    frames = int((seconds - total_seconds) * 75)
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes:02d}:{seconds:02d}:{frames:02d}"

def detect_silence(input_file, noise_threshold, duration):
    command = [
        'ffmpeg',
        '-i', input_file,
        '-map', '0:a',  # Select only the audio streams
        '-af', f'silencedetect=noise={noise_threshold}dB:d={duration}',
        '-f', 'null',
        '-'
    ]

    # Run FFmpeg command and capture output
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    # Process the output while the process is still running
    silence_start = None
    silence_end = None
    last_end = 0
    for i, line in enumerate(process.stdout):
        if 'silence_start' in line:
            silence_start = float(line.split('silence_start: ')[1].split(' ')[0].replace('\n', ''))
        elif 'silence_end' in line:
            silence_end = float(line.split('silence_end: ')[1].split(' ')[0])
            silence_spots.append((silence_start, silence_end))
            print(
                f"Part duration: {str(datetime.timedelta(seconds=silence_end - last_end)).split('.')[0]}, " +
                f"Next part start: {str(datetime.timedelta(seconds=silence_end)).split('.')[0]}, "
            )
            last_end = silence_end

    process.wait()


def export_to_cue(silence_spots, audio_file):
    output_file = audio_file.rsplit('.', 1)[0] + '.cue'
    digits = len(str(len(silence_spots)))
    with open(output_file, 'w') as file:
        file.write(f"FILE \"{os.path.basename(audio_file)}\" MP3\n")  # Replace with your audio file name
        # initial chapter at 00:00:00
        track_num_str = "1".zfill(digits)  # Add leading zeros
        file.write(f"  TRACK {track_num_str} AUDIO\n")
        file.write(f"    TITLE \"Part {track_num_str}\"\n")
        file.write(f"    INDEX 01 00:00:00\n")
        for track_num, (start, end) in enumerate(silence_spots, start=2):
            if end < 5:
                track_num -= 1
                continue
            track_num_str = str(track_num).zfill(digits)  # Add leading zeros
            file.write(f"  TRACK {track_num_str} AUDIO\n")
            file.write(f"    TITLE \"Part {track_num_str}\"\n")
            file.write(f"    INDEX 01 {convert_seconds_to_mm_ss_ff(end)}\n")
    print(f"Chapters exported to: {output_file}")

def export_to_json(silence_spots, audio_file):
    # output_file = audio_file.rsplit('.', 1)[0] + '.json'
    output_file = "chapters.json"
    data = []
    silence_spots.insert(0, (0, 0))
    # remove first found silence spot if it is less than 5 seconds into the audio
    if silence_spots[1][1] < 5:
        silence_spots.pop(1)
    for i in range(len(silence_spots) - 1):
        window = silence_spots[i:i+2]
        prev = window[0]
        curr = window[1]
        prev_start, prev_end = prev
        curr_start, curr_end = curr
        data.append({
            "id": i,
            "start": prev_end,
            "end": curr_end,
            "title": f"Part {i + 1}"
        })

    with open(output_file, 'w') as file:
        json.dump(data, file, separators=(',', ':'))
    print(f"Chapters exported to: {output_file}")

if __name__ == "__main__":
    if not os.path.isfile(input_audio_file):
        print("Input audio file does not exist")
        sys.exit(1)

    detect_silence(input_audio_file, noise_threshold, duration)
    print(f"Total silence spots detected: {len(silence_spots)}")
    if prompt_yes_no(question="Store cue file?", default="no"):
        export_to_cue(silence_spots, input_audio_file)
    if prompt_yes_no(question="Store chapter.json?", default="no"):
        export_to_json(silence_spots, input_audio_file)
