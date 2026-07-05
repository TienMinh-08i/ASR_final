import argparse
import csv
import shutil
import os
import subprocess
import sys
from pathlib import Path


def read_utterances(path, split=None):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if split:
        rows = [row for row in rows if row["split"] == split]
    return rows


def check_audio(root, rows):
    missing = []
    for row in rows:
        if not (root / row["audio_path"]).exists():
            missing.append(row["utt_id"])
    return missing


def transcribe_with_whisper(root, rows, output_path, model_name):
    try:
        import imageio_ffmpeg

        ffmpeg_exe = Path(imageio_ffmpeg.get_ffmpeg_exe())
        ffmpeg_dir = root / "tools" / "ffmpeg-bin"
        ffmpeg_dir.mkdir(parents=True, exist_ok=True)
        ffmpeg_alias = ffmpeg_dir / "ffmpeg.exe"
        if not ffmpeg_alias.exists():
            shutil.copy2(ffmpeg_exe, ffmpeg_alias)
        os.environ["PATH"] = str(ffmpeg_dir) + os.pathsep + os.environ.get("PATH", "")
    except ImportError:
        pass

    # Some numba/coverage combinations fail during Whisper import. Whisper does
    # not need coverage collection, so hide it inside this process only.
    sys.modules["coverage"] = None

    try:
        import whisper
    except ImportError:
        print("Missing dependency: whisper")
        print("Install with:")
        print("  python -m pip install -U openai-whisper")
        raise SystemExit(1)

    print(f"Loading Whisper model: {model_name}")
    model = whisper.load_model(model_name)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["utt_id", "prediction"])
        writer.writeheader()
        for index, row in enumerate(rows, start=1):
            audio_path = root / row["audio_path"]
            print(f"[{index}/{len(rows)}] Transcribing {row['utt_id']}")
            result = model.transcribe(str(audio_path), language="vi", fp16=False)
            writer.writerow(
                {
                    "utt_id": row["utt_id"],
                    "prediction": result.get("text", "").strip(),
                }
            )
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Check recordings, optionally transcribe, then evaluate ViSE-CS Mini."
    )
    parser.add_argument(
        "--root",
        default=str(Path(__file__).resolve().parents[1]),
        help="Dataset root. Default: parent folder of scripts/.",
    )
    parser.add_argument("--split", choices=["train", "dev", "test"], default="test")
    parser.add_argument("--predictions", default=None)
    parser.add_argument(
        "--whisper-model",
        default=None,
        help="Transcribe audio with local openai-whisper model, e.g. tiny, base, small.",
    )
    parser.add_argument("--allow-missing-audio", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    utterances = root / "data" / "utterances.csv"
    lexicon = root / "data" / "lexicon.csv"
    report_name = args.whisper_model if args.whisper_model else Path(args.predictions).stem
    report_dir = root / "reports" / f"{report_name}_{args.split}"
    report_dir.mkdir(parents=True, exist_ok=True)

    rows = read_utterances(utterances, split=args.split)
    missing_audio = check_audio(root, rows)
    print(f"Split: {args.split}", flush=True)
    print(f"Utterances: {len(rows)}", flush=True)
    print(f"Missing audio: {len(missing_audio)}", flush=True)

    if missing_audio and not args.allow_missing_audio:
        print("Missing audio files:")
        for utt_id in missing_audio:
            print(f"- {utt_id}")
        print()
        print("Record missing files first, or pass --allow-missing-audio if you only want to score predictions.")
        raise SystemExit(1)

    if args.predictions:
        predictions = Path(args.predictions).resolve()
    elif args.whisper_model:
        predictions = report_dir / f"predictions_whisper_{args.whisper_model}_{args.split}.csv"
        transcribe_with_whisper(root, rows, predictions, args.whisper_model)
    else:
        print("Provide --predictions PATH or --whisper-model tiny/base/small.")
        raise SystemExit(2)

    cmd = [
        sys.executable,
        str(root / "scripts" / "evaluate_asr.py"),
        str(utterances),
        str(predictions),
        "--lexicon",
        str(lexicon),
        "--split",
        args.split,
        "--output-dir",
        str(report_dir),
    ]
    print(flush=True)
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
