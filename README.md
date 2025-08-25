# Sub2Anki

A powerful Python tool that automatically creates Anki flashcards for intensive listening practice from audio files (MP3, M4A, MOV) and their corresponding subtitle files (LRC, SRT).

## Features

- **Automatic Card Generation**: Creates Anki decks from audio and subtitle files with minimal configuration
- **Multiple Format Support**: Works with both LRC and SRT subtitle formats
- **Smart Audio Slicing**: Automatically slices audio files based on subtitle timestamps
- **Interactive Dictation Cards**: Custom Anki template with playback controls, speed adjustment, and hint system
- **Mistake Tracking**: Records and displays typing mistakes for review on the back of cards
- **Bilingual Support**: Handles both monolingual and bilingual subtitles
- **Batch Processing**: Process multiple configurations in a single run

## How It Works

Sub2Anki takes your audio files and their corresponding subtitles, then:

1. Parses the subtitle file to extract timing and text information
2. Slices the audio file into individual clips based on subtitle timestamps
3. Creates interactive Anki cards with:
   - Audio playback controls
   - Speed adjustment (0.5x, 0.75x, normal)
   - Loop toggle
   - Real-time typing feedback
   - Hint system (type # to reveal next word)
   - Mistake tracking and review

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/sub2anki.git
   cd sub2anki
   ```

2. **Install required dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install FFmpeg** (required for audio processing):
   - **macOS**: `brew install ffmpeg`
   - **Ubuntu/Debian**: `sudo apt install ffmpeg`
   - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

## Configuration

### Directory Structure

Organize your files in the following structure:

```
sub2anki/
├── audio.py              # Main script
├── npr/
│   ├── NPR-2025-08-24.lrc
│   └── NPR-2025-08-24.m4a
├── mw/
│   ├── wd20250824.srt
│   └── wd20250824.mov
└── ...
```

### Configuration Profiles

Edit the `CONFIGS` dictionary in `audio.py` to set up your audio/subtitle pairs:

```python
CONFIGS = {
    "npr": DeckConfig(
        name="npr",
        audio_file=Path("./npr/NPR-2025-08-24.m4a"),
        subtitle_file=Path("./npr/NPR-2025-08-24.lrc"),
        output_deck_name="NPR",
        output_deck_filename=Path("npr_deck.apkg"),
    ),
    "mw": DeckConfig(
        name="mw",
        audio_file=Path("./mw/wd20250824.mov"),
        subtitle_file=Path("./mw/wd20250824.srt"),
        output_deck_name="MW",
        output_deck_filename=Path("mw_deck.apkg"),
    ),
}
```

### Subtitle Format Support

#### LRC Format
LRC files should follow this format:
```
[00:00.00]First sentence text
Translation (optional second line)
[00:05.50]Second sentence text
Translation (optional second line)
```

#### SRT Format
SRT files should follow this format:
```
1
00:00:00,000 --> 00:00:05,500
First sentence text
Translation (optional second line)

2
00:00:05,500 --> 00:00:10,250
Second sentence text
Translation (optional second line)
```

## Usage

### Process All Configurations
```bash
python audio.py
# or
python audio.py all
```

### Process Specific Configuration
```bash
python audio.py npr
python audio.py mw
```

### Importing into Anki

1. Open Anki
2. Click "Import File" (Ctrl+Shift+I)
3. Select the generated `.apkg` file
4. Click "Import"

## Card Template Features

### Front Side
- Audio player with playback controls
- Speed adjustment buttons (0.5x, 0.75x, Normal)
- Loop toggle button
- Real-time typing feedback with color coding:
  - Green: Correct words
  - Red with underline: Incorrect words
  - Hint system: Type `#` to reveal the next word
- Visual hint display showing sentence structure

### Back Side
- Audio player with same controls
- Original sentence with highlighted mistake words
- Translation (if provided in subtitles)
- Mistakes table showing:
  - Correct word
  - Your incorrect attempts

## Requirements

- Python 3.7+
- FFmpeg
- Required Python packages (see requirements.txt):
  - genanki
  - pydub

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.