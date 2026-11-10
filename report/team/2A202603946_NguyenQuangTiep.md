# Báo cáo cá nhân — 

Đổi tên file theo quy tắc `MSSV_HoTen.md`.

Ví dụ: `20241234_NguyenVanAn.md`.

## 1. Thông tin thành viên

- Họ tên: Nguyễn Quang Tiệp
- MSSV: 2A202603946
- Email: 26ai.tiepnq@vinuni.edu.vn

## 2. Phần việc phụ trách

Đánh giá baseline `v0` và tối ưu Prompt/Tool Calling cho Research Agent qua các phiên bản `v1`, `v2`, `v3`; phân tích lỗi chọn công cụ, truyền tham số và xử lý yêu cầu thiếu thông tin. Phần phát triển tool mới và UI do các thành viên khác phụ trách.

## 3. Đóng góp cụ thể

- Cấu hình và chạy đánh giá Agent với provider OpenRouter, model `openai/gpt-4o-mini` trên bộ `data/eval_base.json` gồm 20 case.
- Chạy baseline `v0`, ghi nhận **13/20 case PASS (65%)**, `tool_routing_accuracy = 0.75`, `argument_accuracy = 0.65`, `multiturn_accuracy = 1.0`, `provider_error_cases = 0`.
- Phân tích 7 case FAIL của `v0`: `R03`, `R08`, `R10`, `R11`, `R12`, `R13`, `R14`; xác định các vấn đề về arguments, gọi tool ngoài phạm vi, tự suy đoán thông tin còn thiếu và gọi `send` khi chưa xác nhận.
- Thực hiện các vòng tối ưu `v1`–`v3` và chạy lại base evaluation. Kết quả `v3` đạt **20/20 case PASS (100%)** theo kết quả chạy đã thông báo; run JSON của `v3` chưa được đối chiếu trong repository.

## 4. Bằng chứng

- File/commit/PR: `starter_v0/artifacts/system_prompt.md`; `starter_v0/artifacts/tools.yaml`; `v0_B_base_openrouter_20261110T175817951797.json` (file kết quả v0 đã cung cấp); commit/PR cá nhân: 
- AI/công cụ đã dùng và cách tự kiểm tra kết quả: ChatGPT hỗ trợ đọc và phân tích run JSON, gợi ý tối ưu prompt; Python, PowerShell và OpenRouter dùng để chạy `scripts/preflight_provider.py` và `run_eval.py`. Đối chiếu `expect` với `actual_tool_calls`, kiểm tra `passed`, `observed_mismatch`, `failures` và các chỉ số trong `summary` của file run. 

## 5. Tự đánh giá

Kết quả đánh giá trên bộ base được báo cáo tăng từ **13/20 (65%)** ở `v0` lên **20/20 (100%)** ở `v3`. Phần phân tích lỗi baseline được xác nhận bằng run JSON `v0`; kết quả `v3` cần có run JSON tương ứng trong repository để làm bằng chứng chính thức. Kết quả trên bộ base không thay thế việc đánh giá các case mới và kiểm tra lại sau khi tích hợp tool của nhóm.
