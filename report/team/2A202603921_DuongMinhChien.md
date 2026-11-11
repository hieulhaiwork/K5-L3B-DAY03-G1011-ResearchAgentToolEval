# Báo cáo cá nhân — DuongMinhChien-2A202603921

## 1. Thông tin thành viên

- Họ tên: Dương Minh Chiến
- MSSV: 2A202603921
- Email: 26ai.chiendm3@vinuni.edu.vn
- GitHub: `duongchien147`

## 2. Phần việc phụ trách

Tôi thiết kế, cài đặt và kiểm thử ba tool mới ở CP3, phục vụ hướng Football Research Agent của nhóm:

- `top_scorers`: bảng xếp hạng vua phá lưới của một giải.
- `standings`: bảng xếp hạng đội của một giải.
- `team_fixtures`: N trận đã đá gần nhất của một đội trong một mùa, để nối sang `football_stats` tính phong độ.

Với mỗi tool, tôi viết unit test và eval case routing (CP3, CP4).

## 3. Đóng góp cụ thể

### 3.1. Tool `top_scorers` ([`starter_v0/tools/top_scorers/`](../../starter_v0/tools/top_scorers/))

Tool lấy dữ liệu từ hai nguồn. Nguồn chính là API-Football, cần `API_FOOTBALL_KEY`: tool gọi `/leagues` để lấy league id, danh sách mùa, mùa hiện tại và `coverage.top_scorers`, sau đó gọi `/players/topscorers`. Nguồn dự phòng là SportScore (`/api/widget/topscorers/`, không cần key). Khi API-Football lỗi (thiếu key, 401/403, 429, gói Free không có mùa, 5xx, timeout, JSON hỏng…), tool tự chuyển sang SportScore và ghi lý do vào `attempts` và `provider.fallback_reason` chứ không giấu lỗi.

Các quy tắc xử lý dữ liệu:

- Trường nào provider không có (phạt đền, quốc tịch, tuổi…) thì trả `null`, không thay bằng 0.
- SportScore không trả metadata mùa, nên với yêu cầu mùa cũ tool trả `data_unavailable`; dữ liệu mùa hiện tại không được đưa ra thay cho mùa được hỏi.
- Khi tên giải bị trùng, tool trả `ambiguous_competition` kèm danh sách `candidates` để agent hỏi lại user. Slug SportScore chỉ lấy từ các slug đã kiểm chứng, hoặc từ kết quả search khớp chính xác tên giải.
- Input được kiểm tra trước khi gọi HTTP. Kết quả được cache 24h vì gói Free chỉ có 100 request/ngày. Tool không retry khi gặp 429, và API key không bao giờ xuất hiện trong output.

### 3.2. Tool `standings` ([`starter_v0/tools/standings/`](../../starter_v0/tools/standings/))

Tool trả bảng xếp hạng đội của một giải: hạng, đội, số trận, thắng/hoà/thua, bàn thắng/bại, hiệu số, điểm, chuỗi phong độ 5 trận và mô tả suất (Champions League, Relegation…). Nguồn chính là API-Football `/standings`, nguồn dự phòng là SportScore `/api/widget/standings/`, đúng mô hình của `top_scorers`.

Các quy tắc giữ nguyên như `top_scorers`. SportScore không có trường mùa, nên hỏi mùa cũ thì tool không lấy bảng mùa hiện tại thay vào. Trường nguồn không có (SportScore không có `form` và id đội) thì trả `null`. Giải trùng tên trả `ambiguous_competition`. Giải có nhiều bảng (vòng bảng cúp) được tách thành nhiều phần tử trong `groups`.

Chuỗi `form` của API-Football xếp trận gần nhất đứng đầu. Tôi kiểm tra điều này bằng dữ liệu thật: Arsenal mùa 2024 có `"WWDLD"`, còn 5 trận cuối theo thời gian là D, L, D, W, W.

### 3.3. Tool `team_fixtures` ([`starter_v0/tools/team_fixtures/`](../../starter_v0/tools/team_fixtures/))

Tool lấy N trận đã đá gần nhất của một đội trong một mùa, sắp từ cũ đến mới. Danh sách `matches` dùng đúng format fixture của `football_stats` (`home_team`, `away_team`, `home_score`, `away_score`), nên agent nối được `team_fixtures` → `football_stats`. Trước đây `football_stats` bắt user tự đưa danh sách trận.

