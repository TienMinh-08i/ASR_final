# Phản hồi các nhận xét về báo cáo ViSE-CS

## Đã chỉnh trong báo cáo

1. **Rò rỉ dữ liệu ở glossary correction**
   - Đã đổi cách trình bày: kết quả `Whisper small + glossary correction` không còn được xem là benchmark blind chính thức.
   - Báo cáo hiện gọi đây là **post-hoc glossary correction analysis**.
   - Đã nêu rõ quy tắc được viết sau khi xem lỗi test, nên kết quả có nguy cơ overfit và chỉ nên xem là diagnostic upper bound.

2. **Cỡ mẫu nhỏ**
   - Đã mở rộng phần Limitations.
   - Nêu rõ dataset chỉ có 100 câu, test set 15 câu, nên WER có phương sai lớn và chưa ổn định về thống kê.

3. **Thiếu PhoWhisper**
   - Đã bổ sung PhoWhisper vào Related Work.
   - Đã chạy thêm baseline `PhoWhisper small`.
   - Kết quả mới sau khi chuẩn hóa `đ -> d`: WER 66.67%, term recall 10.71%, F1 19.35%.
   - Nhận xét: PhoWhisper small tốt cho tiếng Việt nhưng chưa tốt với code-switching kỹ thuật dày đặc thuật ngữ tiếng Anh; future work nên thử thêm checkpoint lớn hơn như PhoWhisper medium/large nếu tài nguyên cho phép.

4. **Transcript ASCII**
   - Đã nêu rõ việc bỏ dấu làm benchmark dễ hơn full Vietnamese ASR.
   - Đề xuất future work báo cáo cả diacritic-sensitive WER và accent-normalized WER.

5. **TER đơn giản**
   - Đã đổi thuật ngữ từ `Term Error Rate` sang `Term Miss Rate`.
   - Đã bổ sung thêm term precision, recall và F1 vào evaluator và bảng kết quả.
   - Đã nêu rõ các metric này vẫn dựa trên exact lexicon matching nên còn hạn chế.

6. **Thiếu reproducibility**
   - Đã bổ sung môi trường: Windows, Python 3.11.6, PyTorch 2.7.0 CPU.
   - Đã nêu dùng default decoding của OpenAI Whisper và ép language option là Vietnamese.

7. **Thông tin tác giả**
   - Vẫn để placeholder vì chưa có tên/trường/email thật.
   - Cần thay `Student Name`, `University / Institution Name`, `student.email@example.com` trước khi nộp.

## Cách diễn giải kết quả hiện tại

Kết quả benchmark blind nên lấy:

| System | WER | TMR |
|---|---:|---:|
| Whisper tiny | 108.33% | 96.43% |
| Whisper base | 68.75% | 82.14% |
| Whisper small | 32.64% | 67.86% |
| PhoWhisper small | 66.67% | 89.29% |

Trong bài hiện có thêm precision/recall/F1 cho thuật ngữ. Điểm đáng chú ý là term precision đều cao vì hệ thống hầu như không chèn nhầm thuật ngữ có trong lexicon; lỗi chính là recall thấp, tức là không nhận ra được thuật ngữ kỹ thuật trong reference.

Domain-level WER hiện dùng `Whisper small` vì đây là model có kết quả blind raw-ASR tốt nhất. Báo cáo đã nói rõ không dùng bản glossary-corrected cho bảng domain để tránh trình bày kết quả post-hoc như benchmark blind.

## Cập nhật theo review lần 3

1. **Precision = 100%**
   - Đã giải thích rõ hơn trong Results: precision 100% không có nghĩa transcript không có lỗi kỹ thuật, mà do exact-match lexicon metric hầu như không ghi nhận false-positive lexicon terms.
   - Lỗi chính là recall thấp: model bóp méo thuật ngữ thành chuỗi không nằm trong lexicon.

2. **Công bố mẫu số term-level**
   - Đã thêm `T = 28` reference term occurrences trong test split.

3. **TMR và Recall trùng thông tin**
   - Đã bỏ cột TMR khỏi bảng chính và bảng post-hoc.
   - Bảng giờ giữ `WER`, `Precision`, `Recall`, `F1`.
   - TMR vẫn được định nghĩa trong text vì nó là cách diễn giải trực quan của `1 - Recall`.

4. **Thiếu khoảng tin cậy**
   - Đã thêm bảng bootstrap 95% CI cho WER, dùng utterance-level resampling với 10,000 samples.
   - CI khá rộng, củng cố thông điệp rằng đây là pilot study chứ chưa phải benchmark ổn định.

Kết quả glossary correction nên gọi là phân tích hậu nghiệm:

| System | WER | TMR |
|---|---:|---:|
| Whisper small + post-hoc glossary | 9.72% | 0.00% |

Không nên trình bày dòng này như kết quả test chính thức nếu chưa xây rules từ dev set.
