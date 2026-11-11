# Báo cáo cá nhân — Trần Xuân Lộc-2A202603951

Đổi tên file theo quy tắc `MSSV_HoTen.md`.

Ví dụ: `20241234_NguyenVanAn.md`.

## 1. Thông tin thành viên

- Họ tên: Trần Xuân Lộc
- MSSV: 2A202603951
- Email: xuanloca2tv@gmail.com

## 2. Phần việc phụ trách

CP3: hoàn thiện ba tool bóng đá và unit test. CP4: hoàn thiện bộ eval nhóm gồm 10 case (5 single turn, 5 multi turn), chạy kiểm thử và phân tích kết quả. Thực hiện thêm phần Test challenge.

## 3. Đóng góp cụ thể

- `football_stats`: tính phong độ, điểm và bàn thắng/bại từ danh sách trận; kiểm tra dữ liệu thiếu hoặc sai.
- `football_headlines`: dùng Firecrawl đọc nhiều link, loại URL trùng và ghi lỗi từng nguồn.
- `football_mentions`: dùng RapidAPI lấy timeline nhiều tài khoản X, lọc từ khóa và loại tweet trùng.
- Hoàn thiện đăng ký, khai báo và TOOL.md; viết 50 lượt test cho ba tool và triển khai 14 test stub có sẵn, tổng 64 lượt sau tham số hóa. Các test chạy offline bằng mock.
- Cập nhật eval và báo cáo; giữ nguyên system prompt và khai báo tool cũ của nhóm. `top_scorers` do bạn Chiến phụ trách, không thuộc phần việc cá nhân này.

## 4. Bằng chứng

- File/commit/PR: `45804d1` (football_stats và eval nhóm), `cfd1017` (hoàn thiện tool, test và bằng chứng CP3/CP4).

- Code và tài liệu: [football_stats](../../starter_v0/tools/football_stats/TOOL.md), [football_headlines](../../starter_v0/tools/football_headlines/TOOL.md), [football_mentions](../../starter_v0/tools/football_mentions/TOOL.md); mỗi thư mục có `tool.py`.
- [Unit test](../../starter_v0/tests/test_tools_todo.py): toàn dự án **172 passed, 0 failed, 0 skipped**, gồm cả test của các thành viên khác. Phần cá nhân có 64 lượt test như mục 3; đáp ứng điều kiện Test challenge của bài.
- [Eval nhóm](../../starter_v0/data/eval_group.json), [log hiện tại](../../starter_v0/runs/v5_B_group_openrouter_20261111T011314148993.json): **9/10 PASS**, không có provider error. G05 còn gọi `fetch` hai lần thay vì `football_headlines`; đây là lỗi chọn tool cần cải thiện.
- Chạy eval trên máy cá nhân bằng OpenRouter / `openai/gpt-4o-mini`, nhãn v5. Chi tiết output và giới hạn tại B3/B5a của [báo cáo nhóm](group_report.md).

- AI/công cụ đã dùng và cách tự kiểm tra kết quả: Codex hỗ trợ code, test và báo cáo; kiểm chứng bằng pytest, eval API thật và đọc tool_results trong log.

## 5. Tự đánh giá
- Em đã hoàn thành ba tool, unit test và bộ eval trong phần phụ trách. Qua bài này, em hiểu rõ hơn sự khác nhau giữa kiểm thử code và đánh giá cách model chọn tool. Kết quả eval hiện đạt 9/10; em cần cải thiện cách mô tả `football_headlines` để model chọn đúng khi đọc nhiều nguồn.
...
