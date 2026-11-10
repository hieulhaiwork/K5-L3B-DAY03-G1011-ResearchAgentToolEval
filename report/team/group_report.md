# Báo cáo nhóm — Day 03 Research Agent Tool Eval

Phần A giới thiệu agent; Phần B ghi kết quả và bằng chứng. Nội dung dưới đây cập nhật phần CP3/CP4 của Trần Xuân Lộc: football_stats, football_headlines và football_mentions. Phần tool và eval của thành viên khác do người phụ trách tự bổ sung. Các mục chờ CP1/CP2 và CP5 được ghi rõ bên dưới.

## 1. Thông tin nhóm

- Tên nhóm: G1011
- Thành viên và phân công: xem [TEAM.md](../../TEAM.md)
- Provider/model CP1/CP2: chờ thành viên phụ trách xác nhận và hoàn thiện cùng bảng B1.
- Kiểm thử CP3/CP4 trên máy cá nhân: OpenRouter / `openai/gpt-4o-mini`, nhãn v5 (chi tiết B3).

## 2. Mục tiêu và cách tiếp cận — PHẦN A: Giới thiệu agent

### A1. Agent này làm được gì

Nhóm xây dựng một agent thử nghiệm hỗ trợ tìm tin bóng đá, đọc nội dung từ link và tính phong độ đội bóng từ danh sách kết quả được cung cấp. Trong phần việc của Trần Xuân Lộc, nhóm sử dụng tool có sẵn của bài lab và thêm ba tool: tính phong độ, đọc nhiều link và lọc bài đăng từ một nhóm tài khoản X.

Phạm vi hiện tại còn nhỏ: nhóm đã kiểm tra cách chọn tool, truyền tham số và tính thống kê cơ bản. Agent chưa có nguồn dữ liệu tỷ số trực tiếp riêng; thông tin tìm được vẫn cần kiểm tra nguồn.

**UI và link dùng thử (CP5):** chưa có bằng chứng trong bản báo cáo hiện tại. Thành viên phụ trách cần bổ sung lệnh chạy, dependency và URL dùng thử.

### A2. Tool được mô tả trong phần báo cáo này

| Tên tool | Chức năng | Nguồn |
|---|---|---|
| `clarify` | Hỏi lại khi thiếu thông tin hoặc cần xác nhận. | Có sẵn |
| `lookup` | Tìm kiếm thông tin trên web. | Có sẵn |
| `fetch` | Đọc nội dung một đường link. | Có sẵn |
| `social_search` | Tìm bài đăng X theo từ khóa. | Có sẵn |
| `timeline` | Lấy bài đăng của một tài khoản X. | Có sẵn |
| `format` | Trình bày dữ liệu thành bản tin hoặc thread. | Có sẵn |
| `send` | Gửi Telegram sau khi người dùng xác nhận. Chưa có bằng chứng gửi thật. | Có sẵn |
| `policy` | Tra cứu tài liệu chính sách nội bộ mẫu. | Có sẵn |
| `papers`, `paper_text` | Tìm paper và đọc PDF arXiv; không phải trọng tâm thử nghiệm bóng đá. | Có sẵn |
| `football_stats` | Tính phong độ, điểm và bàn thắng/bại từ danh sách trận. | Nhóm tự thêm |
| `football_headlines` | Đọc nhiều link, loại URL trùng và ghi lỗi từng nguồn. | Nhóm tự thêm |
| `football_mentions` | Lọc bài có từ khóa trong timeline của một nhóm tài khoản X. | Nhóm tự thêm |

### A3. Câu hỏi mẫu để thử

