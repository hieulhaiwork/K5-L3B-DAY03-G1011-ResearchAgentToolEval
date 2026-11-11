# Team

## Thông tin nhóm

- Tên nhóm: G1011
- Lớp: L3B
- Repo nhóm: `K5-L3B-DAY03-G1011-ResearchAgentToolEval`
- URL repo, nhánh nộp, commit chốt:

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
|   1 |        |      |       |        |         |
|   2 | Dương Minh Chiến | 2A202603921 | 26ai.chiendm3@vinuni.edu.vn | duongchien147 | CP3: 3 tool bóng đá (top_scorers, standings, team_fixtures), unit test; CP4: eval case routing cho 3 tool |
|   3 | Trần Xuân Lộc | 2A202603951     |    xuanloca2tv@gmail.com |   Kaylez-TXL       | CP3: 3 tool bóng đá, unit test; CP4: eval nhóm; bonus Test challenge |
|   4 | Nguyễn Quang Tiệp | 2A202603946 | 26ai.tiepnq@vinuni.edu.vn | nguyenquangtiep |         |

## Cá nhân

Mỗi thành viên đồng thời tạo một báo cáo riêng trong `report/` theo dạng:

```text
report/team/MSSV_HoTen.md
```

Ví dụ: `report/team/20241234_NguyenVanAn.md`.

Sao chép mục dưới đây cho từng thành viên.

## HoVaTen-MSSV

### Phần việc phụ trách

-

### Đóng góp cụ thể

-

### Bằng chứng

-

## Trần Xuân Lộc — 2A202603951

### Phần việc phụ trách

CP3: football_stats, football_headlines, football_mentions và unit test. CP4: 10 case (5 single turn, 5 multi turn), chạy eval và phân tích log. Bonus: Test challenge với 0 skipped.

### Đóng góp cụ thể

- Hoàn thiện validation và regression test football_stats; thêm headlines gom nhiều URL và mentions lọc nhiều timeline, có xử lý trùng và lỗi từng nguồn.
- Thêm code, TOOL.md, đăng ký và khai báo tool mới; giữ nguyên system prompt và khai báo tool cũ của CP1/CP2.
- Viết 50 lượt test cho ba tool sau tham số hóa (22 stats, 13 headlines, 15 mentions), triển khai 14 test stub có sẵn. Toàn suite đạt 172 passed, 0 failed, 0 skipped.
- Chạy eval OpenRouter/openai/gpt-4o-mini trên máy cá nhân, nhãn v5; sau pull đạt 9/10 PASS (G05 còn sai routing). Tổng 172 test pass gồm cả test của thành viên khác.

### Bằng chứng

- [Báo cáo cá nhân](report/team/2A202603951_TranXuanLoc.md), [báo cáo nhóm B3/B5a/B5](report/team/group_report.md).
- [football_stats](starter_v0/tools/football_stats/tool.py), [football_headlines](starter_v0/tools/football_headlines/tool.py), [football_mentions](starter_v0/tools/football_mentions/tool.py); mỗi folder có TOOL.md.
- [Unit test](starter_v0/tests/test_tools_todo.py), [bộ eval nhóm](starter_v0/data/eval_group.json), [run hiện tại](starter_v0/runs/v5_B_group_openrouter_20261111T011314148993.json).
- Commit kỹ thuật: `45804d1` (football_stats và eval nhóm), `cfd1017` (hoàn thiện tool, test và bằng chứng CP3/CP4).

## Nguyễn Quang Tiệp — 2A202603946

### Phần việc phụ trách

- CP1: thiết lập và đánh giá baseline `v0`; CP2: phân tích lỗi và thử nghiệm tối ưu Prompt/Tool Calling qua `v1`–`v3`.

### Đóng góp cụ thể

