---
name: standings
track: core
kind: live_api
provider: API-Football (primary), SportScore (fallback)
requires_env: [API_FOOTBALL_KEY]
inputs: [competition, season, country]
outputs: [status, competition, season, provider, attribution, count, groups, warning, attempts]
side_effect: false
requires_confirmation: false
---

# standings

Bảng xếp hạng đội của một giải bóng đá: hạng, đội, số trận, thắng/hoà/thua, bàn thắng/bại,
hiệu số, điểm, chuỗi phong độ 5 trận, mô tả suất (Champions League, Relegation…).

## When to use

- "Bảng xếp hạng Premier League", "đội nào đang đứng đầu La Liga", "top 4 Serie A mùa 2023/24",
  "Arsenal đang đứng thứ mấy", "nhóm xuống hạng Bundesliga".

## When NOT to use

- Vua phá lưới, cầu thủ ghi bàn -> `top_scorers`.
- Danh sách trận và tỷ số của một đội -> `team_fixtures`; tính phong độ từ danh sách trận -> `football_stats`.
- Tin tức -> `lookup`. Thiếu tên giải -> `clarify` trước, không đoán giải.

## Inputs

| Arg | Kiểu | Ghi chú |
|---|---|---|
| `competition` | string, bắt buộc | Tên giải ("Premier League") hoặc league id API-Football ("39"). |
| `season` | integer, tuỳ chọn | **Năm bắt đầu** mùa: 2024/25 -> `2024`. Bỏ trống = mùa hiện tại. Cũng nhận chuỗi `"2024/25"`. |
| `country` | string, tuỳ chọn | Để phân biệt giải trùng tên ("Premier League" + "England"). Chuỗi rỗng = không truyền. |

Input sai (giải rỗng, season không phải năm 4 chữ số, `country` không phải string) -> `error: invalid_input`
**trước khi** gọi HTTP.

## Providers

Phần dò giải, gọi HTTP, cache 24h, phân loại lỗi và che API key dùng chung với `top_scorers`
(import từ `tools/top_scorers/tool.py`), nên cache `/leagues` cũng dùng chung giữa các tool.

### 1. API-Football (primary)

- `GET /leagues?name=...&country=...` (hoặc `?id=` / `?search=`): league id, mùa `current`, `coverage.standings`.
- `GET /standings?league={id}&season={year}`, header `x-apisports-key`.
- Mỗi câu hỏi tốn 2 request (leagues + standings), cả hai được cache 24h.
- Giải có nhiều bảng (vòng bảng cúp) -> nhiều phần tử trong `groups`.

### 2. SportScore (fallback, không cần key)

- `GET https://sportscore.com/api/widget/standings/?sport=football&slug={slug}`
- Slug lấy theo đúng cách của `top_scorers`: danh sách slug đã kiểm chứng, hoặc search API với tên khớp chính xác.
- **Không có season filter, không có season metadata, không có `form`.** Vì vậy:
  - chỉ dùng khi user không nêu mùa, hoặc mùa được nêu chính là mùa `current` mà API-Football đã báo;
  - mọi trường hợp khác -> `season_unverifiable`, không thay bằng bảng mùa hiện tại;
  - `season.verified` luôn `false`, `season.actual` luôn `null`, `form` và `team_id` luôn `null`.
- Bắt buộc hiển thị attribution "Powered by SportScore" (xem `top_scorers/TOOL.md`).

## Limitations (kiểm chứng bằng gọi thật ngày 2026-11-11)

- **API-Football Free chỉ mở mùa 2022–2024.** `league=39&season=2025` trả
  `"Free plans do not have access to this season, try from 2022 to 2024."` -> `plan_restriction` -> SportScore.
  API-Football hiện báo mùa `current` của Premier League là 2026.
- `form` của API-Football xếp **trận gần nhất đứng đầu**: Arsenal 2024 có `"WWDLD"`, trong khi 5 trận cuối
  theo thời gian là D, L, D, W, W.
- SportScore `english-premier-league` và `spanish-la-liga` trả bảng 20 đội của mùa đang đá.
- Số liệu được chuyển nguyên từ provider; tool không tự phát hiện lỗi dữ liệu phía nguồn.

## Fallback

API-Football thất bại (`missing_api_key`, `auth_error`, `rate_limited` (429, không retry), `plan_restriction`,
`competition_not_found`, `unsupported_season`, `no_standings_coverage`, `timeout`, `connection_error`,
`server_error`, `invalid_json`, `invalid_response`) -> thử SportScore. Mọi lần thử nằm trong `attempts`;
`provider.fallback_reason` cho biết vì sao phải fallback. `ambiguous_competition` thì **không** fallback mà
trả `candidates` để agent hỏi lại user.

## Output

```json
{"tool": "standings", "status": "success",
 "competition": {"id": 39, "name": "Premier League", "country": "England", "slug": null},
 "season": {"requested": 2024, "actual": 2024, "verified": true},
 "provider": {"name": "API-Football", "fallback_used": false, "source_url": "https://www.api-football.com/"},
 "attribution": null, "count": 20, "warning": null,
 "groups": [{"group": "Premier League", "rows": [
   {"rank": 1, "team_id": 0, "team": "...", "played": 0, "win": 0, "draw": 0, "lose": 0,
    "goals_for": 0, "goals_against": 0, "goal_diff": 0, "points": 0, "form": "WWDLD", "description": "..."}]}],
 "attempts": [{"provider": "API-Football", "status": "success"}]}
```

(Giá trị trên chỉ minh hoạ schema.) Bảng rỗng vẫn là `success` với `count: 0` và `warning`.

Lỗi: `{"tool": "standings", "status": "error", "error": "<code>", "message": "...", "attempts": [...]}`
với `<code>` ∈ `invalid_input`, `ambiguous_competition` (kèm `candidates`), `data_unavailable`.
