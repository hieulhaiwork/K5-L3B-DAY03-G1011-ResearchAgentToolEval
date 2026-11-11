# Team

## Thông tin nhóm

- Tên nhóm: G1011
- Lớp: L3B
- Repo nhóm: `K5-L3B-DAY03-G1011-ResearchAgentToolEval`
- URL repo, nhánh nộp, commit chốt:

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
|   1 |Lê Hiền Hiếu   | 2A202603940     | 26ai.hieulh@vinuni.edu.vn      |  hieulhaiwork      | PM/AI Optimizer        |
|   2 |        |      |       |        |         |
|   3 | Trần Xuân Lộc | 2A202603951     |    xuanloca2tv@gmail.com |   Kaylez-TXL       | CP3: 3 tool bóng đá, unit test; CP4: eval nhóm; bonus Test challenge |
|   4 | Nguyễn Quang Tiệp | 2A202603946 | 26ai.tiepnq@vinuni.edu.vn | nguyenquangtiep |         |

## Cá nhân

Mỗi thành viên đồng thời tạo một báo cáo riêng trong `report/` theo dạng:

```text
report/team/MSSV_HoTen.md
```

Ví dụ: `report/team/20241234_NguyenVanAn.md`.

Sao chép mục dưới đây cho từng thành viên.

## Lê Hiền Hiếu — 2A202603940

### Phần việc phụ trách

Nhóm trưởng phụ trách chính là thống nhất ý tưởng, phân chia công việc đều cho các thành viên trong nhóm, tham gia hợp tác cùng NguyenQuangTiep để hoàn thành CP1 và CP2. Trong khi chờ tích hợp tool mới, tôi đề xuất 10 testcase tự tạo để làm baseline định hướng cho 2 bạn viết tool mới. Cuối cùng viết code cho streamlit để demo trực quan.

### Đóng góp cụ thể

- CP1 + CP2: Hợp tác với NguyenQuangTiep cùng hoàn thành việc chạy mô hình baseline v0 trên bộ eval-base. Sau đó cả hai người cùng phân tích lỗi, dự đoán xem vì sao lỗi đó xảy ra, thay đổi system_prompt.md và tools.yaml qua tổng cộng 5 version mới PASS hết các testcase trong bộ eval-base.

- CP4: Khởi tạo sẵn 10 testcases để test các chức năng của model v5 trong thời gian đợi TranXuanLoc và DuongMinhChien tích hợp các tool vào model. Sau đó để TranXuanLoc và DuongMinhChien tự thay đổi các testcases đó để test tool mới.

- CP5: Viết streamlit UI để demo.

- Hoàn thiện các báo cáo: individual report, group_report, version_log.csv

### Bằng chứng

- [Báo cáo cá nhân](report/team/2A202603940_LeHienHieu.md), [báo cáo nhóm B3/B5a/B5](report/team/group_report.md).
- Tôi đóng vai trò phân tích lỗi, đề xuất thay đổi prompt_system và tools describe sau đó gửi các thay đổi sang NguyenQuangTiep thông qua discord để tiết kiệm thời gian. Sau đó chạy thử nghiệm model trên máy tính của NguyenQuangTiep nên bạn đó có các commit về runs v1,v2,v3,v4,v5 và prompt_system cũng như tools. Các commit đó thực tế là công sức của tôi và NguyenQuangTiep cùng làm.
- Comit 1199fca để khởi tạo bộ Eval group.
- [Runs](starter_v0/runs/), [system prompt](starter_v0/artifacts/system_prompt.md), [tool declarations](starter_v0/artifacts/tools.yaml), [version log](starter_v0/artifacts/version_log.csv)
- [Streamlit App](starter_v0/app.py)

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
