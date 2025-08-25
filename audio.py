"""
Sub2Anki - Create Anki flashcards for intensive listening practice from audio and subtitle files.

This script processes audio files with their corresponding LRC/SRT subtitle files to create
interactive Anki decks for language learning. Each subtitle line becomes a flashcard with
audio playback controls, typing practice, and mistake tracking features.
"""

import random
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import genanki
from pydub import AudioSegment

# Import Anki template definitions
from template import ANKI_MODEL


# --- Data Classes ---
@dataclass
class SubtitleLine:
    """Represents a single line of a subtitle file."""

    start_time_ms: int
    end_time_ms: int
    text: str
    translation: Optional[str] = None


@dataclass
class DeckConfig:
    """Configuration for a single Anki deck generation task."""

    name: str
    audio_file: Path
    subtitle_file: Path
    output_deck_name: str
    output_deck_filename: Path


# --- Configuration Profiles ---
# Define configurations for different audio/subtitle pairs
# Each configuration specifies the input files and output deck settings
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

# --- Subtitle Parsers ---


def srt_time_to_ms(time_str: str) -> int:
    """Converts SRT time format (HH:MM:SS,ms) to milliseconds."""
    parts = re.split(r"[:,]", time_str)
    return (
        int(parts[0]) * 3600000
        + int(parts[1]) * 60000
        + int(parts[2]) * 1000
        + int(parts[3])
    )


def parse_srt(content: str) -> List[SubtitleLine]:
    """Parses SRT file content with optional translations."""
    lines = []
    # Regex to capture index, start time, end time, and text
    pattern = re.compile(
        r"(\d+)\n"
        r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n"
        r"([\s\S]+?)(?=\n\n\d+\n|\Z)",
        re.MULTILINE,
    )
    for match in pattern.finditer(content):
        start_time_ms = srt_time_to_ms(match.group(2))
        end_time_ms = srt_time_to_ms(match.group(3))
        text_block = match.group(4).strip().split("\n")
        text = text_block[0].strip()
        translation = text_block[1].strip() if len(text_block) > 1 else None
        lines.append(SubtitleLine(start_time_ms, end_time_ms, text, translation))
    return lines


def parse_lrc(content: str) -> List[SubtitleLine]:
    """Parses LRC file content with optional translations on subsequent lines."""
    lines = []
    content_lines = [
        line.strip() for line in content.strip().split("\n") if line.strip()
    ]

    timed_lines = []
    i = 0
    while i < len(content_lines):
        line = content_lines[i]
        match = re.match(r"^\[(\d{2}):(\d{2})\.(\d{2,3})\](.*)", line)
        if match:
            minutes, seconds, hundredths, text = match.groups()
            if len(hundredths) == 2:
                ms = int(hundredths) * 10
            else:
                ms = int(hundredths)
            time_ms = int(minutes) * 60000 + int(seconds) * 1000 + ms

            translation = None
            if i + 1 < len(content_lines) and not re.match(
                r"^\[(\d{2}):(\d{2})\.(\d{2,3})\]", content_lines[i + 1]
            ):
                translation = content_lines[i + 1]
                i += 1  # Consume translation line

            timed_lines.append(
                {"time_ms": time_ms, "text": text.strip(), "translation": translation}
            )
        i += 1

    for i, timed_line in enumerate(timed_lines):
        start_time_ms = timed_line["time_ms"]
        text = timed_line["text"]
        translation = timed_line["translation"]

        if i + 1 < len(timed_lines):
            end_time_ms = timed_lines[i + 1]["time_ms"]
        else:
            end_time_ms = -1

        if text:
            lines.append(SubtitleLine(start_time_ms, end_time_ms, text, translation))
    return lines


