# Đề Tài Mẫu: ViSE-CS Mini

## 1. Tên đề tài

**ViSE-CS: A Vietnamese Software Engineering Code-Switching Speech Dataset and Benchmark**

## 2. Mục tiêu

Đề tài xây dựng một bộ dữ liệu tiếng nói nhỏ cho hiện tượng code-switching Việt-Anh trong lĩnh vực kỹ thuật phần mềm, đồng thời đề xuất một benchmark cơ bản để đánh giá mô hình nhận dạng tiếng nói tự động.

## 3. Lý do chọn đề tài

Trong môi trường lập trình tại Việt Nam, lập trình viên thường giao tiếp bằng tiếng Việt nhưng giữ nguyên nhiều thuật ngữ tiếng Anh như `pull request`, `unit test`, `deploy`, `database`, `middleware`, `cache`, `docker compose`. Các mô hình ASR tổng quát có thể nhận tốt câu tiếng Việt thông thường nhưng dễ sai ở thuật ngữ kỹ thuật, tên công nghệ, tên lệnh hoặc cụm tiếng Anh được phát âm theo kiểu Việt hóa.

Vì vậy, cần một bộ dữ liệu chuyên biệt để đánh giá và cải thiện ASR cho miền software engineering.

## 4. Phạm vi dữ liệu

Bộ dữ liệu mẫu gồm 100 câu trong 5 miền:

- Frontend
- Backend
- Database
- DevOps
- Testing

Mỗi câu có:

- `utt_id`: mã câu.
- `audio_path`: đường dẫn file audio dự kiến.
- `split`: train/dev/test.
- `domain`: miền kỹ thuật.
- `scenario`: ngữ cảnh như daily standup, debugging, code review.
- `speaker_id`: mã người nói.
- `transcript`: câu chuẩn.

## 5. Phương pháp xây dựng

Quy trình xây dựng dataset gồm 4 bước:

1. Thu thập/thiết kế câu nói tự nhiên trong môi trường kỹ thuật phần mềm.
2. Ghi âm từng câu theo định dạng WAV.
3. Gán transcript chuẩn và nhãn token-level cho hiện tượng code-switching.
4. Chia dữ liệu thành train/dev/test để benchmark.

## 6. Annotation

Các nhãn token-level:

- `VIE`: từ tiếng Việt.
- `ENG`: thuật ngữ hoặc từ tiếng Anh.
- `CODE`: tên công nghệ, biến, hàm, API, framework, command.
- `MIXED`: dạng lai hoặc phát âm Việt hóa.
- `PUNC`: dấu câu.

Ví dụ:

```text
em vừa push code lên branch develop rồi tạo pull request
```

```text
VIE VIE ENG ENG VIE ENG CODE VIE VIE ENG ENG
```

## 7. Benchmark

Baseline đơn giản sử dụng chỉ số Word Error Rate:

```text
WER = (Substitutions + Insertions + Deletions) / Number of Reference Words
```

Ngoài WER, bộ script hiện hỗ trợ:

- Term Error Rate: tính lỗi riêng trên thuật ngữ kỹ thuật.
- WER theo split và theo domain.

Các metric có thể mở rộng thêm:

- Code-switching WER: tính lỗi riêng trên token tiếng Anh.
- Language Identification Accuracy: đo khả năng nhận diện ngôn ngữ ở token-level nếu có prediction nhãn ngôn ngữ.

Sau khi ghi âm và có file dự đoán ASR, có thể chạy:

```bash
python scripts/run_benchmark.py --split test --predictions predictions.csv --allow-missing-audio
```

Hoặc tự transcribe bằng Whisper local:

```bash
python -m pip install -U openai-whisper
python scripts/run_benchmark.py --split test --whisper-model tiny
```

## 8. Kỳ vọng kết quả

Dataset mini này chưa nhằm đạt quy mô công bố chính thức, nhưng đủ để:

- Minh họa hiện tượng code-switching trong software engineering.
- Chạy thử ASR baseline.
- Phân tích lỗi trên thuật ngữ kỹ thuật.
- Làm nền tảng mở rộng lên dataset lớn hơn.

## 9. Hạn chế

- Số lượng câu còn nhỏ.
- Chưa có audio thật nếu chưa tiến hành ghi âm.
- Câu nói được thiết kế thủ công, chưa hoàn toàn phản ánh hội thoại tự nhiên.
- Chưa có nhiều vùng miền, giới tính và điều kiện tiếng ồn.

## 10. Hướng phát triển

- Mở rộng lên 300-1000 câu.
- Thu âm từ nhiều lập trình viên thật.
- Thêm dữ liệu hội thoại họp kỹ thuật.
- Benchmark nhiều mô hình ASR như Whisper, wav2vec2, XLS-R hoặc PhoWhisper.
- Thêm hậu xử lý bằng LLM để sửa thuật ngữ kỹ thuật.
