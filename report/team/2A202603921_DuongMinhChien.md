# Báo cáo cá nhân — DuongMinhChien-2A202603921

## 1. Thông tin thành viên

- Họ tên: Dương Minh Chiến
- MSSV: 2A202603921
- Email: 26ai.chiendm3@vinuni.edu.vn
- GitHub: `duongchien147`

## 2. Phần việc phụ trách

- Thiết kế, cài đặt và kiểm thử tool mới **`top_scorers`** (CP3): bảng xếp hạng vua phá lưới của một giải bóng đá,
  phục vụ hướng Football Research Agent của nhóm.
- Viết unit test và eval case routing cho tool này (CP3, CP4).

## 3. Đóng góp cụ thể

### 3.1. Tool `top_scorers` — [`starter_v0/tools/top_scorers/`](../../starter_v0/tools/top_scorers/)

- **Hai nguồn dữ liệu, có fallback:**
  - Nguồn chính **API-Football** (`/leagues` để lấy league id, danh sách mùa, mùa hiện tại và
    `coverage.top_scorers`; sau đó `/players/topscorers`). Cần `API_FOOTBALL_KEY`.
  - Nguồn dự phòng **SportScore** (`/api/widget/topscorers/`, không cần key). Khi API-Football lỗi
    (thiếu key, 401/403, 429, gói Free không có mùa, 5xx, timeout, JSON hỏng…) tool tự chuyển nguồn và ghi
    lý do vào `attempts` + `provider.fallback_reason`, không giấu lỗi.
- **Không bịa số liệu:** trường provider không có (phạt đền, quốc tịch, tuổi…) trả `null`, không thay bằng 0.
- **Bảo vệ mùa giải:** SportScore không trả metadata mùa, nên yêu cầu mùa cũ **không** bị thay bằng dữ liệu mùa
  hiện tại → trả `data_unavailable`.
- **Không đoán:** giải trùng tên → `ambiguous_competition` kèm danh sách `candidates` để agent hỏi lại user;
  slug SportScore chỉ dùng slug đã kiểm chứng hoặc tên khớp chính xác qua search.
- **An toàn & tiết kiệm quota:** kiểm tra input trước khi gọi HTTP, cache 24h (gói Free 100 request/ngày),
  không retry khi 429, API key không bao giờ xuất hiện trong output.
- Tool luôn trả dict, không raise — đúng yêu cầu C4.

### 3.2. Đăng ký tool

- [`tools/__init__.py`](../../starter_v0/tools/__init__.py): thêm `"top_scorers": top_scorers`.
- [`artifacts/tools.yaml`](../../starter_v0/artifacts/tools.yaml): khai báo tool với mô tả khi nào dùng / không dùng
  (phân biệt với `football_stats` và `lookup`), quy ước args (`season` = năm bắt đầu: 2025/26 → 2025;
  `limit` 1–20; `country` để phân biệt giải trùng tên).
- [`.env.example`](../../starter_v0/.env.example): thêm tên biến `API_FOOTBALL_KEY=` (không có giá trị).

### 3.3. Unit test — [`tests/test_top_scorers.py`](../../starter_v0/tests/test_top_scorers.py)

26 test, chạy offline (mock `requests.get`, không gọi mạng thật), bao gồm:

| Nhóm              | Ví dụ test                                                                                                |
| ----------------- | --------------------------------------------------------------------------------------------------------- |
| Happy path        | API-Football resolve league 39 + season 2025, map đúng thứ hạng/bàn/kiến tạo/phạt đền; `"2025/26"` → 2025 |
| Fallback          | Thiếu key → SportScore; 401/403/429 → SportScore và **không retry**; lỗi `plan` trong body HTTP 200       |
| Season protection | Mùa 2022 không bị thay bằng dữ liệu hiện tại; SportScore không được gọi                                   |
| Cả hai nguồn lỗi  | 500 + timeout → `data_unavailable` có cấu trúc, key không lộ trong output                                 |
| Input xấu         | Giải rỗng/`None`, `limit` 0/21/"ten", `season` 99, `country` 123 → `invalid_input`, 0 request             |
| Khác              | Giải trùng tên → `candidates`; cache tránh gọi lại; JSON hỏng → `invalid_json`                            |

### 3.4. Eval case — [`data/eval_top_scorers.json`](../../starter_v0/data/eval_top_scorers.json)

4 case (3 single-turn, 1 multi-turn): route tới `top_scorers` với `season=2025, limit=10`; câu "Chiếc giày vàng"
không được route sang `lookup`; thiếu tên giải → `clarify`; multi-turn gom giải + `season=2024, limit=5`.
Đặt ở file riêng vì `eval_group.json` của nhóm phải giữ đúng 10 case.

## 4. Bằng chứng

- **Commit chính:** `23e97e0` — _feat(CP3): add top_scorers tool with API-Football primary and SportScore fallback_
  (7 file, +1091 dòng, 0 dòng xoá; đã merge vào `main`).
- **Commit khác:** `794ab19` (tạo báo cáo cá nhân). `428df30` (_Add top scorers research too_) là bản đầu tiên
  của tool, đã bị nhóm revert ở `142d701` vì sửa quá nhiều file dùng chung (gồm `system_prompt.md`).
  Bản `23e97e0` được làm lại từ đầu, chỉ chạm các file của tool.
- **`pytest`:** `tests/test_top_scorers.py` 26 passed; toàn suite **101 passed, 14 skipped, 0 failed**
  (14 skipped là stub có sẵn trong `test_tools_todo.py`); `tests/test_tool_contract.py` xanh sau khi thêm tool.
- **Chạy thật (2026-11-10):**
  - Premier League, mùa hiện tại: API-Football trả _"Free plans do not have access to this season, try from 2022
    to 2024"_ → tool fallback sang SportScore, trả top 5 (Haaland 9 bàn, Isak 7…), `season.verified: false`,
    có attribution.
  - Premier League, `season=2024`: API-Football trả dữ liệu, `verified: true`, không cần fallback.
- **AI/công cụ đã dùng và cách tự kiểm tra kết quả:**
  - Dùng **Claude Code** để đọc codebase, viết code tool, test và tài liệu.
  - Cách kiểm tra:
    1. Gọi thử endpoint thật (API-Football, SportScore) để lấy cấu trúc JSON thật trước khi viết mock,
       thay vì để AI tự đoán schema.
    2. Chạy `pytest` toàn suite và contract test sau mỗi thay đổi.
    3. Chạy tool thật với key Free để xác nhận cả nhánh fallback và nhánh API-Football.
    4. Kiểm tra `git diff --stat` trước khi commit: chỉ có dòng thêm, không đụng file của thành viên khác,
       `.env` không bị stage.
    5. Đọc response gốc khi thấy số liệu bất thường (xem mục 5).

## 5. Tự đánh giá

...
