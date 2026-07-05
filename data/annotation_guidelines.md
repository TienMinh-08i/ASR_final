# Annotation Guidelines

## Mục tiêu

Gán nhãn token-level cho tiếng nói code-switching Việt-Anh trong lĩnh vực kỹ thuật phần mềm.

## Nhãn

- `VIE`: từ tiếng Việt.
- `ENG`: từ tiếng Anh thông thường hoặc thuật ngữ tiếng Anh.
- `CODE`: tên lệnh, tên hàm, biến, API, framework, file, package.
- `MIXED`: cụm có dạng lai hoặc phát âm Việt hóa nhưng giữ thuật ngữ kỹ thuật.
- `PUNC`: dấu câu nếu có.

## Nguyên tắc transcript

1. Giữ nguyên thuật ngữ tiếng Anh phổ biến: `push`, `branch`, `pull request`, `unit test`.
2. Chuẩn hóa tên công nghệ theo dạng dễ đọc: `react query`, `docker compose`, `postgres`.
3. Với acronym, có thể viết theo cách người nói đọc nếu cần ASR: `e two e test`.
4. Không tự dịch thuật ngữ kỹ thuật sang tiếng Việt nếu người nói dùng tiếng Anh.
5. Không thêm dấu câu nếu audio không có ngắt rõ ràng.

## Ví dụ

Transcript:

```text
em vừa push code lên branch develop rồi tạo pull request
```

Token labels:

```text
em/VIE vừa/VIE push/ENG code/ENG lên/VIE branch/ENG develop/CODE rồi/VIE tạo/VIE pull/ENG request/ENG
```

## Lỗi thường gặp

- Ghi `pul request`, `pool request`, `pull requests` không nhất quán.
- Dịch `branch` thành `nhánh` dù người nói dùng từ `branch`.
- Gộp quá nhiều từ thành một token.
- Bỏ sót thuật ngữ trong cụm như `dependency array`, `unique constraint`.