1. Tìm tin tức mới về Arsenal trong hôm nay, kèm link nguồn.
2. Lấy 5 bài đăng mới nhất của tài khoản X `Arsenal`.
3. Tính phong độ Arsenal từ danh sách theo thứ tự cũ đến mới: `[{'team':'Arsenal','scored':2,'conceded':1}, {'team':'Arsenal','scored':0,'conceded':0}]`.
4. Đọc hai [trang tin Arsenal](https://www.arsenal.com/news) và [Liverpool](https://www.liverpoolfc.com/news) để chuẩn bị bản tin, đọc tối đa 2 nguồn.
5. Trong hai tài khoản X Arsenal và PremierLeague, lọc bài có chữ Chelsea; chỉ xem 5 bài mỗi tài khoản và trả tối đa 5 bài khớp.

## 3. Giải pháp

Phần CP1/CP2 do thành viên phụ trách bổ sung. Phần dưới mô tả ba tool và công việc CP3/CP4 đã kiểm chứng.


### 3.1. Ba tool do Trần Xuân Lộc phụ trách

| Tool | Phần code | Phạm vi |
|---|---|---|
| `football_stats` | [tool.py](../../starter_v0/tools/football_stats/tool.py), [TOOL.md](../../starter_v0/tools/football_stats/TOOL.md) | Tính W-D-L, điểm và bàn thắng/bại từ dữ liệu có sẵn. Kiểm tra dữ liệu thiếu/sai; không tự tìm kết quả trận. |
| `football_headlines` | [tool.py](../../starter_v0/tools/football_headlines/tool.py), [TOOL.md](../../starter_v0/tools/football_headlines/TOOL.md) | Dùng Firecrawl hiện có để đọc tối đa 5 URL duy nhất. Giữ bài đọc được khi nguồn khác lỗi; trả đoạn nội dung tối đa 4.000 ký tự mỗi nguồn. |
| `football_mentions` | [tool.py](../../starter_v0/tools/football_mentions/tool.py), [TOOL.md](../../starter_v0/tools/football_mentions/TOOL.md) | Dùng RapidAPI hiện có để lấy timeline tối đa 5 tài khoản, lọc một cụm từ và loại tweet trùng ID. Không phân trang hoặc theo dõi nền. |

Hai tool mới bổ sung xử lý theo nhóm và lỗi từng nguồn, sử dụng lại hàm fetch/timeline; không chỉ đổi tên tool có sẵn. Không thêm key hay thư viện. Đã đăng ký code và khai báo hai tool mới; giữ nguyên system prompt, khai báo các tool cũ và version_log.csv của CP1/CP2. Nhãn chạy vẫn là v5, tools_hash mới phân biệt bộ tool đã mở rộng.

## 4. Kết quả — PHẦN B: Chi tiết và bằng chứng

### B1. Version Evidence

**Chờ thành viên phụ trách CP1/CP2 hoàn thiện.**

Lấy từ `starter_v0/artifacts/version_log.csv` và `starter_v0/runs/*.json`. Chỉ dùng run có `provider_error_cases == 0` và `measured_cases == total_cases`.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline |  |  |  |  |
| v1 |  |  |  |  |  |
| v2 |  |  |  |  |  |
| v3 |  |  |  |  |  |

### B2. Failure Analysis

**Chờ thành viên phụ trách CP1 bổ sung phân tích lỗi baseline.** Các lỗi CP3/CP4 được ghi ở mục 5.

Lấy từ `results[*].result.failures` trong run JSON.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
|  |  |  |  |  |

### B3. Team Eval Cases

Bộ case: [eval_group.json](../../starter_v0/data/eval_group.json), đúng 5 single turn và 5 multi turn. Run hiện tại: [v5_B_group_openrouter_20261111T011314148993.json](../../starter_v0/runs/v5_B_group_openrouter_20261111T011314148993.json). Dùng OpenRouter / `openai/gpt-4o-mini` trên máy cá nhân, nhãn v5; prompt_hash không đổi.

Lệnh từ `starter_v0/`:

```text
python run_eval.py --provider openrouter --model openai/gpt-4o-mini --version v5 --suite group --eval-cases data/eval_group.json
```

Kết quả kiểm tra sau khi pull 8 commit: **9/10 PASS**, provider_error_cases=0, measured_cases=total_cases=10. case_accuracy, tool_routing_accuracy và argument_accuracy = 0.9; multiturn_accuracy = 1.0. Đây là số đo hiện tại; kết quả 10/10 trước khi đồng bộ không được dùng thay cho lần tích hợp này.

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

G05 sau tích hợp vẫn gọi `fetch` hai lần thay vì `football_headlines`, nên bị chấm sai routing dù đã làm rõ description của riêng tool mới. Chưa sửa prompt hoặc khai báo tool của các bạn khác để ép đổi hành vi. Cần tiếp tục cải thiện routing nhiều nguồn; không sửa expected để biến lỗi này thành PASS.

Tool code được kiểm tra bằng unit test; [run trước khi pull](../../starter_v0/runs/v5_B_group_openrouter_20261111T004856648556.json) từng cho thấy headlines đọc được hai nguồn (4.000 ký tự mỗi nguồn) và mentions đọc 10 bài, không có bài khớp Chelsea trong mẫu. Kết quả này là bằng chứng lịch sử, không thay thế eval sau tích hợp. Nội dung rỗng ở URL mẫu G06 và trường hợp không có tweet khớp vẫn cần phân biệt với lỗi routing. Eval riêng của tool do thành viên khác phụ trách không được tổng hợp từ cấu hình API máy này.

### B4. Live Chat Evidence

**Chờ CP5 bổ sung.** Eval nhóm ở B3 không thay thế transcript live. Cần transcript thật từ `chat.py`, gồm yêu cầu thường, thiếu thông tin rồi bổ sung và yêu cầu gửi/đăng; sau đó điền bảng dưới.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| Chờ bổ sung | | | | |

### B5a. Required Evidence — Tool mới, unit test, UI

| Item | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Tool mới `football_stats` | [tool.py](../../starter_v0/tools/football_stats/tool.py), [TOOL.md](../../starter_v0/tools/football_stats/TOOL.md) | Tính thống kê và so sánh; G01/G10 có output thật | Validation trả error dict; không tự tạo dữ liệu thiếu |
| Tool mới `football_headlines` | [tool.py](../../starter_v0/tools/football_headlines/tool.py), [TOOL.md](../../starter_v0/tools/football_headlines/TOOL.md) | 13 lượt unit test; đọc 2 nguồn ở run trước pull; G05 sau pull còn sai routing | Loại trùng, giới hạn request, lỗi riêng và bài rỗng |
| Tool mới `football_mentions` | [tool.py](../../starter_v0/tools/football_mentions/tool.py), [TOOL.md](../../starter_v0/tools/football_mentions/TOOL.md) | G08 đọc 2 tài khoản thật; 15 lượt unit test | Lọc trong mẫu timeline, loại ID trùng, lỗi từng tài khoản |
| Unit test tool mới (≥ 3 test/tool) | [test_tools_todo.py](../../starter_v0/tests/test_tools_todo.py), output bên dưới | football_stats: 22; headlines: 13; mentions: 15 lượt test sau tham số hóa | Offline, mock HTTP; toàn suite không skip |
| UI (CP5) | Chờ bổ sung theo A1 và B4 | Chưa có bằng chứng | Cần chạy thử và transcript thật |

Lệnh kiểm chứng từ `starter_v0/`: `python -m pytest -q`. Output thực tế:

```text
172 passed, 1 warning in 0.70s
```

Tổng 172 là toàn bộ suite sau tích hợp, gồm cả test của các thành viên khác; không phải toàn bộ do Trần Xuân Lộc viết. Phần của Lộc trong test_tools_todo.py vẫn có 64 lượt test: 50 cho ba tool và 14 stub đã hoàn thiện.

0 failed, 0 skipped. Warning đến từ plugin anyio dùng tên CallSpec2 đã deprecated, không phải lỗi test. File test_tools_todo.py có 64 lượt test sau tham số hóa: 14 cho tool có sẵn, 22 cho football_stats, 13 cho headlines và 15 cho mentions. Test API assert request và output; có nhánh input sai, thiếu key, HTTP/timeout, nguồn rỗng và lỗi một phần.

Ví dụ lỗi eval không bắt được: run group ban đầu G01 gọi đúng tool/team_a nhưng bỏ `team` trong từng trận; tool cũ trả success với 0 trận. Test `test_football_stats_malformed_record_returns_error_without_raising` giữ input lỗi đó và yêu cầu error dict, không raise. Test còn kiểm tra tỷ số thiếu/sai và window sai; happy path kiểm tra thống kê, fixture sân nhà/khách và cửa sổ gần nhất.

### B5. Bonus Evidence

| Bonus | Trạng thái và bằng chứng |
|---|---|
| Test challenge | Toàn suite 172 passed, 0 failed, 0 skipped; xem output B5a và [unit test](../../starter_v0/tests/test_tools_todo.py). Đáp ứng điều kiện kỹ thuật bonus 1 điểm theo [RUBRIC](../../RUBRIC.md). |
| Ít nhất 4 tool mới | Phần của Lộc có 3 tool. Việc tổng hợp số tool và bằng chứng của thành viên khác do nhóm bổ sung; chưa kết luận bonus này trong phạm vi báo cáo này. |
| Gửi Telegram thật sau xác nhận | Chưa có transcript chứng minh; test send hiện dùng mock. |

Đã triển khai 14 test stub cho tool có sẵn, gồm kiểm tra request/response và tách chỉ dẫn nhúng khỏi facts trong policy. Bonus test dựa vào toàn suite 0 skipped; không nhận là đã tìm/sửa bug tool có sẵn.

### B7. Small Local Model Challenge (bonus)

Chưa thực hiện, không có run model local hoặc bảng so sánh để nhận bonus này.

## 5. Khó khăn và cách xử lý

- G03 cũ tham chiếu dữ liệu ở lượt trước nhưng lại là single turn: bổ sung hai item cụ thể để kiểm tra format thread mà không yêu cầu model đoán dữ liệu.
- [Run trung gian](../../starter_v0/runs/v5_B_group_openrouter_20261110T232439410147.json) đạt 9/10 vì expected G01 buộc truyền last_n=5 dù hàm đã có default 5. Output thực tế đúng W-W/6 điểm. Bỏ điều kiện dư thừa này; giữ kiểm tra window không mặc định ở G10 (last_n=4). Không sửa prompt hoặc evaluator.
- [Run lỗi kết nối](../../starter_v0/runs/v5_B_group_openrouter_20261110T232339619559.json) có 10 provider_error, measured_cases=0; giữ để giải thích sự cố, không dùng tính accuracy. Chạy lại sau khi được phép kết nối mạng.
- Key Firecrawl/RapidAPI hiện có dùng được cho hai tool mới. Riêng URL mẫu G06 vẫn có nội dung rỗng, xem B3.

- [Run đầu của hai tool mới](../../starter_v0/runs/v5_B_group_openrouter_20261111T004755847035.json) đạt 9/10: G05 gọi fetch hai lần thay vì football_headlines. Chỉ làm rõ description của tool headlines mới để ưu tiên đọc theo nhóm; không sửa prompt hoặc mô tả tool cũ. Run trước pull từng đạt 10/10; sau khi tích hợp 8 commit, G05 lại chọn fetch hai lần. [Run sau pull lần đầu](../../starter_v0/runs/v5_B_group_openrouter_20261111T011204644324.json) và run hiện tại đều 9/10, không có provider error.

## 6. Tổng hợp đóng góp

Trần Xuân Lộc phụ trách ba tool CP3, unit test, eval CP4 và Test challenge; xem [TEAM.md](../../TEAM.md) và [báo cáo cá nhân](2A202603951_TranXuanLoc.md). Phân công và báo cáo của thành viên khác cần được người phụ trách xác nhận; không suy từ kết quả CP3/CP4 thành đóng góp CP1/CP2 hoặc CP5.

## 7. Hạn chế và hướng cải thiện — B6. Reflection

Giữ nguyên system_prompt.md và khai báo tool cũ. Bổ sung hai khai báo tool mới vào tools.yaml, điều chỉnh description headlines dựa trên lỗi G05. Các sửa khác thuộc code/test và eval nhóm. Cần review thủ công output tool, nội dung từ chối và khả năng lấy dữ liệu thật; routing PASS chưa đủ chứng minh kết quả có ích. Vòng tiếp theo nên đo chất lượng dữ liệu nguồn và câu trả lời cuối end-to-end, bổ sung kiểm tra số trận/điểm thực tế ngoài routing. Không so trực tiếp accuracy giữa hai bộ case đã sửa như bằng chứng tối ưu prompt. Ưu tiên tiếp theo là xử lý G05 trong phạm vi tool mới; số đo hiện tại chưa đạt 10/10.

## 8. Tài liệu tham khảo

- [Yêu cầu bài lab](../../README.md), [checkpoints](../../CHECKPOINTS.md), [rubric](../../RUBRIC.md).
- [Contract tool](../../starter_v0/tools/README.md), [hướng dẫn API dùng chung](../../docs/TOOL-SETUP.md).
- [Ví dụ unit test](../../starter_v0/tests/test_tools_examples.py) và ba file TOOL.md ở mục 3.1.
