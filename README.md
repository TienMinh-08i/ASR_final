# ViSE-CS Mini

**ViSE-CS Mini** là bộ dữ liệu mẫu nhỏ cho đề tài:

> ViSE-CS: A Vietnamese Software Engineering Code-Switching Speech Dataset and Benchmark

Bộ này mô phỏng tiếng nói code-switching Việt-Anh trong lĩnh vực kỹ thuật phần mềm. Mục tiêu là giúp xây dựng demo đề tài, guideline annotation và benchmark ASR ban đầu.

## Cấu trúc

```text
vise-cs-mini/
  README.md
  data/
    utterances.csv
    tokens.csv
    lexicon.csv
    split_train.csv
    split_dev.csv
    split_test.csv
    annotation_guidelines.md
    recording_script.md
  audio/
    README.md
  scripts/
    evaluate_asr.py
```

## Quy mô

- 100 utterances.
- 5 miền kỹ thuật: frontend, backend, database, devops, testing.
- 3 split: train/dev/test = 70/15/15.
- Có transcript chuẩn và nhãn token-level: `VIE`, `ENG`, `CODE`, `MIXED`, `PUNC`.

## Cách dùng

1. Ghi âm từng câu trong `data/recording_script.md`.
2. Lưu file audio vào thư mục `audio/` theo tên trong cột `audio_path`.
3. Chạy mô hình ASR bất kỳ để tạo file dự đoán dạng CSV:

```csv
utt_id,prediction
vise_0001,"em vừa push code lên branch develop rồi tạo pull request"
```

4. Đánh giá bằng script:

```bash
python scripts/evaluate_asr.py data/utterances.csv predictions.csv
```

## Thu âm bằng script

Cài thư viện thu âm:

```bash
python -m pip install sounddevice
```

Xem danh sách microphone:

```bash
python scripts/record_audio.py --list-devices
```

Thu toàn bộ câu còn thiếu:

```bash
python scripts/record_audio.py --speaker-id spk01 --only-missing
```

Chạy lại từ câu 1 và ghi đè các file đã thu:

```bash
python scripts/record_audio.py --speaker-id spk01 --start vise_0001 --overwrite
```

Script mặc định hiển thị câu **không dấu** để tránh lỗi font/codepage trên Windows terminal. Nếu muốn hiện thêm câu gốc có dấu:

```bash
python scripts/record_audio.py --speaker-id spk01 --show-accents
```

Thu riêng tập test:

```bash
python scripts/record_audio.py --speaker-id spk01 --split test --only-missing
```

Thu lại từ một câu cụ thể:

```bash
python scripts/record_audio.py --speaker-id spk01 --start vise_0010
```

Nếu muốn chọn microphone cụ thể, truyền index hoặc tên device:

```bash
python scripts/record_audio.py --speaker-id spk01 --device 1
```

Kiểm tra file audio đã thu:

```bash
python scripts/check_recordings.py
```

## Chạy benchmark sau khi thu

Cách 1: nếu bạn đã có file dự đoán ASR dạng CSV:

```csv
utt_id,prediction
vise_0086,"ssl certificate hết hạn làm client không gọi được api"
```

Chạy benchmark trên tập test:

```bash
python scripts/run_benchmark.py --split test --predictions predictions.csv --allow-missing-audio
```

Demo nhanh bằng file mẫu có sẵn:

```bash
python scripts/run_benchmark.py --split test --predictions data/sample_predictions_test.csv --allow-missing-audio
```

Cách 2: tự transcribe bằng local Whisper rồi đánh giá luôn:

```bash
python -m pip install -r requirements-whisper-benchmark.txt
python scripts/run_benchmark.py --split test --whisper-model tiny
```

Script sẽ tự dùng `imageio-ffmpeg` nếu máy chưa có `ffmpeg` trong PATH.

Chạy baseline PhoWhisper/Hugging Face:

```bash
python -m pip install -r requirements-hf-asr.txt
python scripts/transcribe_hf_asr.py --model phowhisper-small --split test
python scripts/evaluate_asr.py data/utterances.csv reports/phowhisper-small_test/predictions_phowhisper-small_test.csv --lexicon data/lexicon.csv --split test --output-dir reports/phowhisper-small_test
```

Kết quả sẽ được lưu vào:

```text
reports/tiny_test/benchmark_summary.json
reports/tiny_test/benchmark_details.csv
reports/tiny_test/predictions_whisper_tiny_test.csv
```

Metric hiện có:

- `WER`: Word Error Rate toàn tập.
- WER theo `split`.
- WER theo `domain`.
- Term precision, recall, F1 theo lexicon thuật ngữ.
- `Term Miss Rate`: tỷ lệ thuật ngữ kỹ thuật trong reference bị thiếu ở prediction.

## Demo hệ thống

Demo nhanh bằng prediction đã chạy sẵn:

```bash
python scripts/demo_system.py --utt-id vise_0097
```

Xem danh sách các câu test có thể demo:

```bash
python scripts/demo_system.py --list-test
```

Chạy demo live bằng Whisper, tức là transcribe lại audio rồi mới sửa bằng glossary:

```bash
python scripts/demo_system.py --utt-id vise_0097 --live --model small
```

Demo live bằng microphone:

```bash
python scripts/demo_microphone.py --model small
```

Nếu realtime nhận sai cả tiếng Việt lẫn tiếng Anh, thử chọn đúng microphone và để language auto:

```bash
python scripts/demo_microphone.py --list-devices
python scripts/demo_microphone.py --model small --language auto --device 17
```

Trên một số máy, headset/microphone khác nhau cho chất lượng rất khác. Nếu máy đủ khỏe, `medium` thường nghe tốt hơn:

```bash
python scripts/demo_microphone.py --model medium --language auto --device 17
```

Nếu muốn chấm điểm ngay trong demo microphone, truyền reference:

```bash
python scripts/demo_microphone.py --model small --language auto --reference "graphql resolver can batch request de tranh n plus one query"
```

Xem danh sách microphone:

```bash
python scripts/demo_microphone.py --list-devices
```

Ví dụ nên dùng khi thuyết trình:

- `vise_0097`: minh họa `graphql resolver` và `n plus one query`.
- `vise_0100`: minh họa `dockerfile` và `multi stage build`.
- `vise_0087`: minh họa `feature flag`.

## Gợi ý mở rộng

- Tăng lên 300-1000 utterances.
- Thu âm từ nhiều người nói, vùng miền khác nhau.
- Thêm tiếng ồn văn phòng, họp online, bàn phím.
- Bổ sung metric thuật ngữ đầy đủ hơn như term precision, recall, F1 và richer term alignment.
