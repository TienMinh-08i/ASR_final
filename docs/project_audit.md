# ViSE-CS Mini Project Audit

Audit date: 2026-07-05

## Data

- Utterances: 100
- Audio files recorded: 100/100
- Missing audio: 0
- Total duration: 10.30 minutes
- Average duration: 6.18 seconds
- Split: train 70, dev 15, test 15
- Domains: DevOps 21, Frontend 20, Backend 20, Database 20, Testing 19
- Token/tag alignment: passed, 100 rows, 0 mismatches

## Current Blind Benchmark

| Model | WER | Term Precision | Term Recall | Term F1 |
|---|---:|---:|---:|---:|
| Whisper tiny | 108.33% | 100.00% | 3.57% | 6.90% |
| Whisper base | 68.75% | 100.00% | 17.86% | 30.30% |
| Whisper small | 32.64% | 100.00% | 32.14% | 48.65% |
| PhoWhisper small | 66.67% | 100.00% | 10.71% | 19.35% |

Reference term occurrences in test set: 28.

## Post-Hoc Analysis

| System | WER | Term Precision | Term Recall | Term F1 |
|---|---:|---:|---:|---:|
| Whisper small + post-hoc glossary | 9.72% | 100.00% | 100.00% | 100.00% |

This is not a blind benchmark result because correction rules were created after inspecting test-set errors.

## Scripts

- `record_audio.py`: record utterance-level dataset audio.
- `check_recordings.py`: verify audio coverage and duration.
- `run_benchmark.py`: run Whisper transcription and evaluation.
- `transcribe_hf_asr.py`: run Hugging Face ASR/PhoWhisper transcription.
- `evaluate_asr.py`: compute WER and term metrics.
- `postprocess_predictions.py`: glossary-oriented correction.
- `demo_system.py`: demo using saved predictions or live Whisper on existing audio.
- `demo_microphone.py`: live microphone demo.

All Python scripts compile successfully.

## Demo Status

- `demo_system.py --utt-id vise_0097`: passed.
- `demo_microphone.py --list-devices`: passed, microphone devices detected.

## Report Status

- IEEE LaTeX report: `outputs/vise_cs_ieee_report.tex`
- Reviewer response notes: `outputs/review_response_vi.md`
- Main dataset zip: `outputs/vise-cs-mini.zip`

Known limitation: PDF was not compiled locally because `pdflatex` is not installed in PATH.