Gọi thử ngày 2026-11-11 cho thấy gói Free của API-Football chặn tham số `last` và `next` của `/fixtures`, và chỉ mở mùa 2022–2024. Vì vậy tool lấy nguyên lịch một mùa rồi tự lọc và cắt. `season` là tham số bắt buộc, còn mùa ngoài khoảng đó trả `data_unavailable` kèm lý do `plan_restriction`. Tool không có nguồn dự phòng: widget `/api/widget/team/` của SportScore trả cùng một trận mẫu "Arsenal vs Chelsea" cho cả `arsenal` lẫn `chelsea`, nên không dùng được.

Các quy tắc xử lý dữ liệu:

- Đội được tìm qua `/teams?search=`, chỉ nhận tên khớp chính xác. Tìm "Arsenal" ra 3 đội cùng tên (Anh, Guadeloupe, Belarus), nên khi không có `country` tool trả `ambiguous_team` kèm `candidates`, không tự chọn.
- Chỉ giữ trận có status `FT`, `AET`, `PEN` và đủ tỷ số. Trận hoãn, huỷ hoặc thiếu tỷ số bị bỏ qua, không điền tỷ số giả.
- Tỷ số là kết quả sau 90 phút hoặc sau hiệp phụ. Loạt luân lưu nằm riêng trong `penalty_shootout`, vì `goals` của API-Football không tính luân lưu.
- Không truyền `competition` thì kết quả gồm mọi giải, kể cả giao hữu, và `warning` có ghi rõ điều đó. Arsenal mùa 2024 có 63 trận như vậy, trong đó có trận giao hữu thắng 2-1 Manchester United vẫn đá luân lưu.

### 3.4. Phần dùng chung và đăng ký

- Trong [`top_scorers/tool.py`](../../starter_v0/tools/top_scorers/tool.py), tôi tách phần dò giải thành `_resolve_api_football_league` và `_api_football_key`, hành vi không đổi (26 test cũ vẫn pass). Ba tool dùng chung một cache, nên lần tra `/leagues` của tool này tiết kiệm quota cho tool kia. Cả ba luôn trả dict, không raise (yêu cầu C4).
- [`tools/__init__.py`](../../starter_v0/tools/__init__.py): thêm `top_scorers`, `standings`, `team_fixtures`. [`.env.example`](../../starter_v0/.env.example): thêm tên biến `API_FOOTBALL_KEY=`, để trống giá trị.
- [`artifacts/tools.yaml`](../../starter_v0/artifacts/tools.yaml): khai báo ba tool ở cuối file, mỗi tool có mô tả khi nào dùng và khi nào không. `top_scorers` tách khỏi `football_stats` và `lookup`; `standings` (đội) tách khỏi `top_scorers` (cầu thủ); `team_fixtures` dùng cho một mùa cụ thể đã qua rồi chuyển `matches` sang `football_stats`, còn phong độ gần đây thì để `football_stats` tự tìm. Quy ước args: `season` là năm bắt đầu mùa (2025/26 → 2025), `limit` từ 1 đến 20, `country` để phân biệt giải hoặc đội trùng tên.

### 3.5. Unit test

77 test chạy offline (mock `requests.get`, không gọi mạng thật): 26 trong [`test_top_scorers.py`](../../starter_v0/tests/test_top_scorers.py), 51 trong [`test_standings.py`](../../starter_v0/tests/test_standings.py) và [`test_team_fixtures.py`](../../starter_v0/tests/test_team_fixtures.py). Các nhóm test:

- Happy path: resolve league 39 và mùa, map đúng từng trường; chuỗi `"2025/26"` được đổi thành 2025.
- Fallback: thiếu key, 401/403/429 (không retry) và lỗi `plan` nằm trong body của response HTTP 200 đều chuyển sang SportScore.
- Bảo vệ mùa giải: mùa 2022 không bị thay bằng dữ liệu hiện tại, SportScore không được gọi.
- Cả hai nguồn cùng lỗi (500, timeout) trả `data_unavailable` có cấu trúc; key không lộ trong output.
- Input xấu (giải rỗng hoặc `None`, `limit` 0/21/"ten", `season` 99, `country` 123, thiếu `season` với `team_fixtures`) trả `invalid_input` và không phát sinh request nào.
- Giải hoặc đội trùng tên trả `candidates`; trận chưa đá bị bỏ qua; luân lưu tách khỏi tỷ số; cache tránh gọi lại; JSON hỏng trả `invalid_json`; một test nối thẳng output `team_fixtures` vào `football_stats`.

### 3.6. Eval case

12 case, mỗi tool 4 case (3 single-turn, 1 multi-turn), nằm ở 3 file riêng vì `eval_group.json` của nhóm phải giữ đúng 10 case: [`eval_top_scorers.json`](../../starter_v0/data/eval_top_scorers.json), [`eval_standings.json`](../../starter_v0/data/eval_standings.json), [`eval_team_fixtures.json`](../../starter_v0/data/eval_team_fixtures.json).

