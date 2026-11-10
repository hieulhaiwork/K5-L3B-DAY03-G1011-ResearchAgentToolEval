# Báo cáo nhóm — Day 03 Research Agent Tool Eval

> Báo cáo gồm 2 phần có hạn khác nhau:
> - **Phần A (mục 2)** — giới thiệu agent, ngắn gọn 1 trang. **Xong trước Team showdown (16:30)** để team khác hiểu nhanh agent có tool gì, làm được gì. Có thể làm thêm poster `report/team/poster.html` hoặc `poster.svg`.
> - **Phần B (mục 3–7)** — chi tiết và bằng chứng, dựa trên log thật. Hoàn thiện trước deadline nộp bài.
>
> Mỗi bảng phải trỏ được tới file thật: run JSON, transcript, commit. Cách chấm xem [RUBRIC.md](../../RUBRIC.md).

## 1. Thông tin nhóm

- Tên nhóm: G1011
- Thành viên và phân công: xem [TEAM.md](../../TEAM.md)
- Provider/model dùng cho v0–v3: OpenAPI (ChatGPT)

## 2. Mục tiêu và cách tiếp cận — PHẦN A: Giới thiệu agent

### A1. Agent này làm được gì

AI Agent tự động tìm kiếm thông tin về lĩnh vực bóng đá (ví dụ: tối nay có trận đấu nào? kết quả như thế nào? đội hình ra sân của đội nào? Tiểu sử của một cầu thủ?...)

*Note:* Agent phù hợp nhất với các câu hỏi cần tổng hợp nhiều nguồn: lịch thi đấu,
kết quả mới nhất, tin tức, phát biểu trên mạng xã hội và hồ sơ cầu thủ. Với
thông tin có tính thời gian thực như tỷ số hoặc đội hình ra sân, agent phải
hiển thị thời điểm cập nhật và nguồn; không được suy đoán khi chưa có dữ liệu
đáng tin cậy.

**Cách chạy UI:** (để sau)

> Lệnh chạy UI (ví dụ `streamlit run app.py`) và dependency đã thêm vào `starter_v0/requirements.txt`.

**Link dùng thử (deploy):**

> Dán link public để team khác mở thử ngay. Cách deploy nhanh bằng Cloudflare Tunnel xem README. Nếu deploy Vercel/Streamlit Cloud thì dán link đó.
>
> URL:

### A2. Tool agent có

> Liệt kê các tool agent đang dùng (gồm tool mới nhóm tự thêm). Mỗi tool 1 dòng: tên + làm được gì.

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| `clarify` | Hỏi lại khi thiếu định danh đội/cầu thủ, giải đấu, ngày hoặc múi giờ; nên dùng trước khi tìm nếu có nhiều khả năng trùng tên. | không |
| `lookup` | Tìm web/Tavily theo từ khóa; dùng cho tin bóng đá, lịch/kết quả, tiểu sử và thông tin đội/cầu thủ. `topic=news` + `timeframe=day` phù hợp tin nóng; trả về tiêu đề, URL, nguồn, tóm tắt và điểm liên quan. | không |
| `fetch` | Đọc toàn văn một URL đã tìm được; dùng để kiểm tra chi tiết đội hình, tỷ số hoặc tiểu sử từ nguồn gốc trước khi trả lời. | không |
| `social_search` | Tìm bài đăng X theo từ khóa, sắp xếp `Latest` hoặc `Top`; phù hợp phát biểu/chấn thương/đội hình được CLB hoặc nhà báo đăng. Đây là nguồn tham khảo, không nên là nguồn duy nhất cho tỷ số chính thức. | không |
| `timeline` | Lấy bài đăng mới nhất của một tài khoản X cụ thể; phù hợp theo dõi tài khoản chính thức của CLB, giải đấu hoặc nhà báo. `screenname` không có ký tự `@`. | không |
| `format` | Chuẩn hóa các kết quả đã thu thập thành bản tin Markdown (`brief`, `sections`, `bullets`, `daily_ai_vn`); dùng ở bước cuối để câu trả lời có cấu trúc và link nguồn. | không |
| `send` | Gửi bản tin qua Telegram sau khi người dùng xác nhận rõ; phù hợp đăng ký bản tin/lịch nhắc, không gọi tự động khi chưa xác nhận vì có side effect. | không (bonus có sẵn) |
| `policy` | Tra cứu chính sách nội bộ về trích dẫn, quyền riêng tư và sử dụng tool; không phải nguồn dữ liệu bóng đá nhưng giúp kiểm soát cách trả lời. | không (bonus có sẵn) |

### A2.1. Ma trận nhu cầu và luồng gọi tool

