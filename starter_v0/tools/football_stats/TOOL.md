---
name: football_stats
track: core
kind: live_api
provider: Tavily + Firecrawl + local calculation
requires_env: [TAVILY_API_KEY, FIRECRAWL_API_KEY]
inputs: [team_a, matches, team_b, last_n]
outputs: [status, team_a, team_b, comparison, data_mode, research, matches_used, warning]
side_effect: false
requires_confirmation: false
---

# football_stats

Tự tìm kết quả trận gần đây và tính phong độ một hoặc hai đội; vẫn hỗ trợ tính từ danh sách trận đã có.

## Khi dùng

- Hỏi phong độ gần đây, số trận thắng/hòa/thua, điểm, bàn thắng/bại hoặc so sánh hai đội.
- Ví dụ: `team_a="Liverpool", team_b="MU", last_n=5`. Không cần người dùng nhập tỷ số. MU/Man Utd được chuẩn hóa thành Manchester United.
- Không dùng cho vua phá lưới (top_scorers), tin tức chung (lookup) hoặc lịch sắp tới.

## Hai chế độ

### Tự tìm kết quả (bỏ hẳn matches)

1. Dùng Tavily tìm trang kết quả ESPN của từng đội; không hard-code ID đội hoặc bịa URL.
2. Dùng Firecrawl đọc đầy đủ markdown của trang; code trích tỷ số từ bảng kết quả có tên đội, tháng/năm, link trận và trạng thái FT/FT-Pens/FT-AET/AET. Không dùng LLM tạo bản ghi trận.
3. Bỏ trận tương lai, giao hữu, đang đá, bản ghi thiếu năm và trận cũ hơn 120 ngày. Loại ID trùng; xếp ngày cũ đến mới rồi lấy tối đa last_n trận gần nhất từ bảng nguồn.
4. Tính W-D-L, điểm quy đổi 3/1/0, bàn thắng/bại, hiệu số, sạch lưới và tỷ lệ thắng. Đây là điểm quy đổi để so phong độ trên mọi giải, không phải điểm bảng xếp hạng một giải. Không dùng tỷ số luân lưu để đổi trận hòa thành thắng.

last_n mặc định 5, hỗ trợ 1–20. Mỗi đội tối đa 1 Tavily search và 2 Firecrawl scrape; dừng khi đọc được một trang kết quả phù hợp. Dùng hai key hiện có, không cần API/provider mới. Ngày hiện tại lấy theo UTC+7.

Output có `data_mode=automatic_research`, `matches_used` với ngày/tỷ số/đối thủ/link từng trận và `research` với trang nguồn, as_of, số trận yêu cầu. Nếu có ít hơn số trận yêu cầu, trả partial và cảnh báo; không xếp đội tốt hơn khi mẫu chưa đủ. Nếu không đọc được nguồn cho một trong hai đội, trả error dict thay vì tự tạo tỷ số.

Giới hạn: hiện parser chỉ hỗ trợ bảng kết quả ESPN có cấu trúc như trên; có thể lỗi khi site đổi layout, thiếu đội hoặc bị chặn. Không đảm bảo dữ liệu nguồn chính xác hoặc đã cập nhật mọi trận vừa kết thúc. Chỉ phân tích các trận có trong bảng lấy được, không tuyên bố kiểm chứng chéo nhiều nguồn. Không có phân trang tự động.

### Dữ liệu sẵn có (truyền matches)

- Chỉ truyền khi có kết quả cụ thể trong ngữ cảnh; model không được tự đoán tỷ số. Chế độ này không gọi mạng.
- Danh sách theo thứ tự cũ đến mới. Mỗi bản ghi có `team`, `scored`, `conceded` hoặc `home_team`, `away_team`, `home_score`, `away_score`.
- Tỷ số là số nguyên không âm (nhận chuỗi số nguyên), không nhận boolean/số thập phân hoặc trường thiếu. Lỗi trả error dict, không raise.
- `matches=[]` là dữ liệu rỗng được cung cấp rõ: trả 0 trận và N/A, không tự tìm. So sánh tổng điểm/hiệu số ở chế độ dữ liệu sẵn có có thể lệch nếu số trận hai đội khác nhau.

## Kiểm tra

Từ starter_v0: `python -m pytest -q tests/test_tools_todo.py -k football_stats`. Unit test offline gồm bảng nguồn thật dạng rút gọn, chuẩn hóa MU, request API, lọc trận tương lai/giao hữu, luân lưu, nguồn sai, thiếu key, partial và bảo toàn chế độ dữ liệu sẵn có.