- Tham số: "mùa 2025/26" phải thành `season=2025`, "top 10" thành `limit=10`, "5 trận cuối" thành `last_n=5`.
- Chọn đúng tool: câu "Chiếc giày vàng" không được route sang `lookup`; câu hỏi điểm số của đội (S02) không được route sang `top_scorers`; F02 yêu cầu lượt đầu gọi `team_fixtures`, gọi ngay `football_stats` với danh sách trận tự bịa là sai.
- Thiếu thông tin: thiếu tên giải hoặc thiếu mùa phải dẫn tới `clarify`.
- Multi-turn: gom thông tin qua nhiều lượt, ví dụ Bundesliga + mùa 2024/25 + top 5 thành `season=2024, limit=5`.

## 4. Bằng chứng

- File/commit/PR:
  - `23e97e0` (_feat(CP3): add top_scorers tool with API-Football primary and SportScore fallback_): 7 file, +1091 dòng, 0 dòng xoá. Bản đầu `428df30` (_Add top scorers research too_) bị nhóm revert ở `142d701` vì sửa quá nhiều file dùng chung, trong đó có `system_prompt.md`; `23e97e0` được làm lại từ đầu và chỉ chạm vào các file của tool.
  - `791e511` (_feat(CP3): add standings and team_fixtures tools_): 11 file, +1543 dòng, 4 dòng xoá (phần tách hàm trong `top_scorers/tool.py`).
  - `2450c27`: eval với LLM, gồm mô tả `standings`/`team_fixtures` trong `tools.yaml` qua v6–v10 và 32 file run. Các dòng v6–v10 trong [`version_log.csv`](../../starter_v0/artifacts/version_log.csv) ghi lý do, giả thuyết và số liệu trước/sau của từng lần sửa.
- `pytest`: lúc thêm `top_scorers`, 26 test của tool pass, toàn suite 101 passed, 14 skipped (stub có sẵn trong `test_tools_todo.py`). Sau `791e511`: 233 passed. Trên `main` hiện tại (sau commit `8239fc1` của Lộc): 246 passed, 0 failed. `tests/test_tool_contract.py` xanh ở cả ba thời điểm.
- Chạy thật với key Free:
  - 2026-11-10, `top_scorers` Premier League mùa hiện tại: API-Football trả _"Free plans do not have access to this season, try from 2022 to 2024"_, tool fallback sang SportScore và trả top 5 (Haaland 9 bàn, Isak 7…), `season.verified: false`, có attribution. Với `season=2024`: API-Football trả dữ liệu, `verified: true`.
  - 2026-11-11, `standings("Premier League", 2024, "England")`: Liverpool hạng 1 với 84 điểm, Arsenal hạng 2 với 74 điểm. Mùa hiện tại: fallback sang SportScore (`fallback_reason: plan_restriction`), bảng 20 đội, Arsenal dẫn đầu 27 điểm sau 10 trận.
  - 2026-11-11, `team_fixtures("Arsenal", 2024, "Premier League", "England", 5)`: 5 trận cuối mùa, từ Arsenal 2-2 Crystal Palace đến Southampton 1-2 Arsenal. Đưa thẳng vào `football_stats` ra phong độ `D-L-D-W-W`, khớp với `form` `"WWDLD"` của `standings` khi đọc ngược. Mùa 2025 trả `data_unavailable` (`plan_restriction`); không kèm `country` trả `ambiguous_team`.
