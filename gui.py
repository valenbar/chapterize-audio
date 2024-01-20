import tkinter as tk
from tkinter import filedialog

def select_audio_file():
    filename = filedialog.askopenfilename(filetypes=[("Audio files", "*.mp3, *.m4b")])
    if filename:
        audio_file_var.set(filename)
    print(audio_file_var)

def start_processing():
    audio_file = audio_file_var.get()
    if audio_file:
        # Call your function here
        print(f"Processing {audio_file}")
    else:
        print("No audio file selected")

WINDOW_MIN_WIDTH = 600
WINDOW_MIN_HEIGHT = 300

window = tk.Tk()
# set min size
window.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
# window.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
window.geometry("")

window.rowconfigure(0, weight=0, minsize=20)  # Make the first row fill the entire height
window.rowconfigure(1, weight=1, minsize=WINDOW_MIN_HEIGHT - 20)  # Make the second row fill the remaining height
window.columnconfigure(0, weight=1)  # Make each column fill the entire width
window.columnconfigure(1, weight=1)  # Make each column fill the entire width
window.columnconfigure(2, weight=1)  # Make each column fill the entire width


label_input = tk.Label(text="Input", justify="left")
label_options = tk.Label(text="Options")
label_output = tk.Label(text="Output")

label_input.grid(row=0, column=0)
label_options.grid(row=0, column=1)
label_output.grid(row=0, column=2)



# Create frames for each column
input_frame = tk.Frame()
input_frame.grid(row=1, column=0, padx=10, pady=10)

options_frame = tk.Frame()
options_frame.grid(row=1, column=1, padx=10, pady=10)

output_frame = tk.Frame()
output_frame.grid(row=1, column=2, padx=10, pady=10)

# Rest of the code...

# Input column
input_label = tk.Label(input_frame, text="Input")
input_label.pack()

audio_file_var = tk.StringVar()
select_button = tk.Button(input_frame, text="Select audio file", command=select_audio_file)
select_button.pack()


# Checkbox for boolean options
# silence dB threshold input
threshold_label = tk.Label(options_frame, text="Threshold (dB):")
threshold_label.pack()
threshold = tk.Entry(options_frame)
threshold.insert(0, "-30")
threshold.pack()

# silence duration input
silence_duration_label = tk.Label(options_frame, text="Silence duration (s):")
silence_duration_label.pack()
silence_duration = tk.Entry(options_frame)
silence_duration.insert(0, "2.5")
silence_duration.pack()

# custom chapter label input
label_label = tk.Label(options_frame, text="Custom chapter label:")
label_label.pack()
label = tk.Entry(options_frame)
label.insert(0, "Chapter")
label.pack()

# checkbox to enable transcribing
transcribing_var = tk.BooleanVar()
transcribing_var.set(True)
transcribing_checkbox = tk.Checkbutton(options_frame, text="Transcribing", variable=transcribing_var)
transcribing_checkbox.pack()

# Dropdown menu for language selection
language_var = tk.StringVar()
language_var.set("English")
options = ["English", "German"]
dropdown_menu = tk.OptionMenu(options_frame, language_var, *options)
dropdown_menu.pack()

# transcription duration input
transcript_duration_label = tk.Label(options_frame, text="Transcription duration (s):")
transcript_duration_label.pack()
transcript_duration = tk.Entry(options_frame)
transcript_duration.insert(0, "2")
transcript_duration.pack()

options_label = tk.Label(options_frame, text="Options")
options_label.pack()

output_frame.rowconfigure(0, weight=1, minsize=20)  # Make the first row fill the entire height
output_frame.rowconfigure(1, weight=5)  # Make the second row fill the remaining height

start_button = tk.Button(output_frame, text="Start processing", command=start_processing)
start_button.grid(row=0, column=0, sticky="n")

output_text = tk.Text(output_frame)
output_text.grid(row=1, column=0, sticky="nsew")


window.mainloop()