| Nhu cầu bóng đá | Tool nên gọi | Cách dùng/giới hạn |
|---|---|---|
| Tối nay có trận nào? | `lookup` → `fetch` → `format` | Thêm ngày hiện tại, múi giờ và tên giải vào truy vấn; đối chiếu trang lịch chính thức trước khi kết luận. |
| Kết quả trận vừa kết thúc | `lookup(topic=news, timeframe=day)` → `fetch` → `format` | Trích tỷ số, thời điểm và trạng thái trận; nếu nguồn mâu thuẫn phải nêu rõ hoặc tìm nguồn thứ hai. |
| Đội hình ra sân | `lookup` → `fetch`; có thể bổ sung `social_search`/`timeline` | Phân biệt đội hình dự kiến và đội hình chính thức; chỉ gọi `send` sau xác nhận nếu người dùng muốn nhận thông báo. |
| Tiểu sử cầu thủ/đội bóng | `lookup` → `fetch` → `format` | Ưu tiên nguồn chính thức hoặc hồ sơ uy tín; chuẩn hóa tên để tránh nhầm cầu thủ trùng tên. |
| Phản ứng và tin nóng | `social_search` hoặc `timeline` → `lookup` → `format` | Gắn thời gian đăng và tài khoản; không coi bài đăng mạng xã hội là thông tin đã được xác minh. |
| Phân tích chiến thuật/số liệu | `lookup` → `papers` → `paper_text` → `format` | Tách dữ liệu trận đấu khỏi kết luận nghiên cứu; nêu năm và giới hạn của bài nghiên cứu. |

### A3. Câu hỏi mẫu để thử

> 3–5 câu hỏi/yêu cầu mẫu để team khác tự thử agent ngay.

1. Tối nay (giờ Việt Nam) có những trận bóng đá đáng chú ý nào? Cho tôi giờ đá, giải đấu và link nguồn.
2. Kết quả trận Liverpool gặp Manchester City gần nhất là gì? Ai ghi bàn và trận đã kết thúc chưa?
3. Đội hình ra sân chính thức của Việt Nam trong trận gần nhất là ai? Phân biệt với đội hình dự kiến.
4. Hãy tóm tắt tiểu sử và phong độ gần đây của [tên cầu thủ], kèm nguồn và ngày cập nhật.
5. Tìm các phát biểu mới nhất của tài khoản X chính thức của [CLB] về trận đấu sắp tới, rồi tạo bản tin ngắn.

## 3. Giải pháp

> Tóm tắt các thay đổi chính trong `starter_v0/artifacts/system_prompt.md` và `starter_v0/artifacts/tools.yaml`, và tool mới nhóm viết (tên, làm gì, khi nào agent nên gọi).


### 3.1. Tool bổ sung đề xuất cho phiên bản bóng đá

| Ưu tiên | Tool đề xuất | Chức năng chính | Giá trị trải nghiệm và yêu cầu an toàn |
|---|---|---|---|
| P0 | `football_fixtures` | Lịch trận theo ngày, giải đấu, đội; trả về múi giờ, sân, trạng thái và ID trận. | Giải quyết trực tiếp câu hỏi “tối nay có trận nào”; dùng API dữ liệu thể thao có timestamp và cache ngắn. |
| P0 | `football_match` | Tỷ số trực tiếp/chung cuộc, phút thi đấu, bàn thắng, thẻ, thay người và sự kiện trận. | Tránh ghép dữ liệu từ bài báo; phải công bố `last_updated` và trạng thái `scheduled/live/finished/postponed`. |
| P0 | `football_lineups` | Đội hình chính thức, dự bị, sơ đồ và cầu thủ vắng mặt. | Phân biệt `predicted`/`confirmed`, ghi nguồn và thời điểm xác nhận. |
| P1 | `football_team` | Hồ sơ đội, HLV, sân nhà, danh hiệu và phong độ gần đây. | Chuẩn hóa theo `team_id` thay vì chỉ tên để tránh nhầm CLB/đội tuyển. |
| P1 | `football_player` | Tiểu sử, vị trí, quốc tịch, đội hiện tại và thống kê mùa giải. | Trả về `player_id`, ngày sinh đã được kiểm chứng và nguồn; không suy luận dữ liệu nhạy cảm. |
| P1 | `football_standings` | Bảng xếp hạng theo giải/mùa: điểm, hiệu số, trận đã đấu, quy tắc xếp hạng. | Hỗ trợ câu hỏi “đội đang đứng thứ mấy”; cần tham số mùa giải và thời điểm cập nhật. |
| P1 | `football_stats` | Thống kê cầu thủ/đội theo trận hoặc mùa: bàn, kiến tạo, phút, xG nếu nguồn có. | Hiển thị định nghĩa chỉ số và mẫu dữ liệu, tránh so sánh khác giải khi chưa chuẩn hóa. |
| P1 | `source_verify` | Đối chiếu nhiều nguồn, chấm độ tin cậy và đánh dấu mâu thuẫn. | Giảm hallucination cho tỷ số/đội hình; không tự biến dữ liệu chưa xác minh thành kết luận chắc chắn. |
| P2 | `football_alerts` | Đăng ký nhắc trận, thay đổi tỷ số, đội hình hoặc tin chấn thương. | Tăng tính chủ động; cần lịch sử đăng ký, chống gửi trùng và cơ chế hủy. |
| P2 | `football_compare` | So sánh hai đội/cầu thủ trong cùng giải và cùng khoảng thời gian. | Trả bảng chỉ số có cùng định nghĩa; không đưa ra khuyến nghị cá cược. |
| P2 | `football_translate` | Dịch thuật ngữ/bản tin bóng đá giữa tiếng Việt và ngôn ngữ nguồn. | Hữu ích cho người dùng Việt; giữ nguyên tên riêng, tỷ số, đơn vị và link gốc. |

