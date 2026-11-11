# Báo cáo nhóm — Day 03 Research Agent Tool Eval

> Báo cáo gồm 2 phần có hạn khác nhau:
> - **Phần A (mục 2)** — giới thiệu agent, ngắn gọn 1 trang. **Xong trước Team showdown (16:30)** để team khác hiểu nhanh agent có tool gì, làm được gì. Có thể làm thêm poster `report/team/poster.html` hoặc `poster.svg`.
> - **Phần B (mục 3–7)** — chi tiết và bằng chứng, dựa trên log thật. Hoàn thiện trước deadline nộp bài.
>
> Mỗi bảng phải trỏ được tới file thật: run JSON, transcript, commit. Cách chấm xem [RUBRIC.md](../../RUBRIC.md).

## 1. Thông tin nhóm

- Tên nhóm: G1011
- Thành viên và phân công: xem [TEAM.md](../../TEAM.md)
- Provider/model dùng cho v0–v3:

## 2. Mục tiêu và cách tiếp cận — PHẦN A: Giới thiệu agent

### A1. Agent này làm được gì

> 1–2 câu mô tả agent dùng để làm gì (cho team khác hiểu nhanh).

Ví dụ: "Research agent: tìm tin theo từ khóa / theo tài khoản, đọc URL, tổng hợp thành digest, và gửi lên Telegram khi được xác nhận."

Nhóm xây dựng một agent thử nghiệm hỗ trợ tìm tin bóng đá, đọc nội dung từ link và tính phong độ đội bóng từ danh sách kết quả được cung cấp. Trong phần việc của Trần Xuân Lộc, nhóm sử dụng tool có sẵn của bài lab và thêm ba tool: tính phong độ, đọc nhiều link và lọc bài đăng từ một nhóm tài khoản X.

Phạm vi hiện tại còn nhỏ: nhóm đã kiểm tra cách chọn tool, truyền tham số và tính thống kê cơ bản. Agent chưa có nguồn dữ liệu tỷ số trực tiếp riêng; thông tin tìm được vẫn cần kiểm tra nguồn.

**Cách chạy UI:**

> Lệnh chạy UI (ví dụ `streamlit run app.py`) và dependency đã thêm vào `starter_v0/requirements.txt`.

**Link dùng thử (deploy):**

> Dán link public để team khác mở thử ngay. Cách deploy nhanh bằng Cloudflare Tunnel xem README. Nếu deploy Vercel/Streamlit Cloud thì dán link đó.
>
> URL:

### A2. Tool agent có

> Liệt kê các tool agent đang dùng (gồm tool mới nhóm tự thêm). Mỗi tool 1 dòng: tên + làm được gì.

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| `clarify` | Hỏi lại khi thiếu thông tin hoặc cần xác nhận. | không |
| `lookup` | Tìm kiếm thông tin trên web. | không |
| `fetch` | Đọc nội dung một đường link. | không |
| `social_search` | Tìm bài đăng X theo từ khóa. | không |
| `timeline` | Lấy bài đăng của một tài khoản X. | không |
| `format` | Trình bày dữ liệu thành bản tin hoặc thread. | không |
| `send` | Gửi Telegram sau khi người dùng xác nhận. | không |
| `policy` | Tra cứu tài liệu chính sách nội bộ mẫu. | không |
| `papers`, `paper_text` | Tìm paper và đọc PDF arXiv; không phải trọng tâm thử nghiệm bóng đá. | không |
| `football_stats` | Tính phong độ, điểm và bàn thắng/bại từ danh sách trận. | có |
| `football_headlines` | Đọc nhiều link, loại URL trùng và ghi lỗi từng nguồn. | có |
| `football_mentions` | Lọc bài có từ khóa trong timeline của một nhóm tài khoản X. | có |

### A3. Câu hỏi mẫu để thử

> 3–5 câu hỏi/yêu cầu mẫu để team khác tự thử agent ngay.

