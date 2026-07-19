# Claude Log Collector

Công cụ nhỏ, chạy để xuất lịch sử chat **Claude Code** của **đúng dự án đang mở** vào **1 file `.txt` cố định** trong thư mục [claude-log-collector](claude-log-collector), đã **che (redact) API key/secret**. Khi chạy lại hoặc đồng đội chạy lại trên cùng dự án, script sẽ **gộp thêm session mới** vào file hiện có, **không ghi đè**, **không tạo file mới**, và **không lặp lại session đã có**.

## Yêu cầu
- Đã cài **Node.js >= 18** (kiểm tra: `node --version`). Không cần cài thêm gói nào.
- Đã từng dùng **Claude Code** trên máy (log nằm ở `~/.claude/projects`).

## Cách dùng

Mở terminal **tại thư mục gốc dự án** rồi chạy:

```bash
node claude-log-collector/collect-claude-log.mjs
```

Kết quả: file `claude-ai-log.txt` được tạo/ghi nối trong thư mục [claude-log-collector](claude-log-collector).

### Tuỳ chọn
```bash
# Chỉ định dự án khác (nếu không chạy từ trong thư mục dự án):
node claude-log-collector/collect-claude-log.mjs --project "D:\đường-dẫn\dự-án"

# Đổi tên/đường dẫn file kết quả (nếu cần):
node claude-log-collector/collect-claude-log.mjs --out my-log.txt
```

## Nó làm gì
1. **Tự tìm** nơi Claude lưu log: `$CLAUDE_CONFIG_DIR/projects` nếu có, ngược lại `~/.claude/projects`.
2. **Khớp đúng dự án** theo trường `cwd` bên trong file log (không dựa vào tên thư mục đã mã hóa — vốn khác nhau giữa các máy).
3. **Gộp** mọi session của dự án thành 1 file, theo thứ tự thời gian, có mốc thời gian và đánh dấu công cụ đã dùng (`[dùng công cụ: ...]`).
4. **Che key**:
   - Đọc các file `.env` / `backend/.env` / `frontend/.env*` trong dự án và che chính xác các giá trị secret.
   - Che theo mẫu key phổ biến: Google `AIza…`, Gemini `AQ.…`, Anthropic `sk-ant-…`, OpenAI `sk-…`, GitHub `ghp_…`, AWS `AKIA…`, JWT, Slack token, và các gán `api_key=…`, `authorization: …`, `bearer …`.
   - Phần input/output của công cụ (nơi key hay xuất hiện) **không** được đưa vào log — chỉ giữ nội dung hội thoại.
   - Cuối cùng **tự kiểm tra lại**: nếu còn sót giá trị secret của `.env`, thoát với mã lỗi.

## Lưu ý bảo mật
- File `.txt` sinh ra chứa **nội dung chat** — hãy giữ **riêng tư**, gửi qua kênh riêng, **không commit** lên repo chung. (Repo này đã `.gitignore` sẵn `claude-ai-log-*.txt`.)
- Redaction là lớp bảo vệ tự động, không thay thế việc **rà lại bằng mắt** trước khi gửi.
- Công cụ **chỉ đọc** log, không sửa/xóa gì trong `~/.claude`.
