import argparse
import csv
import re
import unicodedata
from pathlib import Path


def remove_accents(text):
    text = text.replace("đ", "d").replace("Đ", "D")
    normalized = unicodedata.normalize("NFD", text)
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def normalize_text(text):
    text = remove_accents(text.lower())
    text = re.sub(r"[^a-z0-9\s-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


RULES = [
    (r"\blayout (sep|set|ship|shift)\b", "layout shift"),
    (r"\bfeature (flux|flak|flack|flex)\b", "feature flag"),
    (r"\binum status\b", "enum status"),
    (r"\bplay drive chess\b", "playwright trace"),
    (r"\bplay drive trace\b", "playwright trace"),
    (r"\bartifact bill\b", "artifact build"),
    (r"\bversion (thac|tag|tac)\b", "version tag"),
    (r"\b(gich|git) commit\b", "git commit"),
    (r"\botcobac direct\b", "oauth callback redirect"),
    (r"\botcobac\b", "oauth callback"),
    (r"\bstatic\b", "staging"),
    (r"\btim nhan id\b", "tenant id"),
    (r"\bchac dinh\b", "sharding"),
    (r"\bworker cast\b", "worker cache"),
    (r"\bservice worker cast\b", "service worker cache"),
    (r"\bcrap pl resolver\b", "graphql resolver"),
    (r"\bgraph ql resolver\b", "graphql resolver"),
    (r"\bbus request\b", "batch request"),
    (r"\bn plus 1 qe\b", "n plus one query"),
    (r"\bn plus one qe\b", "n plus one query"),
    (r"\bchu nick indic\b", "unique index"),
    (r"\bunique indic\b", "unique index"),
    (r"\bnon duoc\b", "null duoc"),
    (r"\brequestiontest\b", "regression test"),
    (r"\brequestion test\b", "regression test"),
    (r"\bdockerfine\b", "dockerfile"),
    (r"\bdocker file\b", "dockerfile"),
    (r"\bmantis txtview\b", "multi stage build"),
    (r"\bmulti state build\b", "multi stage build"),
]


def correct_prediction(text):
    corrected = normalize_text(text)
    for pattern, replacement in RULES:
        corrected = re.sub(pattern, replacement, corrected)
    corrected = re.sub(r"\s+", " ", corrected).strip()
    return corrected


def main():
    parser = argparse.ArgumentParser(description="Apply glossary-oriented ASR post-processing.")
    parser.add_argument("input_csv")
    parser.add_argument("output_csv")
    args = parser.parse_args()

    input_path = Path(args.input_csv)
    output_path = Path(args.output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(input_path, newline="", encoding="utf-8") as f_in, open(
        output_path, "w", newline="", encoding="utf-8"
    ) as f_out:
        reader = csv.DictReader(f_in)
        writer = csv.DictWriter(f_out, fieldnames=["utt_id", "prediction"])
        writer.writeheader()
        for row in reader:
            writer.writerow(
                {
                    "utt_id": row["utt_id"],
                    "prediction": correct_prediction(row["prediction"]),
                }
            )

    print(f"Wrote: {output_path}")


if __name__ == "__main__":
    main()
