# Báo cáo cá nhân — DuongMinhChien-2A202603921

## 1. Thông tin thành viên

- Họ tên: Dương Minh Chiến
- MSSV: 2A202603921
- Email: 26ai.chiendm3@vinuni.edu.vn
- GitHub: `duongchien147`

## 2. Phần việc phụ trách

Tôi thiết kế, cài đặt và kiểm thử tool mới `top_scorers` ở CP3. Tool trả về bảng xếp hạng vua phá lưới của một giải bóng đá, phục vụ hướng Football Research Agent của nhóm. Tôi cũng viết unit test và eval case routing cho tool này (CP3, CP4).

## 3. Đóng góp cụ thể

### 3.1. Tool `top_scorers` ([`starter_v0/tools/top_scorers/`](../../starter_v0/tools/top_scorers/))

Tool lấy dữ liệu từ hai nguồn. Nguồn chính là API-Football, cần `API_FOOTBALL_KEY`: tool gọi `/leagues` để lấy league id, danh sách mùa, mùa hiện tại và `coverage.top_scorers`, sau đó gọi `/players/topscorers`. Nguồn dự phòng là SportScore (`/api/widget/topscorers/`, không cần key). Khi API-Football lỗi (thiếu key, 401/403, 429, gói Free không có mùa, 5xx, timeout, JSON hỏng…), tool tự chuyển sang SportScore và ghi lý do vào `attempts` và `provider.fallback_reason` chứ không giấu lỗi.

Các quy tắc xử lý dữ liệu:

- Trường nào provider không có (phạt đền, quốc tịch, tuổi…) thì trả `null`, không thay bằng 0.
- SportScore không trả metadata mùa, nên với yêu cầu mùa cũ tool trả `data_unavailable`; dữ liệu mùa hiện tại không được đưa ra thay cho mùa được hỏi.
- Khi tên giải bị trùng, tool trả `ambiguous_competition` kèm danh sách `candidates` để agent hỏi lại user. Slug SportScore chỉ lấy từ các slug đã kiểm chứng, hoặc từ kết quả search khớp chính xác tên giải.
- Input được kiểm tra trước khi gọi HTTP. Kết quả được cache 24h vì gói Free chỉ có 100 request/ngày. Tool không retry khi gặp 429, và API key không bao giờ xuất hiện trong output.

Tool luôn trả dict, không raise, đúng yêu cầu C4.

### 3.2. Đăng ký tool

- [`tools/__init__.py`](../../starter_v0/tools/__init__.py): thêm `"top_scorers": top_scorers`.
- [`artifacts/tools.yaml`](../../starter_v0/artifacts/tools.yaml): khai báo tool, mô tả khi nào nên dùng và khi nào không (để phân biệt với `football_stats` và `lookup`), kèm quy ước args. `season` là năm bắt đầu mùa (2025/26 → 2025), `limit` từ 1 đến 20, còn `country` dùng để phân biệt các giải trùng tên.
- [`.env.example`](../../starter_v0/.env.example): thêm tên biến `API_FOOTBALL_KEY=`, để trống giá trị.

### 3.3. Unit test ([`tests/test_top_scorers.py`](../../starter_v0/tests/test_top_scorers.py))

File có 26 test, chạy offline: `requests.get` được mock nên không có lời gọi mạng thật. Các nhóm test:

- Happy path: API-Football resolve league 39 và season 2025, map đúng thứ hạng, bàn thắng, kiến tạo, phạt đền; chuỗi `"2025/26"` được đổi thành 2025.
- Fallback: thiếu key thì chuyển sang SportScore; 401/403/429 cũng chuyển sang SportScore và không retry; lỗi `plan` nằm trong body của response HTTP 200.
- Bảo vệ mùa giải: mùa 2022 không bị thay bằng dữ liệu hiện tại, và SportScore không được gọi.
- Cả hai nguồn cùng lỗi: 500 và timeout cho ra `data_unavailable` có cấu trúc, key không lộ trong output.
- Input xấu: giải rỗng hoặc `None`, `limit` bằng 0, 21 hay "ten", `season` 99, `country` 123 đều trả `invalid_input` và không phát sinh request nào.
- Trường hợp khác: giải trùng tên trả `candidates`; cache tránh gọi lại; JSON hỏng trả `invalid_json`.

### 3.4. Eval case ([`data/eval_top_scorers.json`](../../starter_v0/data/eval_top_scorers.json))

Có 4 case, gồm 3 single-turn và 1 multi-turn. Câu hỏi phải được route tới `top_scorers` với `season=2025, limit=10`; câu "Chiếc giày vàng" không được route sang `lookup`; câu thiếu tên giải phải dẫn tới `clarify`; case multi-turn gom đủ tên giải cùng `season=2024, limit=5`. Các case nằm ở file riêng vì `eval_group.json` của nhóm phải giữ đúng 10 case.

## 4. Bằng chứng

- File/commit/PR:
  - Commit chính `23e97e0` (_feat(CP3): add top_scorers tool with API-Football primary and SportScore fallback_): 7 file, +1091 dòng, 0 dòng xoá, đã merge vào `main`.
  - Commit `794ab19` tạo báo cáo cá nhân.
  - Commit `428df30` (_Add top scorers research too_) là bản đầu tiên của tool. Nhóm đã revert commit này ở `142d701` vì nó sửa quá nhiều file dùng chung, trong đó có `system_prompt.md`. Bản `23e97e0` được làm lại từ đầu và chỉ chạm vào các file của tool.
- `pytest`: `tests/test_top_scorers.py` 26 passed. Toàn suite 101 passed, 14 skipped, 0 failed (14 test skipped là stub có sẵn trong `test_tools_todo.py`). `tests/test_tool_contract.py` vẫn xanh sau khi thêm tool.
- Chạy thật ngày 2026-11-10:
  - Premier League, mùa hiện tại: API-Football trả _"Free plans do not have access to this season, try from 2022 to 2024"_, tool fallback sang SportScore và trả top 5 (Haaland 9 bàn, Isak 7…), `season.verified: false`, có attribution.
  - Premier League, `season=2024`: API-Football trả dữ liệu, `verified: true`, không phải fallback.
- AI/công cụ đã dùng và cách tự kiểm tra kết quả: tôi dùng Claude Code để đọc codebase. Cách tôi kiểm tra kết quả:
  1. Gọi thử endpoint thật của API-Football và SportScore để lấy cấu trúc JSON thật rồi mới viết mock, không để AI tự đoán schema.
  2. Chạy `pytest` toàn suite và contract test sau mỗi thay đổi.
  3. Chạy tool thật với key Free để xác nhận cả nhánh fallback lẫn nhánh API-Football.
  4. Xem `git diff --stat` trước khi commit để chắc rằng chỉ có dòng thêm, không đụng file của thành viên khác và `.env` không bị stage.
  5. Đọc response gốc khi thấy số liệu bất thường (xem mục 5).

## 5. Tự đánh giá

...
