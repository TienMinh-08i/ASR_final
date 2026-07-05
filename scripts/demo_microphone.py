import argparse
import ctypes
import os
import shutil
import sys
import wave
from datetime import datetime
from pathlib import Path

from demo_system import print_block, print_scores, score_one
from evaluate_asr import load_terms
from postprocess_predictions import correct_prediction


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


def ensure_ffmpeg(root):
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


def load_sounddevice():
    try:
        import sounddevice as sd
    except ImportError:
        print("Missing dependency: sounddevice")
        print("Install with: python -m pip install -r requirements-recording.txt")
        raise SystemExit(1)
    return sd


def write_wav(path, frames, sample_rate, channels):
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"".join(frames))


def record_audio(path, sample_rate, channels, device):
    sd = load_sounddevice()
    frames = []

    def callback(indata, frame_count, time_info, status):
        if status:
            print(f"Audio status: {status}", file=sys.stderr)
        frames.append(indata.copy().tobytes())

    input("Press Enter to START recording from microphone...")
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
    duration = (datetime.now() - start).total_seconds()
    write_wav(path, frames, sample_rate, channels)
    return duration


DEFAULT_PROMPT = (
    "Vietnamese and English software engineering speech. "
    "Important terms: graphql resolver, batch request, n plus one query, "
    "dockerfile, multi stage build, feature flag, oauth callback, playwright trace, "
    "service worker cache, unique index, regression test, keyboard navigation."
)


def transcribe(audio_path, model_name, root, language, initial_prompt):
    ensure_ffmpeg(root)
    sys.modules["coverage"] = None
    try:
        import whisper
    except ImportError:
        print("Missing dependency: openai-whisper")
        print("Install with: python -m pip install -r requirements-whisper-benchmark.txt")
        raise SystemExit(1)

    print(f"Loading Whisper model: {model_name}")
    model = whisper.load_model(model_name)
    kwargs = {
        "fp16": False,
        "temperature": 0,
        "condition_on_previous_text": False,
        "initial_prompt": initial_prompt or None,
    }
    if language != "auto":
        kwargs["language"] = language
    result = model.transcribe(str(audio_path), **kwargs)
    return result.get("text", "").strip()


def main():
    configure_console()

    parser = argparse.ArgumentParser(description="Live microphone demo for ViSE-CS ASR.")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--model", default="small")
    parser.add_argument(
        "--language",
        default="auto",
        choices=["auto", "vi", "en"],
        help="Use auto for code-switching; vi may over-Vietnamize English terms.",
    )
    parser.add_argument(
        "--initial-prompt",
        default=DEFAULT_PROMPT,
        help="Whisper prompt/glossary hint. Use an empty string to disable.",
    )
    parser.add_argument("--sample-rate", type=int, default=16000)
    parser.add_argument("--channels", type=int, default=1)
    parser.add_argument("--device", default=None, help="Input device index or name.")
    parser.add_argument("--reference", default=None, help="Optional reference transcript for scoring.")
    parser.add_argument("--list-devices", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    sd = load_sounddevice()
    if args.list_devices:
        print(sd.query_devices())
        return

    demo_dir = root / "demo_recordings"
    audio_path = demo_dir / f"mic_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"

    print()
    print("ViSE-CS Live Microphone Demo")
    print()

    duration = record_audio(audio_path, args.sample_rate, args.channels, args.device)
    print(f"Saved audio: {audio_path}")
    print(f"Duration: {duration:.2f}s")

    raw_prediction = transcribe(audio_path, args.model, root, args.language, args.initial_prompt)
    corrected = correct_prediction(raw_prediction)

    print_block("RAW ASR", raw_prediction)
    print_block("AFTER GLOSSARY CORRECTION", corrected)

    if args.reference:
        terms = load_terms(root / "data" / "lexicon.csv")
        raw_scores = score_one(args.reference, raw_prediction, terms)
        corrected_scores = score_one(args.reference, corrected, terms)
        print_block("REFERENCE", args.reference)
        print_scores("Raw ASR scores", raw_scores)
        print_scores("Corrected scores", corrected_scores)


if __name__ == "__main__":
    main()