- Eval với LLM ngày 2026-11-11, OpenRouter / `openai/gpt-4o-mini`. Mỗi version chạy 12 case của ba tool và chạy lại 10 case của `eval_group.json` để kiểm tra hồi quy; mọi run có provider_error_cases=0.

  | Version | Thay đổi trong mô tả `standings` / `team_fixtures` | 12 case của tôi | `eval_group` |
  |---|---|---|---|
  | v6 | Mô tả lúc commit `791e511` | 7/12 | 9/10 |
  | v7 | Thêm "GỌI THẲNG …, KHÔNG gọi clarify để xác nhận lại" | 10/12 | 8/10 |
  | v8 | Thêm quy tắc "lấy năm đứng trước dấu '/'" cho `season` | 12/12 | 8/10 (2 lần) |
  | v9 | Viết lại hai câu trên bằng giọng bình thường, giữ nguyên ý | 12/12 (2 lần) | 9/10 (2 lần) |
  | v10 | Sau `8239fc1`: thêm ranh giới với `football_stats` tự tìm kết quả | 12/12 (2 lần) | 8/10 (2 lần) |

  - Ở v6 (`top_scorers` 4/4, `standings` 2/4, `team_fixtures` 1/4), cả 5 case fail đều do model gọi `clarify` dạng `yes_no` để xác nhận lại dù câu hỏi đã đủ giải, đội và mùa (F03 hỏi đúng chuyện mùa nhưng dùng `yes_no` thay vì `text`). Ở v7, S01 và F02 còn đổi "2023/24" thành `season=2024`.
  - Từ v7, G08 gọi `football_mentions` hai lần. Chạy lại `eval_group` với `tools.yaml` của v6 (nhãn `v6check`) được 9/10 cả hai lần, nên lỗi do cách viết hoa mạnh của v7; v9 sửa được.
  - Ở v10, G05 và G08 fail. Với `tools.yaml` trên `main` không có thay đổi của tôi (nhãn `v10base`) kết quả cũng là 8/10 cả hai lần với cùng hai case, và hai run v5 Lộc commit cùng ngày có một lần G08 pass, một lần fail. G08 không ổn định từ trước; đây là case của Lộc nên tôi không sửa.
  - Run v10: [top_scorers](../../starter_v0/runs/v10_B_group_openrouter_20261111T105958560103.json), [standings](../../starter_v0/runs/v10_B_group_openrouter_20261111T110009615199.json), [team_fixtures](../../starter_v0/runs/v10_B_group_openrouter_20261111T110021824098.json). Mọi thay đổi chỉ nằm ở mô tả `standings` và `team_fixtures`; system prompt và mô tả các tool khác giữ nguyên.
- AI/công cụ đã dùng và cách tự kiểm tra kết quả: tôi dùng Claude Code để đọc codebase. Cách tôi kiểm tra kết quả:
  1. Gọi thử endpoint thật của API-Football và SportScore để lấy cấu trúc JSON thật rồi mới viết mock, không để AI tự đoán schema.
  2. Chạy `pytest` toàn suite và contract test sau mỗi thay đổi.
  3. Chạy tool thật với key Free để xác nhận cả nhánh fallback lẫn nhánh API-Football.
  4. Xem `git diff --stat` trước khi commit để chắc rằng chỉ có dòng thêm, không đụng file của thành viên khác và `.env` không bị stage.
  5. Đọc response gốc khi thấy số liệu bất thường (xem mục 5).

## 5. Tự đánh giá

Những phần làm được:

- Ba tool `top_scorers`, `standings`, `team_fixtures` chạy với dữ liệu thật. Khi nguồn chính lỗi, tool chuyển sang nguồn dự phòng hoặc trả lỗi kèm lý do, không trả dữ liệu sai mùa hay tỷ số tự điền. Có 77 unit test chạy offline, và 12 eval case đạt 12/12 với `openai/gpt-4o-mini` ở cả hai lần chạy.
- Trước khi viết code, tôi gọi thử API thật để biết giới hạn: gói Free của API-Football chỉ mở mùa 2022–2024 và chặn `last`/`next`, còn widget team của SportScore trả dữ liệu mẫu. Các giới hạn này được ghi vào TOOL.md của từng tool.
- Mỗi lần sửa mô tả tool đều có giả thuyết, chạy lại eval và ghi vào `version_log.csv` (v6–v10).

Những phần chưa tốt và rút kinh nghiệm:

- Bản đầu của `top_scorers` (`428df30`) sửa quá nhiều file dùng chung, trong đó có `system_prompt.md`, nên bị nhóm revert ở `142d701`. Từ đó tôi chỉ thêm file mới và thêm dòng vào file chung.
- Ở v7, câu tôi thêm vào mô tả hai tool làm case G08 của Lộc fail. Tôi phát hiện được vì chạy lại `eval_group.json` sau mỗi thay đổi. Sửa mô tả một tool có thể làm đổi cách model chọn tool khác, nên phải chạy lại cả bộ eval của nhóm, không chỉ case của mình.
- Eval chỉ chấm tool và tham số, không bắt được lỗi dữ liệu phía nguồn. API-Football trả Matheus Cunha 30 bàn sau 66 trận cho mùa Premier League 2024, trong khi một mùa chỉ có 38 trận. Tool chuyển nguyên số liệu nên không tự phát hiện. Tôi chỉ thấy khi đọc response gốc, nên số liệu bất thường vẫn cần kiểm tra bằng tay.
- Với key Free, `team_fixtures` không trả lời được phong độ của mùa đang đá. Muốn dùng thật thì cần key trả phí hoặc một nguồn dữ liệu khác.