- Chạy đánh giá base bằng OpenRouter / `openai/gpt-4o-mini`: `v0` có 20 case, 13 PASS (65%), 0 lỗi provider.
- Phân tích 7 case FAIL: R03, R08, R10, R11, R12, R13, R14; phân loại lỗi arguments, thiếu thông tin, ngoài phạm vi và xác nhận trước khi gửi.
- Thử nghiệm cải thiện các quy tắc chọn tool, hỏi lại khi thiếu thông tin và không gửi nội dung khi chưa xác nhận; kết quả `v1`–`v3` cần đối chiếu run JSON tương ứng.

### Bằng chứng

- [Báo cáo cá nhân](report/team/2A202603946_NguyenQuangTiep.md), [phân tích baseline và bảng version ở báo cáo nhóm](report/team/group_report.md).
- [Run v0](starter_v0/runs/v0_B_base_openrouter_20261110T175817951797.json), [system prompt](starter_v0/artifacts/system_prompt.md), [tool declarations](starter_v0/artifacts/tools.yaml), [version log](starter_v0/artifacts/version_log.csv).

## Dương Minh Chiến — 2A202603921

### Phần việc phụ trách

CP3: ba tool bóng đá mới `top_scorers` (vua phá lưới), `standings` (bảng xếp hạng đội), `team_fixtures` (N trận đã đá của một đội trong một mùa) và unit test cho từng tool. CP4: eval case routing cho ba tool, đặt ở file riêng để `eval_group.json` vẫn giữ đúng 10 case.

### Đóng góp cụ thể

- `top_scorers` và `standings` lấy dữ liệu từ API-Football, khi lỗi thì chuyển sang SportScore và ghi lý do vào `attempts`. SportScore không có trường mùa, nên hỏi mùa cũ thì tool trả `data_unavailable`, không đưa dữ liệu mùa hiện tại ra thay. Trường nguồn không có thì trả `null`, giải trùng tên thì trả `candidates` để agent hỏi lại.
- `team_fixtures` trả `matches` đúng format fixture của `football_stats`, nên agent nối được `team_fixtures` → `football_stats`. Gói Free của API-Football chặn `last`/`next` và chỉ mở mùa 2022–2024, nên `season` là tham số bắt buộc và tool không có fallback (widget team của SportScore trả dữ liệu mẫu).
- Ba tool dùng chung phần dò giải, cache 24h và xử lý lỗi; không retry khi gặp 429; API key không xuất hiện trong output. Chỉ thêm file mới và thêm dòng vào `tools/__init__.py`, `tools.yaml`, `.env.example`; không sửa system prompt hay tool của thành viên khác.
- 77 unit test offline (26 `top_scorers`, 51 cho hai tool sau). Toàn suite sau lần rebase cuối: 233 passed, 0 failed. Chạy thật với key Free: `standings` mùa 2024 cho Liverpool 84 điểm đứng đầu; nối `team_fixtures` Arsenal 2024 sang `football_stats` ra phong độ `D-L-D-W-W`, khớp với `form` `"WWDLD"` của `standings`.
- 12 eval case (mỗi tool 4 case, gồm 3 single-turn và 1 multi-turn). Các file đã qua kiểm tra định dạng của `run_eval.py` nhưng chưa chạy với LLM, nên chưa có tỷ lệ PASS.

### Bằng chứng

- [Báo cáo cá nhân](report/team/2A202603921_DuongMinhChien.md).
- [top_scorers](starter_v0/tools/top_scorers/tool.py), [standings](starter_v0/tools/standings/tool.py), [team_fixtures](starter_v0/tools/team_fixtures/tool.py); mỗi folder có TOOL.md ghi giới hạn đã kiểm chứng bằng gọi thật.
- Unit test: [test_top_scorers.py](starter_v0/tests/test_top_scorers.py), [test_standings.py](starter_v0/tests/test_standings.py), [test_team_fixtures.py](starter_v0/tests/test_team_fixtures.py). Eval: [eval_top_scorers.json](starter_v0/data/eval_top_scorers.json), [eval_standings.json](starter_v0/data/eval_standings.json), [eval_team_fixtures.json](starter_v0/data/eval_team_fixtures.json).
- Commit kỹ thuật: `23e97e0` (top_scorers), `791e511` (standings và team_fixtures).