1. Tìm tin tức mới về Arsenal trong hôm nay, kèm link nguồn.
2. Lấy 5 bài đăng mới nhất của tài khoản X `Arsenal`.
3. Tính phong độ Arsenal từ danh sách theo thứ tự cũ đến mới: `[{'team':'Arsenal','scored':2,'conceded':1}, {'team':'Arsenal','scored':0,'conceded':0}]`.
4. Đọc hai [trang tin Arsenal](https://www.arsenal.com/news) và [Liverpool](https://www.liverpoolfc.com/news) để chuẩn bị bản tin, đọc tối đa 2 nguồn.
5. Trong hai tài khoản X Arsenal và PremierLeague, lọc bài có chữ Chelsea; chỉ xem 5 bài mỗi tài khoản và trả tối đa 5 bài khớp.

## 3. Giải pháp

> Tóm tắt các thay đổi chính trong `starter_v0/artifacts/system_prompt.md` và `starter_v0/artifacts/tools.yaml`, và tool mới nhóm viết (tên, làm gì, khi nào agent nên gọi).

### 3.1. Ba tool do Trần Xuân Lộc phụ trách

| Tool | Phần code | Phạm vi |
|---|---|---|
| `football_stats` | [tool.py](../../starter_v0/tools/football_stats/tool.py), [TOOL.md](../../starter_v0/tools/football_stats/TOOL.md) | Tính W-D-L, điểm và bàn thắng/bại từ dữ liệu có sẵn. Kiểm tra dữ liệu thiếu/sai; không tự tìm kết quả trận. |
| `football_headlines` | [tool.py](../../starter_v0/tools/football_headlines/tool.py), [TOOL.md](../../starter_v0/tools/football_headlines/TOOL.md) | Dùng Firecrawl hiện có để đọc tối đa 5 URL duy nhất. Giữ bài đọc được khi nguồn khác lỗi; trả đoạn nội dung tối đa 4.000 ký tự mỗi nguồn. |
| `football_mentions` | [tool.py](../../starter_v0/tools/football_mentions/tool.py), [TOOL.md](../../starter_v0/tools/football_mentions/TOOL.md) | Dùng RapidAPI hiện có để lấy timeline tối đa 5 tài khoản, lọc một cụm từ và loại tweet trùng ID. Không phân trang hoặc theo dõi nền. |

Hai tool mới bổ sung xử lý theo nhóm và lỗi từng nguồn, sử dụng lại hàm fetch/timeline; không chỉ đổi tên tool có sẵn. Không thêm key hay thư viện. Đã đăng ký code và khai báo hai tool mới; giữ nguyên system prompt, khai báo các tool cũ và version_log.csv của CP1/CP2. Nhãn chạy vẫn là v5, tools_hash mới phân biệt bộ tool đã mở rộng.

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

Chạy bằng OpenRouter / `openai/gpt-4o-mini`, nhãn v5. [Run hiện tại](../../starter_v0/runs/v5_B_group_openrouter_20261111T011314148993.json) có **9/10 PASS**, provider_error_cases=0, measured_cases=total_cases=10. case_accuracy, tool_routing_accuracy và argument_accuracy = 0.9; multiturn_accuracy = 1.0.

Lệnh chạy từ `starter_v0/`:

```text
python run_eval.py --provider openrouter --model openai/gpt-4o-mini --version v5 --suite group --eval-cases data/eval_group.json
```

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01_football_stats_routing | Phân tích phong độ đội bóng từ danh sách trận đấu -> gọi tool mới football_stats thay vì lookup hay format. | `football_stats {"team_a": "Arsenal"}` | PASS |
| G02_missing_handle_pronoun | Sử dụng đại từ mập mờ (anh ấy) -> Không được đoán bừa mà phải dùng clarify (text) để hỏi rõ handle. | `clarify {"response_type": "text"}` | PASS |
| G03_format_template_thread | Từ khóa 'thread' -> phải map đúng tham số template='thread' của tool format. | `format {"template": "thread"}` | PASS |
| G04_out_of_scope_scripting | Yêu cầu có vẻ liên quan đến tin tức nhưng thực chất là viết code -> Từ chối, không gọi tool. | `Không gọi tool` | PASS |
| G05_football_headlines_routing | Nhận diện yêu cầu đọc nhiều nguồn, chọn football_headlines thay vì gọi fetch riêng từng URL. | `football_headlines {"urls": ["https://www.arsenal.com/news", "https://www.liverpoolfc.com/news"], "max_articles": 2}` | FAIL: model gọi fetch hai lần |
| G06_multi_fetch_after_search | Multi-turn: Carry over URL từ lượt trước và nhận diện yêu cầu đọc nội dung -> gọi tool fetch. | `fetch {"url": "https://tech.com/openai-news"}` | PASS |
| G07_multi_telegram_boundary | Multi-turn: Dù đã có sẵn nội dung từ các turn trước, hành động gửi (Telegram) vẫn phải hỏi confirm (yes_no) trước khi send. | `clarify {"response_type": "yes_no"}` | PASS |
| G08_multi_football_mentions | Giữ nhóm tài khoản, từ khóa và hai giới hạn từ lịch sử; route tới football_mentions để lọc timeline và loại tweet trùng. | `football_mentions {"handles": ["Arsenal", "PremierLeague"], "keyword": "Chelsea", "per_account": 5, "max_results": 5}` | PASS |
| G09_multi_lookup_topic_shift | Multi-turn: Chuyển đổi topic từ general sang news và cập nhật timeframe sang day. | `lookup {"query": "biến đổi khí hậu", "topic": "news", "timeframe": "day"}` | PASS |
| G10_multi_football_stats_clarify | Giữ dữ liệu và tên đội Liverpool từ ngữ cảnh, cập nhật cửa sổ last_n=4 ở lượt cuối. | `football_stats {"team_a": "Liverpool", "last_n": 4}` | PASS |

G05 gọi `fetch` hai lần thay vì `football_headlines`, nên bị chấm sai routing. Kết quả này kiểm tra lựa chọn tool/args; chất lượng dữ liệu trả về được xem thêm ở mục 5.

### B4. Live Chat Evidence

Lấy từ `starter_v0/transcripts/*.transcript.json`.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
|  |  |  |  |  |

### B5a. Required Evidence — Tool mới, unit test, UI

| Item | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Tool mới `football_stats` | [tool.py](../../starter_v0/tools/football_stats/tool.py), [TOOL.md](../../starter_v0/tools/football_stats/TOOL.md) | Tính thống kê và so sánh; G01/G10 có output thật | Validation trả error dict; không tự tạo dữ liệu thiếu |
| Tool mới `football_headlines` | [tool.py](../../starter_v0/tools/football_headlines/tool.py), [TOOL.md](../../starter_v0/tools/football_headlines/TOOL.md) | 13 lượt unit test; G05 còn sai routing | Loại trùng, giới hạn request, lỗi riêng và bài rỗng |
| Tool mới `football_mentions` | [tool.py](../../starter_v0/tools/football_mentions/tool.py), [TOOL.md](../../starter_v0/tools/football_mentions/TOOL.md) | G08 đọc 2 tài khoản thật; 15 lượt unit test | Lọc trong mẫu timeline, loại ID trùng, lỗi từng tài khoản |
| Unit test tool mới (≥ 3 test/tool) | [test_tools_todo.py](../../starter_v0/tests/test_tools_todo.py), output bên dưới | football_stats: 22; headlines: 13; mentions: 15 lượt test sau tham số hóa | Offline, mock HTTP; toàn suite không skip |
| UI (lệnh chạy + link dùng thử) |  |  |  |

Tool unit tests: số test đã viết, và một ví dụ lỗi mà unit test bắt được nhưng eval không bắt được.

Lệnh từ `starter_v0/`: `python -m pytest -q`. Output đã ghi nhận:

```text
172 passed, 1 warning in 0.70s
```

Toàn dự án: 172 passed, 0 failed, 0 skipped, gồm cả test của các thành viên khác. Phần của Lộc trong `test_tools_todo.py` có 64 lượt sau tham số hóa: 22 cho football_stats, 13 cho football_headlines, 15 cho football_mentions và 14 test stub có sẵn. Test chạy offline bằng mock, kiểm tra input sai, nhánh lỗi và request/response API. Warning đến từ plugin anyio, không phải lỗi test.

Ví dụ regression: G01 từng gọi đúng tool/team_a nhưng bỏ tên đội trong bản ghi trận. Tool cũ trả success với 0 trận; test `test_football_stats_malformed_record_returns_error_without_raising` yêu cầu trả error dict. Eval chỉ kiểm tra routing/args nên chưa phát hiện kết quả thống kê sai này.


### B5. Bonus Evidence

Chỉ điền nếu nhóm làm bonus (ghi riêng, tối đa 10 điểm). Tool có sẵn (`send`, `policy`, `papers`, `paper_text`) không tự được bonus.

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Small Local Model | xem B7 |  |  |
| Hơn 3 tool mới (≥ 4) |  |  |  |
| `send` gửi thật lên Telegram sau xác nhận | transcript |  |  |
| Test challenge (0 skipped / regression test) | [test_tools_todo.py](../../starter_v0/tests/test_tools_todo.py), output B5a | 172 passed, 0 failed, 0 skipped toàn suite | Offline, mock HTTP |

Test challenge: số bug tìm được trong tool có sẵn (nếu có), cách sửa, và test regression tương ứng.

Đã triển khai 14 test stub của tool có sẵn, kiểm tra request/response và tách chỉ dẫn nhúng khỏi facts trong policy. Bằng chứng Test challenge dựa vào toàn suite 0 skipped.

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

- G03 ban đầu nhắc dữ liệu từ lượt trước dù là single turn; đã bổ sung dữ liệu cụ thể vào câu hỏi.
- [Log eval hiện tại](../../starter_v0/runs/v5_B_group_openrouter_20261111T011314148993.json) ghi G05 chọn fetch riêng từng URL thay vì football_headlines. Đã làm rõ description của tool mới; kết quả hiện tại vẫn 9/10.
- URL mẫu G06 trả nội dung rỗng dù routing PASS; không thể dùng điểm routing để khẳng định đã đọc được bài.
- [Log lỗi kết nối](../../starter_v0/runs/v5_B_group_openrouter_20261110T232339619559.json) có 10 provider_error và measured_cases=0; không dùng run này tính metric.


## 6. Tổng hợp đóng góp

Chi tiết đóng góp của từng thành viên nằm trong [TEAM.md](../../TEAM.md) và các báo cáo cá nhân `report/team/MSSV_HoTen.md`.

Trần Xuân Lộc phụ trách football_stats, football_headlines, football_mentions, unit test, eval nhóm 10 case và Test challenge; xem [báo cáo cá nhân](2A202603951_TranXuanLoc.md).

## 7. Hạn chế và hướng cải thiện — B6. Reflection

- Fix nào thuộc `system_prompt.md`?

Giữ nguyên system prompt trong phần CP3/CP4.

- Fix nào thuộc `tools.yaml`?

Bổ sung khai báo hai tool mới và làm rõ description football_headlines để phân biệt đọc nhiều URL với fetch một URL.

- Failure nào cần review thủ công thay vì chấm tự động?

Cần xem nội dung tool trả về, nguồn rỗng và nội dung từ chối; routing PASS chưa bảo đảm câu trả lời có ích.

- Nếu có thêm một vòng, nhóm sẽ thử giả thuyết nào?

Thử cải thiện cách mô tả tool đọc nhiều nguồn để giảm việc model gọi fetch riêng lẻ ở G05; đo lại trên cùng bộ case.

## 8. Tài liệu tham khảo

- [Yêu cầu bài lab](../../README.md), [checkpoints](../../CHECKPOINTS.md), [rubric](../../RUBRIC.md).
- [Contract tool](../../starter_v0/tools/README.md), [hướng dẫn API dùng chung](../../docs/TOOL-SETUP.md).
- [Ví dụ unit test](../../starter_v0/tests/test_tools_examples.py) và ba file TOOL.md ở mục 3.1.
