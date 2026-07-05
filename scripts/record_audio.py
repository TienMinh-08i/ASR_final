import argparse
import csv
import ctypes
import sys
import unicodedata
import wave
from datetime import datetime
from pathlib import Path


def configure_console():
    if sys.platform.startswith("win"):
        try:
            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
            ctypes.windll.kernel32.SetConsoleCP(65001)
        except Exception:
            pass
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def remove_accents(text):
    normalized = unicodedata.normalize("NFD", text)
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def load_sounddevice():
    try:
        import sounddevice as sd
    except ImportError:
        print("Missing dependency: sounddevice")
        print("Install with:")
        print("  python -m pip install sounddevice")
        raise SystemExit(1)
    return sd


def read_utterances(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_ascii_prompts(path):
    if not path.exists():
        return {}
    with open(path, newline="", encoding="utf-8") as f:
        return {row["utt_id"]: row["prompt_ascii"] for row in csv.DictReader(f)}


def write_wav(path, frames, sample_rate, channels):
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"".join(frames))


def append_session_log(root, row):
    log_path = root / "data" / "recording_sessions.csv"
    exists = log_path.exists()
    with open(log_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "recorded_at",
                "utt_id",
                "audio_path",
                "speaker_id",
                "sample_rate",
                "channels",
                "duration_seconds",
                "device",
            ],
        )
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def select_rows(rows, start=None, split=None, domain=None, only_missing=False, root=None):
    selected = rows
    if start:
        seen_start = False
        trimmed = []
        for row in selected:
            if row["utt_id"] == start:
                seen_start = True
            if seen_start:
                trimmed.append(row)
        selected = trimmed
    if split:
        selected = [row for row in selected if row["split"] == split]
    if domain:
        selected = [row for row in selected if row["domain"] == domain]
    if only_missing and root:
        selected = [row for row in selected if not (root / row["audio_path"]).exists()]
    return selected


def record_one(sd, out_path, sample_rate, channels, device):
    frames = []

    def callback(indata, frame_count, time_info, status):
        if status:
            print(f"Audio status: {status}", file=sys.stderr)
        frames.append(indata.copy().tobytes())

    input("Press Enter to START recording...")
    print("Recording... press Enter to STOP.")
    start = datetime.now()
    with sd.InputStream(
        samplerate=sample_rate,
        channels=channels,
        dtype="int16",
        callback=callback,
        device=device,
    ):
        input()
    end = datetime.now()
    duration = (end - start).total_seconds()
    write_wav(out_path, frames, sample_rate, channels)
    return duration


def main():
    configure_console()

    parser = argparse.ArgumentParser(
        description="Record utterance-level WAV files for ViSE-CS Mini."
    )
    parser.add_argument(
        "--root",
        default=str(Path(__file__).resolve().parents[1]),
        help="Dataset root folder. Default: parent folder of scripts/.",
    )
    parser.add_argument("--sample-rate", type=int, default=16000)
    parser.add_argument("--channels", type=int, default=1)
    parser.add_argument("--device", default=None, help="Input device name or index.")
    parser.add_argument("--speaker-id", default=None, help="Speaker id for session log.")
    parser.add_argument("--start", default=None, help="Start from a specific utt_id.")
    parser.add_argument("--split", choices=["train", "dev", "test"], default=None)
    parser.add_argument("--domain", default=None)
    parser.add_argument("--only-missing", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--show-accents",
        action="store_true",
        help="Also show the original Vietnamese sentence with accents.",
    )
    parser.add_argument("--list-devices", action="store_true")
    args = parser.parse_args()

    sd = load_sounddevice()

    if args.list_devices:
        print(sd.query_devices())
        return

    root = Path(args.root).resolve()
    utterance_path = root / "data" / "utterances.csv"
    prompt_path = root / "data" / "recording_prompts_ascii.csv"
    rows = read_utterances(utterance_path)
    ascii_prompts = read_ascii_prompts(prompt_path)
    rows = select_rows(
        rows,
        start=args.start,
        split=args.split,
        domain=args.domain,
        only_missing=args.only_missing,
        root=root,
    )

    if not rows:
        print("No utterances selected.")
        return

    print(f"Dataset root: {root}")
    print(f"Selected utterances: {len(rows)}")
    print(f"Sample rate: {args.sample_rate} Hz")
    print()

    for index, row in enumerate(rows, start=1):
        out_path = root / row["audio_path"]
        speaker_id = args.speaker_id or row.get("speaker_id", "")

        print("=" * 72)
        print(f"[{index}/{len(rows)}] {row['utt_id']} | {row['split']} | {row['domain']}")
        print(f"Speaker: {speaker_id}")
        print(f"Output: {out_path}")
        print()
        transcript = row["transcript"]
        prompt = ascii_prompts.get(row["utt_id"], remove_accents(transcript))
        print(prompt)
        if args.show_accents:
            print(f"Original: {transcript}")
        print()

        if out_path.exists() and not args.overwrite:
            answer = input("File exists. Re-record it? [y/N] ").strip().lower()
            if answer != "y":
                print("Skipped.")
                continue

        duration = record_one(
            sd,
            out_path=out_path,
            sample_rate=args.sample_rate,
            channels=args.channels,
            device=args.device,
        )
        append_session_log(
            root,
            {
                "recorded_at": datetime.now().isoformat(timespec="seconds"),
                "utt_id": row["utt_id"],
                "audio_path": row["audio_path"],
                "speaker_id": speaker_id,
                "sample_rate": args.sample_rate,
                "channels": args.channels,
                "duration_seconds": f"{duration:.2f}",
                "device": args.device or "default",
            },
        )
        print(f"Saved. Duration: {duration:.2f}s")

    print("=" * 72)
    print("Done.")


if __name__ == "__main__":
    main()
