# Installation and Run Guide

Hướng dẫn này dùng cho repo `lab17-multi-memory-agent` trong thư mục `track3-lab2`.

## 1. Yêu cầu

- Windows PowerShell
- Python 3.11+ hoặc `py` launcher
- `uv`
- Tùy chọn:
  - Redis nếu muốn dùng preference memory backend thật
  - OpenAI API key nếu muốn dùng model thật
  - Chroma nếu muốn bật semantic backend persistent theo cấu hình

## 2. Tạo môi trường và cài dependency

Từ thư mục repo:

```powershell
uv venv
.venv\Scripts\Activate.ps1
uv pip install -r requirements.txt
```

Nếu máy chưa có `uv`, cài trước rồi chạy lại các lệnh trên.

## 3. Tạo file cấu hình môi trường

```powershell
Copy-Item .env.example .env
```

Các biến quan trọng trong `.env`:

```env
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
REDIS_URL=redis://localhost:6379/0
USE_REDIS=false
USE_CHROMA=false
MEMORY_DIR=memory
REPORTS_DIR=reports
DEFAULT_MAX_CONTEXT_TOKENS=1400
```

Gợi ý:

- Nếu chỉ muốn demo nhanh, giữ `USE_REDIS=false` và `USE_CHROMA=false`.
- Nếu có Redis thật, đổi `USE_REDIS=true`.
- Nếu có API key OpenAI, điền `OPENAI_API_KEY` để agent tạo câu trả lời bằng model thật thay vì fallback nội bộ.

## 4. Chạy demo bằng CLI

### 4.1. Gửi một query đơn lẻ

```powershell
py -m src.main --user-id user_001 --session-id session_1 --query "Tôi thích Python, không thích Java."
```

Session mới:

```powershell
py -m src.main --user-id user_001 --session-id session_2 --query "Tôi nên học framework backend nào?"
```

### 4.2. Chạy interactive mode

```powershell
py -m src.main --user-id user_001 --session-id session_1
```

Thoát bằng:

```text
exit
```

### 4.3. Chạy baseline agent

```powershell
py -m src.main --user-id user_001 --session-id session_1 --mode baseline --query "Tôi nên học framework backend nào?"
```

## 5. Chạy giao diện Streamlit

```powershell
streamlit run src/demo/app.py
```

UI hỗ trợ:

- nhập `user_id`
- nhập `session_id`
- chọn `memory` hoặc `baseline`
- chat trực tiếp với agent
- xem memory panel gồm:
  - router decision
  - retrieved memories
  - memory writes
  - metrics và token breakdown

## 6. Chạy benchmark

```powershell
py -m src.benchmark.run_benchmark
```

Kết quả được ghi ra:

- [BENCHMARK.md](/D:/AI/26AI/track3-lab2/BENCHMARK.md)
- [reports/benchmark_report.md](/D:/AI/26AI/track3-lab2/reports/benchmark_report.md)
- [reports/results.json](/D:/AI/26AI/track3-lab2/reports/results.json)

## 7. Chạy test

```powershell
py -m pytest
```

Nếu báo lỗi thiếu `pytest`, kiểm tra lại bước cài dependency:

```powershell
uv pip install -r requirements.txt
```

## 8. Luồng demo tối thiểu nên chạy

### Bước 1: lưu preference

```powershell
py -m src.main --user-id user_001 --session-id session_1 --query "Tôi thích Python, không thích Java."
```

### Bước 2: sang session mới và recall preference

```powershell
py -m src.main --user-id user_001 --session-id session_2 --query "Tôi nên học framework backend nào?"
```

Kỳ vọng:

- Agent ưu tiên Python/FastAPI/Django
- Không cần hỏi lại preference

### Bước 3: lưu episodic memory

```powershell
py -m src.main --user-id user_001 --session-id session_3 --query "Tôi bị rối async await, không hiểu await có block chương trình không."
```

### Bước 4: recall episode ở session khác

```powershell
py -m src.main --user-id user_001 --session-id session_4 --query "Lần trước tôi bị rối phần async, giải thích lại giúp tôi."
```

## 9. Thư mục quan trọng

- [src/main.py](/D:/AI/26AI/track3-lab2/src/main.py): CLI entrypoint
- [src/demo/app.py](/D:/AI/26AI/track3-lab2/src/demo/app.py): Streamlit demo
- [src/graph.py](/D:/AI/26AI/track3-lab2/src/graph.py): workflow chính
- [src/memory](/D:/AI/26AI/track3-lab2/src/memory): các backend memory
- [src/benchmark](/D:/AI/26AI/track3-lab2/src/benchmark): benchmark pipeline
- [memory](/D:/AI/26AI/track3-lab2/memory): dữ liệu memory local fallback
- [reports](/D:/AI/26AI/track3-lab2/reports): benchmark outputs

## 10. Ghi chú

- Nếu không bật Redis hoặc Chroma, hệ thống vẫn chạy bằng fallback local.
- Nếu không có `OPENAI_API_KEY`, agent dùng deterministic fallback response để pipeline vẫn hoạt động.
- Repo hiện ưu tiên khả năng demo và benchmark ổn định; nếu muốn production-like hơn thì nên thay rule-based router bằng model-based routing và tokenizer chính xác hơn.
