# Báo cáo cá nhân — Nguyễn Quang Tiệp-2A202603946

Đổi tên file theo quy tắc `MSSV_HoTen.md`.

Ví dụ: `20241234_NguyenVanAn.md`.

## 1. Thông tin thành viên

- Họ tên: Nguyễn Quang Tiệp
- MSSV: 2A202603946
- Email: 26ai.tiepnq@vinuni.edu.vn

## 2. Phần việc phụ trách

CP1: chạy baseline `v0`, đọc run JSON và phân tích lỗi của Agent. CP2: tối ưu Prompt/Tool Calling qua `v1`, `v2`, `v3`. Phần viết tool mới, unit test cho tool mới, bộ Group Eval và UI do thành viên khác phụ trách.

## 3. Đóng góp cụ thể

- Chạy `run_eval.py` với provider `openrouter`, model `openai/gpt-4o-mini`, bộ `data/eval_base.json` gồm 20 case.
- Ghi nhận v0: 13/20 PASS (`case_accuracy=0.65`), `tool_routing_accuracy=0.75`, `argument_accuracy=0.65`, `multiturn_accuracy=1.0`; `provider_error_cases=0`, `measured_cases=20`.
- Đối chiếu `expect` với `actual_tool_calls` và phân tích 7 case FAIL: R03, R08, R10, R11, R12, R13, R14. Các lỗi gồm truyền sai tham số, tự điền thông tin thiếu, gọi `send` sai mục đích và thiếu xác nhận trước khi gửi.
- Thử nghiệm tối ưu qua v1–v3; kết quả v3 20/20 là kết quả người thực hiện đã thông báo, chưa tìm được run JSON v3 có thể đối chiếu trong repository.

## 4. Bằng chứng

- File/commit/PR: [Run v0](../../starter_v0/runs/v0_B_base_openrouter_20261110T175817951797.json); [system_prompt.md](../../starter_v0/artifacts/system_prompt.md); [tools.yaml](../../starter_v0/artifacts/tools.yaml); [version_log.csv](../../starter_v0/artifacts/version_log.csv); commit/PR cá nhân:
- AI/công cụ đã dùng và cách tự kiểm tra kết quả: ChatGPT hỗ trợ giải thích lỗi, rà soát run và gợi ý cải thiện prompt. Python/PowerShell, OpenRouter và `run_eval.py` được sử dụng để chạy kiểm thử. Tự kiểm tra bằng cách đối chiếu `expect`, `actual_tool_calls`, `observed_mismatch`, `failures` và `summary` trong JSON; chỉ tính run không có lỗi provider.

## 5. Tự đánh giá

Đã xác minh baseline v0 đạt 13/20 case PASS (65%) và xác định 7 lỗi cụ thể. Theo kết quả đã thông báo, v3 đạt 20/20 case PASS (100%), nhưng chưa có run JSON v3 được xác minh trong repository nên chưa thể dùng làm bằng chứng chính thức. Cần bổ sung run v1–v3, thông số hash và commit kỹ thuật cá nhân để chứng minh toàn bộ vòng tối ưu; kết quả base không thay thế Group Eval hoặc kiểm thử sau tích hợp.
