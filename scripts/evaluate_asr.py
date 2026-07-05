import argparse
import csv
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path


def remove_accents(text):
    text = text.replace("đ", "d").replace("Đ", "D")
    normalized = unicodedata.normalize("NFD", text)
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def normalize(text):
    text = remove_accents(text.lower().strip())
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text)
    return text


def edit_distance(ref, hyp):
    rows = len(ref) + 1
    cols = len(hyp) + 1
    dp = [[0] * cols for _ in range(rows)]
    for i in range(rows):
        dp[i][0] = i
    for j in range(cols):
        dp[0][j] = j
    for i in range(1, rows):
        for j in range(1, cols):
            cost = 0 if ref[i - 1] == hyp[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,
                dp[i][j - 1] + 1,
                dp[i - 1][j - 1] + cost,
            )
    return dp[-1][-1]


def load_refs(path):
    refs = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            refs[row["utt_id"]] = row
    return refs


def load_predictions(path):
    preds = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            preds[row["utt_id"]] = row["prediction"]
    return preds


def load_terms(path):
    if not path or not path.exists():
        return []
    terms = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            term = normalize(row["term"])
            if term:
                terms.append(term)
    return sorted(set(terms), key=lambda value: (-len(value.split()), value))


def word_error_rate(ref_text, hyp_text):
    ref_words = normalize(ref_text).split()
    hyp_words = normalize(hyp_text).split()
    errors = edit_distance(ref_words, hyp_words)
    return errors, len(ref_words)


def term_stats(ref_text, hyp_text, terms):
    ref_norm = f" {normalize(ref_text)} "
    hyp_norm = f" {normalize(hyp_text)} "
    ref_terms = [term for term in terms if f" {term} " in ref_norm]
    hyp_terms = [term for term in terms if f" {term} " in hyp_norm]
    matched = [term for term in ref_terms if term in hyp_terms]
    missed = [term for term in ref_terms if term not in hyp_terms]
    inserted = [term for term in hyp_terms if term not in ref_terms]
    return ref_terms, hyp_terms, matched, missed, inserted


def main():
    parser = argparse.ArgumentParser(description="Evaluate ASR predictions for ViSE-CS Mini.")
    parser.add_argument("utterances")
    parser.add_argument("predictions")
    parser.add_argument("--lexicon", default=None)
    parser.add_argument("--split", choices=["train", "dev", "test"], default=None)
    parser.add_argument("--domain", default=None)
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()

    refs = load_refs(Path(args.utterances))
    preds = load_predictions(Path(args.predictions))
    terms = load_terms(Path(args.lexicon)) if args.lexicon else []

    total_words = 0
    total_errors = 0
    missing = []
    scored_rows = []
    group_stats = defaultdict(lambda: {"errors": 0, "words": 0, "utterances": 0})
    total_ref_terms = 0
    total_hyp_terms = 0
    matched_terms = 0
    missed_terms = 0

    for utt_id, row in refs.items():
        if args.split and row["split"] != args.split:
            continue
        if args.domain and row["domain"] != args.domain:
            continue
        if utt_id not in preds:
            missing.append(utt_id)
            continue

        ref_text = row["transcript"]
        hyp_text = preds[utt_id]
        errors, words = word_error_rate(ref_text, hyp_text)
        wer = errors / words if words else 0
        ref_terms, hyp_terms, matched, missed, inserted = term_stats(ref_text, hyp_text, terms)

        total_words += words
        total_errors += errors
        total_ref_terms += len(ref_terms)
        total_hyp_terms += len(hyp_terms)
        matched_terms += len(matched)
        missed_terms += len(missed)

        for key in [f"split:{row['split']}", f"domain:{row['domain']}"]:
            group_stats[key]["errors"] += errors
            group_stats[key]["words"] += words
            group_stats[key]["utterances"] += 1

        scored_rows.append(
            {
                "utt_id": utt_id,
                "split": row["split"],
                "domain": row["domain"],
                "wer": f"{wer:.4f}",
                "errors": errors,
                "words": words,
                "ref_term_count": len(ref_terms),
                "hyp_term_count": len(hyp_terms),
                "matched_term_count": len(matched),
                "missed_term_count": len(missed),
                "inserted_term_count": len(inserted),
                "missed_terms": "; ".join(missed),
                "inserted_terms": "; ".join(inserted),
                "reference": ref_text,
                "prediction": hyp_text,
            }
        )

    wer = total_errors / total_words if total_words else 0
    term_recall = matched_terms / total_ref_terms if total_ref_terms else 0
    term_precision = matched_terms / total_hyp_terms if total_hyp_terms else 0
    term_f1 = (
        2 * term_precision * term_recall / (term_precision + term_recall)
        if term_precision + term_recall
        else 0
    )
    term_miss_rate = 1 - term_recall if total_ref_terms else 0

    print(f"Utterances: {len(refs)}")
    print(f"Scored: {len(scored_rows)}")
    print(f"Missing predictions: {len(missing)}")
    print(f"WER: {wer:.4f}")
    if terms:
        print(f"Term Precision: {term_precision:.4f}")
        print(f"Term Recall: {term_recall:.4f}")
        print(f"Term F1: {term_f1:.4f}")
        print(f"Term Miss Rate: {term_miss_rate:.4f}")

    if group_stats:
        print("\nBreakdown:")
        for key, stats in sorted(group_stats.items()):
            group_wer = stats["errors"] / stats["words"] if stats["words"] else 0
            print(f"- {key}: WER={group_wer:.4f}, utterances={stats['utterances']}")

    if missing:
        print()
        print("Missing utt_id:")
        for utt_id in missing:
            print(f"- {utt_id}")

    if args.output_dir:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        report_csv = output_dir / "benchmark_details.csv"
        summary_json = output_dir / "benchmark_summary.json"

        with open(report_csv, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "utt_id",
                "split",
                "domain",
                "wer",
                "errors",
                "words",
                "ref_term_count",
                "hyp_term_count",
                "matched_term_count",
                "missed_term_count",
                "inserted_term_count",
                "missed_terms",
                "inserted_terms",
                "reference",
                "prediction",
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(scored_rows)

        summary = {
            "utterances": len(refs),
            "scored": len(scored_rows),
            "missing_predictions": len(missing),
            "wer": wer,
            "term_precision": term_precision if terms else None,
            "term_recall": term_recall if terms else None,
            "term_f1": term_f1 if terms else None,
            "term_miss_rate": term_miss_rate if terms else None,
            "term_error_rate": term_miss_rate if terms else None,
            "matched_terms": matched_terms,
            "reference_terms": total_ref_terms,
            "hypothesis_terms": total_hyp_terms,
            "groups": {
                key: {
                    "wer": stats["errors"] / stats["words"] if stats["words"] else 0,
                    "utterances": stats["utterances"],
                    "errors": stats["errors"],
                    "words": stats["words"],
                }
                for key, stats in sorted(group_stats.items())
            },
            "missing_utt_id": missing,
        }
        summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print()
        print(f"Wrote: {report_csv}")
        print(f"Wrote: {summary_json}")


if __name__ == "__main__":
    main()
