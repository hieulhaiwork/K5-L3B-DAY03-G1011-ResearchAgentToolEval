---
name: team_fixtures
track: core
kind: live_api
provider: API-Football
requires_env: [API_FOOTBALL_KEY]
inputs: [team, season, competition, country, last_n]
outputs: [status, team, competition, season, provider, order, count, fixtures_in_season, finished_in_season, matches, warning, attempts]
side_effect: false
requires_confirmation: false
---

# team_fixtures

N trận **đã đá** gần nhất (tỷ số thật) của một đội trong một mùa giải, sắp theo thời gian cũ -> mới.
`matches` dùng đúng format fixture của `football_stats` (`home_team`, `away_team`, `home_score`, `away_score`),
nên agent có thể nối: `team_fixtures` -> `football_stats(team_a=team.name, matches=matches)`.

## When to use

- "5 trận cuối mùa 2024/25 của Arsenal ở Premier League", "kết quả của Liverpool mùa 2023/24".
- User muốn phân tích phong độ W-D-L của một đội trong một mùa cụ thể nhưng không đưa danh sách trận:
  gọi tool này trước rồi chuyển `matches` sang `football_stats`.

## When NOT to use

- Bảng xếp hạng -> `standings`. Vua phá lưới -> `top_scorers`.
- Lịch thi đấu sắp tới, trận đang diễn ra: **không hỗ trợ** (chỉ lấy trận đã kết thúc).
- User không nêu mùa -> `clarify` hỏi mùa, không tự điền.

## Inputs

| Arg | Kiểu | Ghi chú |
|---|---|---|
| `team` | string, bắt buộc | Tên đội ("Arsenal") hoặc team id API-Football ("42"). |
| `season` | integer, **bắt buộc** | Năm bắt đầu mùa: 2024/25 -> `2024`. Cũng nhận chuỗi `"2024/25"`. |
| `competition` | string, tuỳ chọn | Chỉ lấy trận của một giải/cúp. Bỏ trống = mọi giải đấu, **kể cả giao hữu**. |
| `country` | string, tuỳ chọn | Quốc gia của **đội**, để phân biệt đội trùng tên ("Arsenal" + "England"). |
| `last_n` | integer 1–50, mặc định 5 | Số trận đã đá gần nhất cần lấy. |

Input sai (thiếu team/season, `last_n` ngoài 1–50, kiểu sai) -> `error: invalid_input` **trước khi** gọi HTTP.

## Provider: API-Football (không có fallback)

1. `GET /teams?search={tên đã bỏ dấu, chỉ chữ/số/khoảng trắng}`, cache 24h. Chỉ nhận đội có tên **khớp chính xác**
   (sau khi lọc theo `country` nếu có). Nhiều đội khớp chính xác -> `ambiguous_team` kèm `candidates`;
   chỉ có đội tên gần giống -> cũng `ambiguous_team` (không tự chọn). Team id dạng số thì bỏ qua bước này.
2. Nếu có `competition`: dò giải qua `/leagues` (dùng chung với `top_scorers`), thử trước với quốc gia của đội
   (giải quốc nội), không thấy thì thử không kèm quốc gia (cúp châu lục).
3. `GET /fixtures?team={id}&season={year}[&league={id}]`, cache 24h. Lấy nguyên mùa rồi lọc và cắt ở phía tool.

Mỗi câu hỏi tốn 2 request (teams + fixtures), thêm 1 nếu có `competition` và `/leagues` chưa có trong cache.

Chỉ giữ trận có status `FT`, `AET`, `PEN` và có đủ tên hai đội và tỷ số. Trận hoãn/huỷ/bỏ dở bị bỏ qua,
không bao giờ điền tỷ số giả. `home_score`/`away_score` là tỷ số sau 90 phút hoặc sau hiệp phụ, **không**
gồm loạt luân lưu; loạt luân lưu nằm riêng trong `penalty_shootout`, và `decided_by` cho biết trận kết thúc thế nào.

## Limitations (kiểm chứng bằng gọi thật ngày 2026-11-11)

- **Free plan chặn tham số `last` và `next`** (`"Free plans do not have access to the Last parameter."`),
  nên tool phải lấy cả mùa rồi tự cắt.
- **Free plan chỉ mở mùa 2022–2024.** Mùa khác trả lỗi `plan` -> `error: data_unavailable`, reason
  `plan_restriction`. Vì vậy tool không trả lời được "phong độ gần đây" của mùa đang đá.
- **Không có fallback.** SportScore `/api/widget/team/` trả cùng một trận mẫu "Arsenal vs Chelsea"
  (`status: upcoming`, ngày 2026-04-10, URL `.../m1/`) cho cả `arsenal` lẫn `chelsea`, nên không dùng được.
  `/api/widget/matches/` không lọc theo đội.
- `/teams?search=Arsenal` trả 25 đội, trong đó 3 đội tên đúng "Arsenal" (Anh, Guadeloupe, Belarus):
  cần `country` hoặc team id.
- `/fixtures?team=42&season=2024` không kèm giải trả 63 trận: 38 Premier League, 14 Champions League,
  5 League Cup, 4 giao hữu CLB, 1 Emirates Cup, 1 FA Cup. Trong đó có trận giao hữu Arsenal 2-1 Manchester United
  vẫn đá luân lưu (`PEN`). Nên truyền `competition` khi phân tích phong độ.

## Output

```json
{"tool": "team_fixtures", "status": "success",
 "team": {"id": 42, "name": "Arsenal", "country": "England"},
 "competition": {"id": 39, "name": "Premier League", "country": "England"},
 "season": {"requested": 2024, "actual": 2024, "verified": true},
 "provider": {"name": "API-Football", "fallback_used": false, "source_url": "https://www.api-football.com/"},
 "order": "oldest_first", "count": 5, "fixtures_in_season": 38, "finished_in_season": 38,
 "matches": [{"fixture_id": 0, "date": "...", "competition": "Premier League", "round": "...",
              "home_team": "...", "away_team": "...", "home_score": 0, "away_score": 0,
              "venue": "home", "decided_by": "regular_time", "penalty_shootout": null}],
 "warning": null, "attempts": [{"provider": "API-Football", "status": "success"}]}
```

(Giá trị trên chỉ minh hoạ schema.) Không truyền `competition` thì `warning` nhắc rằng đã gồm mọi giải đấu.

Lỗi: `{"tool": "team_fixtures", "status": "error", "error": "<code>", "message": "...", "attempts": [...]}`
với `<code>` ∈ `invalid_input`, `ambiguous_team` / `ambiguous_competition` (kèm `candidates`), `data_unavailable`.
Tool không raise và không bao giờ đưa API key vào output.
