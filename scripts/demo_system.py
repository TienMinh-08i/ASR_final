import argparse
import ctypes
import csv
import os
import shutil
import sys
from pathlib import Path

from evaluate_asr import load_terms, normalize, term_stats, word_error_rate
from postprocess_predictions import correct_prediction


DEFAULT_PROMPT = (
    "Vietnamese and English software engineering speech. "
    "Important terms: graphql resolver, batch request, n plus one query, "
    "dockerfile, multi stage build, feature flag, oauth callback, playwright trace, "
    "service worker cache, unique index, regression test, keyboard navigation."
)


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


def read_csv_by_id(path, key="utt_id"):
    with open(path, newline="", encoding="utf-8") as f:
        return {row[key]: row for row in csv.DictReader(f)}


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


def transcribe_live(root, audio_path, model_name, language, initial_prompt):
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


def score_one(reference, prediction, terms):
    errors, words = word_error_rate(reference, prediction)
    wer = errors / words if words else 0
    ref_terms, hyp_terms, matched, missed, inserted = term_stats(reference, prediction, terms)
    precision = len(matched) / len(hyp_terms) if hyp_terms else 0
    recall = len(matched) / len(ref_terms) if ref_terms else 0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
    return {
        "wer": wer,
        "errors": errors,
        "words": words,
        "ref_terms": ref_terms,
        "hyp_terms": hyp_terms,
        "matched": matched,
        "missed": missed,
        "inserted": inserted,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def print_block(title, text):
    print()
    print("=" * 78)
    print(title)
    print("-" * 78)
    print(text if text else "(empty)")


def print_scores(label, scores):
    print()
    print(f"{label}:")
    print(f"  WER: {scores['wer'] * 100:.2f}% ({scores['errors']}/{scores['words']})")
    print(f"  Term precision: {scores['precision'] * 100:.2f}%")
    print(f"  Term recall: {scores['recall'] * 100:.2f}%")
    print(f"  Term F1: {scores['f1'] * 100:.2f}%")
    print(f"  Matched terms: {', '.join(scores['matched']) if scores['matched'] else '(none)'}")
    print(f"  Missed terms: {', '.join(scores['missed']) if scores['missed'] else '(none)'}")
    print(f"  Inserted terms: {', '.join(scores['inserted']) if scores['inserted'] else '(none)'}")


def choose_default_utt(rows):
    for candidate in ["vise_0097", "vise_0100", "vise_0087", "vise_0089"]:
        if candidate in rows:
            return candidate
    return next(iter(rows))


def main():
    configure_console()

    parser = argparse.ArgumentParser(description="Demo ViSE-CS ASR + glossary correction.")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--utt-id", default=None, help="Utterance id to demo, e.g. vise_0097.")
    parser.add_argument("--predictions", default=None, help="Prediction CSV. Default: Whisper small test predictions.")
    parser.add_argument("--live", action="store_true", help="Run live Whisper transcription instead of using saved predictions.")
    parser.add_argument("--model", default="small", help="Whisper model for --live mode.")
    parser.add_argument("--language", default="auto", choices=["auto", "vi", "en"])
    parser.add_argument("--initial-prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--list-test", action="store_true", help="List available test utterances.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    utterances = read_csv_by_id(root / "data" / "utterances.csv")
    terms = load_terms(root / "data" / "lexicon.csv")

    test_ids = [utt_id for utt_id, row in utterances.items() if row["split"] == "test"]
    if args.list_test:
        for utt_id in test_ids:
            print(f"{utt_id}: {utterances[utt_id]['transcript']}")
        return

    utt_id = args.utt_id or choose_default_utt({key: utterances[key] for key in test_ids})
    if utt_id not in utterances:
        print(f"Unknown utt_id: {utt_id}")
        raise SystemExit(2)

    row = utterances[utt_id]
    audio_path = root / row["audio_path"]
    reference = row["transcript"]

    if args.live:
        raw_prediction = transcribe_live(root, audio_path, args.model, args.language, args.initial_prompt)
        source = f"live Whisper {args.model}"
    else:
        pred_path = Path(args.predictions) if args.predictions else root / "reports" / "small_test" / "predictions_whisper_small_test.csv"
        predictions = read_csv_by_id(pred_path)
        if utt_id not in predictions:
            print(f"{utt_id} not found in predictions: {pred_path}")
            raise SystemExit(3)
        raw_prediction = predictions[utt_id]["prediction"]
        source = str(pred_path)

    corrected = correct_prediction(raw_prediction)
    raw_scores = score_one(reference, raw_prediction, terms)
    corrected_scores = score_one(reference, corrected, terms)

    print()
    print("ViSE-CS Mini Demo")
    print(f"Utterance: {utt_id}")
    print(f"Domain: {row['domain']} | Scenario: {row['scenario']}")
    print(f"Audio: {audio_path}")
    print(f"Prediction source: {source}")

    print_block("REFERENCE", reference)
    print_block("RAW ASR", raw_prediction)
    print_block("AFTER GLOSSARY CORRECTION", corrected)

    print_scores("Raw ASR scores", raw_scores)
    print_scores("Corrected scores", corrected_scores)

    print()
    print("Demo takeaway:")
    if corrected_scores["f1"] > raw_scores["f1"]:
        print("  Glossary correction improves technical-term recovery for this example.")
    else:
        print("  Glossary correction does not improve this example; inspect the error manually.")


if __name__ == "__main__":
    main()
