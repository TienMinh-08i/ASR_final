import csv
import wave
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    utterance_path = root / "data" / "utterances.csv"

    with open(utterance_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    missing = []
    invalid = []
    durations = []

    for row in rows:
        wav_path = root / row["audio_path"]
        if not wav_path.exists():
            missing.append(row["utt_id"])
            continue
        try:
            with wave.open(str(wav_path), "rb") as wf:
                frames = wf.getnframes()
                sample_rate = wf.getframerate()
                channels = wf.getnchannels()
                duration = frames / float(sample_rate)
                durations.append(duration)
                if duration < 0.4 or channels != 1:
                    invalid.append((row["utt_id"], f"{duration:.2f}s", channels))
        except wave.Error as exc:
            invalid.append((row["utt_id"], f"wave error: {exc}", ""))

    print(f"Total utterances: {len(rows)}")
    print(f"Recorded: {len(rows) - len(missing)}")
    print(f"Missing: {len(missing)}")
    if durations:
        print(f"Total duration: {sum(durations) / 60:.2f} minutes")
        print(f"Average duration: {sum(durations) / len(durations):.2f} seconds")

    if missing:
        print("\nMissing utt_id:")
        for utt_id in missing:
            print(f"- {utt_id}")

    if invalid:
        print("\nSuspicious files:")
        for item in invalid:
            print(f"- {item[0]} | {item[1]} | channels={item[2]}")


if __name__ == "__main__":
    main()
