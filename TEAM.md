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
- Chạy eval OpenRouter/openai/gpt-4o-mini trên máy cá nhân, nhãn v5; sau pull đạt 9/10 PASS (G05 còn sai routing). Tổng 172 test pass gồm cả test của thành viên khác, không phải toàn bộ do Lộc viết. Không nhận là đã làm UI, gửi Telegram thật hoặc chạy model local.

### Bằng chứng

- [Báo cáo cá nhân](report/team/2A202603951_TranXuanLoc.md), [báo cáo nhóm B3/B5a/B5](report/team/group_report.md).
- [football_stats](starter_v0/tools/football_stats/tool.py), [football_headlines](starter_v0/tools/football_headlines/tool.py), [football_mentions](starter_v0/tools/football_mentions/tool.py); mỗi folder có TOOL.md.
- [Unit test](starter_v0/tests/test_tools_todo.py), [bộ eval nhóm](starter_v0/data/eval_group.json), [run hiện tại](starter_v0/runs/v5_B_group_openrouter_20261111T011314148993.json).
- Commit kỹ thuật đã có: `45804d1` (football_stats và eval nhóm). Phần bổ sung mới chưa có commit chốt, cần review rồi commit/push.
