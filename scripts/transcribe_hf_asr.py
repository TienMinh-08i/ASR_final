import argparse
import csv
import os
import shutil
from pathlib import Path

import torch
from transformers import pipeline


MODEL_ALIASES = {
    "phowhisper-tiny": "vinai/PhoWhisper-tiny",
    "phowhisper-base": "vinai/PhoWhisper-base",
    "phowhisper-small": "vinai/PhoWhisper-small",
    "phowhisper-medium": "vinai/PhoWhisper-medium",
}


def read_rows(root, split):
    with open(root / "data" / "utterances.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if split:
        rows = [row for row in rows if row["split"] == split]
    return rows


def main():
    parser = argparse.ArgumentParser(description="Transcribe ViSE-CS Mini with Hugging Face ASR models.")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--model", default="phowhisper-small")
    parser.add_argument("--split", choices=["train", "dev", "test"], default="test")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    try:
        import imageio_ffmpeg

        ffmpeg_src = Path(imageio_ffmpeg.get_ffmpeg_exe())
        ffmpeg_dir = root / "tools" / "ffmpeg-bin"
        ffmpeg_dir.mkdir(parents=True, exist_ok=True)
        ffmpeg_alias = ffmpeg_dir / "ffmpeg.exe"
        if not ffmpeg_alias.exists():
            shutil.copy2(ffmpeg_src, ffmpeg_alias)
        os.environ["PATH"] = str(ffmpeg_dir) + os.pathsep + os.environ.get("PATH", "")
    except ImportError:
        pass

    model_id = MODEL_ALIASES.get(args.model, args.model)
    rows = read_rows(root, args.split)
    out_path = Path(args.output) if args.output else root / "reports" / f"{args.model}_{args.split}" / f"predictions_{args.model}_{args.split}.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    device = 0 if torch.cuda.is_available() else -1
    dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    print(f"Model: {model_id}")
    print(f"Device: {'cuda' if device == 0 else 'cpu'}")
    print(f"Utterances: {len(rows)}")

    asr = pipeline(
        "automatic-speech-recognition",
        model=model_id,
        torch_dtype=dtype,
        device=device,
    )

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["utt_id", "prediction"])
        writer.writeheader()
        for index, row in enumerate(rows, start=1):
            audio_path = root / row["audio_path"]
            print(f"[{index}/{len(rows)}] {row['utt_id']}")
            result = asr(str(audio_path), generate_kwargs={"language": "vi", "task": "transcribe"})
            writer.writerow({"utt_id": row["utt_id"], "prediction": result["text"].strip()})

    print(f"Wrote: {out_path}")


if __name__ == "__main__":
    main()
