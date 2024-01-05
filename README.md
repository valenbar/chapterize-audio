# Chapterize Audio

This script generates chapters for an audio file by detecting silence. The chapters are stored to a CUE file and a JSON file.

## Prerequisites

- Python
- [FFmpeg](https://ffmpeg.org/) (Make sure it is installed and added to the system's PATH)


## Usage

Example usage:

```bash
python chapterize.py -i <audio.mp3>  -t <dB threshold> -d <silence duration>
```

Options:

```text
  -h, --help            show this help message and exit
  -i INPUT_AUDIO, --input_audio INPUT_AUDIO
                        The input audio file
  -t THRESHOLD, --threshold THRESHOLD
                        The silence threshold in dB (default: -30)
  -d DURATION, --duration DURATION
                        The minimum silence duration in seconds (default: 2.5)
```

Output:

```bash
./audio.cue
./chapters.json
```

CUE file output:

    FILE "audio.mp3" MP3
    TRACK 1 AUDIO
        TITLE "Part 1"
        INDEX 01 00:00:00
    TRACK 3 AUDIO
        TITLE "Part 3"
        INDEX 01 00:14:37
    TRACK 4 AUDIO
        TITLE "Part 4"
        INDEX 01 01:56:36

JSON file output:

```json
[
    {
        "id": "0",
        "title": "Part 1",
        "start": "00:00:00",
        "end": "00:14:37"
    },
    {
        "id": "1",
        "title": "Part 3",
        "start": "00:14:37",
        "end": "01:56:36"
    },
    {
        "id": "2",
        "title": "Part 4",
        "start": "01:56:36",
        "end": "02:00:00"
    }
]
```


## Acknowledgements

- [FFmpeg](https://ffmpeg.org/)