def parse_subtitles(subtitle_file: Path) -> Optional[List[SubtitleLine]]:
    """
    Parses a subtitle file, dispatching to the correct parser based on extension.
    """
    try:
        with open(subtitle_file, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: Subtitle file not found -> {subtitle_file}")
        return None
    except Exception as e:
        print(f"Error reading subtitle file {subtitle_file}: {e}")
        return None

    extension = subtitle_file.suffix.lower()
    if extension == ".lrc":
        return parse_lrc(content)
    elif extension == ".srt":
        return parse_srt(content)
    else:
        print(f"Error: Unsupported subtitle format: {extension}")
        return None


# --- Core Logic ---


def create_anki_deck(config: DeckConfig):
    """
    Generates an Anki deck based on the provided configuration.
    """
    print(f"--- Starting process for '{config.name}' ---")

    # 1. Validate input files
    if not config.audio_file.exists():
        print(f"Error: Audio file not found -> {config.audio_file}")
        return
    if not config.subtitle_file.exists():
        print(f"Error: Subtitle file not found -> {config.subtitle_file}")
        return

    print("1. Parsing subtitle file...")
    subs = parse_subtitles(config.subtitle_file)
    if not subs:
        print("Failed to parse subtitles. Aborting.")
        return
    print(f"Successfully parsed {len(subs)} subtitle lines.")

    print("2. Loading audio file...")
    try:
        audio = AudioSegment.from_file(config.audio_file)
    except Exception as e:
        print(f"Error loading audio file: {e}")
        print("Please ensure ffmpeg is installed and in your system's PATH.")
        return

    # Create a temporary directory for media clips
    media_dir = Path(f"media_{config.name}")
    media_dir.mkdir(exist_ok=True)

    print("3. Slicing audio and preparing Anki notes...")
    notes = []
    media_files = []
    deck_id = random.randrange(1 << 30, 1 << 31)

    for i, line in enumerate(subs):
        start_time_ms = line.start_time_ms
        end_time_ms = line.end_time_ms
        text = line.text

        # For LRC, the last line's end time needs to be the audio's end
        if end_time_ms == -1:
            end_time_ms = len(audio)

        if not text.strip():
            continue

        # Slice audio
        clip = audio[start_time_ms:end_time_ms]

        # Generate a safe and unique filename for the clip
        safe_text = "".join(c for c in text if c.isalnum() or c in " _-").rstrip()
        clip_filename = f"{config.name}_{i+1:03d}_{safe_text[:20]}.mp3"
        clip_path = media_dir / clip_filename

        # Export audio clip
        clip.export(clip_path, format="mp3")

        card_uuid = str(uuid.uuid4())
        translation_text = line.translation if line.translation else ""
        fields = [
            f"[sound:{clip_filename}]",
            clip_filename,
            text,
            translation_text,
            card_uuid,
        ]
        note = genanki.Note(model=ANKI_MODEL, fields=fields)
        notes.append(note)
        media_files.append(str(clip_path))

        print(f"  - Processed line {i+1}: {text[:40]}...")

    print("4. Generating Anki deck package (.apkg)...")
    deck = genanki.Deck(deck_id, config.output_deck_name)
    for note in notes:
        deck.add_note(note)

    package = genanki.Package(deck)
    package.media_files = media_files
    package.write_to_file(config.output_deck_filename)

    print("\n🎉 Success!")
    print(f"Anki deck '{config.output_deck_filename}' created for '{config.name}'.")
    print("Import it into Anki to start learning.")
    print("-" * (len(config.name) + 22))


if __name__ == "__main__":
    import argparse

    # --- Command-Line Argument Parsing ---
    parser = argparse.ArgumentParser(
        description="Create Anki decks from audio and subtitle files."
    )
    parser.add_argument(
        "config_name",
        nargs="?",  # Make the argument optional
        default="all",  # Default to 'all' if no argument is provided
        choices=list(CONFIGS.keys()) + ["all"],
        help=(
            "The name of the configuration to run (e.g., 'npr', 'mw'). "
            "If set to 'all' or not provided, all configurations will be run."
        ),
    )
    args = parser.parse_args()

    # --- Main Execution Logic ---
    if args.config_name == "all":
        print("Running for all configurations...")
        for config_key in CONFIGS:
            create_anki_deck(CONFIGS[config_key])
    else:
        print(f"Running for specific configuration: '{args.config_name}'")
        create_anki_deck(CONFIGS[args.config_name])