**Thứ tự triển khai đề xuất:** làm `football_fixtures`, `football_match`,
`football_lineups` trước; sau đó thêm `football_player`, `football_standings`
và `source_verify`. Đây là nhóm bao phủ các nhu cầu cốt lõi, giảm phụ thuộc
vào tìm kiếm web tự do và giúp kiểm thử đầu ra có cấu trúc.

## 4. Kết quả — PHẦN B: Chi tiết và bằng chứng

### B1. Version Evidence

Lấy từ `starter_v0/artifacts/version_log.csv` và `starter_v0/runs/*.json`. Chỉ dùng run có `provider_error_cases == 0` và `measured_cases == total_cases`.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline |  |  |  |  |
| v1 |  |  |  |  |  |
| v2 |  |  |  |  |  |
| v3 |  |  |  |  |  |

### B2. Failure Analysis

Lấy từ `results[*].result.failures` trong run JSON.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
|  |  |  |  |  |

### B3. Team Eval Cases

Liệt kê đúng 10 case trong `starter_v0/data/eval_group.json` (5 single turn + 5 multi turn).

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
|  |  |  |  |

### B4. Live Chat Evidence

Lấy từ `starter_v0/transcripts/*.transcript.json`.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
|  |  |  |  |  |

### B5a. Required Evidence — Tool mới, unit test, UI

| Item | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Tool mới (`tools/<tên>/`) |  |  |  |
| Unit test tool mới (≥ 3 test/tool) | `pytest` output (0 failed) |  |  |
| UI (lệnh chạy + link dùng thử) |  |  |  |

Tool unit tests: số test đã viết, và một ví dụ lỗi mà unit test bắt được nhưng eval không bắt được.

### B5. Bonus Evidence

Chỉ điền nếu nhóm làm bonus (ghi riêng, tối đa 10 điểm). Tool có sẵn (`send`, `policy`, `papers`, `paper_text`) không tự được bonus.

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Small Local Model | xem B7 |  |  |
| Hơn 3 tool mới (≥ 4) |  |  |  |
| `send` gửi thật lên Telegram sau xác nhận | transcript |  |  |
| Test challenge (0 skipped / regression test) | `pytest` output |  |  |

Test challenge: số bug tìm được trong tool có sẵn (nếu có), cách sửa, và test regression tương ứng.

### B7. Small Local Model Challenge (bonus)

Chỉ điền nếu nhóm làm bonus này.

| Version | Model (provider) | Prompt/Tools | case_accuracy | tool_routing | argument | multiturn | Run File |
|---|---|---|---|---|---|---|---|
| v3 | (cloud) | v3 |  |  |  |  |  |
| v3-<model> | (ollama) | v3 |  |  |  |  |  |
| v3-<model> | (ollama) | v3 |  |  |  |  |  |
| v4-local |  |  |  |  |  |  |  |
| v5-local |  |  |  |  |  |  |  |

Lỗi đặc thù của model nhỏ (đếm từ run JSON):

| Failure Pattern | Count | Example Case | Fix Tried | Helped? |
|---|---|---|---|---|
| wrong / hallucinated tool |  |  |  |  |
| invalid JSON args (`_invalid_json_arguments`) |  |  |  |  |
| no tool call / answered directly |  |  |  |  |
| missed `clarify` |  |  |  |  |
| repeated / unnecessary calls |  |  |  |  |

- Cái gì giúp model nhỏ gọi tool đúng hơn nhất? Bằng chứng?
- Bản prompt tối ưu cho local chạy trên model cloud thì sao?
- Khi nào nhóm sẽ chọn model local thay vì cloud cho agent này?

## 5. Khó khăn và cách xử lý

> Khó khăn chính và cách nhóm xử lý. Nếu gặp lỗi kỹ thuật (provider lỗi, hết quota API, tool không chạy), mô tả lỗi và dẫn bằng chứng: run JSON, log, ảnh chụp.

-

## 6. Tổng hợp đóng góp

Chi tiết đóng góp của từng thành viên nằm trong [TEAM.md](../../TEAM.md) và các báo cáo cá nhân `report/team/MSSV_HoTen.md`.

## 7. Hạn chế và hướng cải thiện — B6. Reflection

- Fix nào thuộc `system_prompt.md`?
- Fix nào thuộc `tools.yaml`?
- Failure nào cần review thủ công thay vì chấm tự động?
- Nếu có thêm một vòng, nhóm sẽ thử giả thuyết nào?

## 8. Tài liệu tham khảo

-
