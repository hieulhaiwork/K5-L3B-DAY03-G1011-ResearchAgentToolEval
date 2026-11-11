# Báo cáo cá nhân — LeHienHieu-2A202603940

## 1. Thông tin thành viên

- Họ tên: Lê Hiền Hiếu
- MSSV: 2A202603940
- Email: 26ai.hieulh@vinuni.edu.vn

## 2. Phần việc phụ trách
Nhóm trưởng phụ trách chính là thống nhất ý tưởng, phân chia công việc đều cho các thành viên trong nhóm, tham gia hợp tác cùng NguyenQuangTiep để hoàn thành CP1 và CP2. Trong khi chờ tích hợp tool mới, tôi đề xuất 10 testcase tự tạo để làm baseline định hướng cho 2 bạn viết tool mới. Cuối cùng viết code cho streamlit để demo trực quan.


## 3. Đóng góp cụ thể

- CP1 + CP2: Hợp tác với NguyenQuangTiep cùng hoàn thành việc chạy mô hình baseline v0 trên bộ eval-base. Sau đó cả hai người cùng phân tích lỗi, dự đoán xem vì sao lỗi đó xảy ra, thay đổi system_prompt.md và tools.yaml qua tổng cộng 5 version mới PASS hết các testcase trong bộ eval-base.

- CP4: Khởi tạo sẵn 10 testcases để test các chức năng của model v5 trong thời gian đợi TranXuanLoc và DuongMinhChien tích hợp các tool vào model. Sau đó để TranXuanLoc và DuongMinhChien tự thay đổi các testcases đó để test tool mới.

- CP5: Viết streamlit UI để demo.

- Hoàn thiện các báo cáo: individual report, group_report, version_log.csv


## 4. Bằng chứng

- File/commit/PR: 
    - Tôi đóng vai trò phân tích lỗi, đề xuất thay đổi prompt_system và tools describe sau đó gửi các thay đổi sang NguyenQuangTiep thông qua discord để tiết kiệm thời gian. Sau đó chạy thử nghiệm model trên máy tính của NguyenQuangTiep nên bạn đó có các commit về runs v1,v2,v3,v4,v5 và prompt_system cũng như tools. Các commit đó thực tế là công sức của tôi và NguyenQuangTiep cùng làm.
    - report/team/group_report.md
    - starter_v0/artifacts/version_log.csv
    - starter_v0/app.py
- AI/công cụ đã dùng và cách tự kiểm tra kết quả:
+ Gemini Chat: Đề xuất hướng giải quyết cho mỗi lỗi mà tôi đã xác định nguyên nhân và cần một hướng để fix (không phải thay đổi prompt hộ tôi). Tự kiểm tra bằng cách đọc lại, thảo luận cùng NguyenQuangTiep để xác nhận theo logic rằng hướng phát triển đó có phù hợp không? Và thay đổi và chạy thử.
+ Copilot: Code file app.py để demo streamlit. Thử nghiệm bằng cách chạy thử, dính 1 error và đã tự đọc logs và fix mà không cần copilot hỗ trợ nữa.

## 5. Tự đánh giá

Kết quả chatbot cuối cùng đạt yêu cầu về chatbot tìm kiếm, tổng hợp, trả lời các câu hỏi về lĩnh vực bóng đá. Tôi tự đánh giá bản thân đã cố gắng hết sức để điều phối nhóm thực hiện các công việc đầy đủ mặc dù 4 người chưa từng gặp nhau bao giờ. Tuy trong giai đoạn đầu nhóm còn bối rối về việc thực hiện như thế nào nhưng qua trao đổi với nhau, tôi đã lập được kế hoạch và phân công công việc với nhau, hoàn thành yêu cầu của lab và kịp tiến độ lab đề ra. 
