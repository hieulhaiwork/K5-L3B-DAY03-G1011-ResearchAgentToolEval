---
name: football_mentions
track: core
kind: live_api
provider: RapidAPI
requires_env:
- RAPIDAPI_KEY
- RAPIDAPI_TWITTER_HOST
inputs:
- handles
- keyword
- per_account
- max_results
outputs:
- tool
- status
- handles
- keyword
- items
- errors
- scanned_count
- matched_count
- truncated
- note
side_effect: false
requires_confirmation: false
---

# football_mentions

Lấy timeline từ endpoint RapidAPI đang dùng cho timeline, rồi lọc một cụm từ và loại tweet ID trùng trong nhóm tài khoản. Không tìm toàn X và không theo dõi nền.

- handles: 1–5 tài khoản, 1–15 ký tự chữ ASCII/số/gạch dưới, có thể có @. Chuẩn hóa chữ thường, loại trùng trước khi gọi API.
- keyword: một cụm từ không rỗng, tối đa 200 ký tự; lọc chuỗi con không phân biệt hoa thường, không hiểu Boolean/từ đồng nghĩa.
- per_account: 1–20 bài có ID đầu tiên từ trang timeline trả về; không phân trang. max_results: 1–50 tweet duy nhất trả về. Giữ thứ tự tài khoản đầu vào rồi thứ tự API, không khẳng định toàn bộ kết quả đã sắp theo thời gian.
- items chứa tweet_id, account đã truy vấn, author, text, date từ nguồn và link gốc. Bỏ bản ghi không có ID hoặc ID không hợp lệ. Không xác minh nội dung bài đăng.
- errors ghi riêng tài khoản lỗi. success với items=[] nghĩa là không thấy bài khớp trong mẫu đã đọc, không có nghĩa chưa ai từng nhắc tới từ đó. partial khi có tài khoản đọc được và tài khoản lỗi; error khi toàn bộ lỗi hoặc input sai.
- Dùng RAPIDAPI_KEY và RAPIDAPI_TWITTER_HOST hiện có trong .env. Tối đa 5 lượt timeline mỗi lần gọi, không thêm key/dependency. Không lưu key hoặc response lỗi thô vào output.

Ví dụ: handles=[Arsenal, PremierLeague], keyword=Chelsea, per_account=10.

Test offline từ starter_v0: `python -m pytest -q tests/test_tools_todo.py -k football_mentions`.
