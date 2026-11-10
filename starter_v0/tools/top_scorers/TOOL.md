---
name: top_scorers
track: core
kind: live_api
provider: API-Football (primary), SportScore (fallback)
requires_env: [API_FOOTBALL_KEY]
inputs: [competition, season, limit, country]
outputs: [status, competition, season, provider, attribution, count, scorers, warning, attempts]
side_effect: false
requires_confirmation: false
---

# top_scorers

Bảng xếp hạng vua phá lưới (top scorers) của một giải bóng đá: thứ hạng, cầu thủ,
CLB, bàn thắng, kiến tạo, bàn phạt đền, số trận, số phút.

## When to use

- "Top 10 cầu thủ ghi bàn nhiều nhất Premier League 2025/26", "vua phá lưới La Liga",
  "Golden Boot", "ai đang dẫn đầu danh sách ghi bàn Champions League".
- So sánh các chân sút hàng đầu của một giải.

## When NOT to use

- Phong độ W-D-L của một đội từ danh sách trận -> `football_stats`.
- Tin tức, chuyển nhượng, tiểu sử cầu thủ -> `lookup` / `fetch`.
- Thiếu tên giải -> `clarify` trước, không đoán giải.

## Inputs

| Arg | Kiểu | Ghi chú |
|---|---|---|
| `competition` | string, bắt buộc | Tên giải ("Premier League") hoặc league id API-Football ("39"). |
| `season` | integer, tuỳ chọn | **Năm bắt đầu** mùa: 2025/26 -> `2025`. Bỏ trống = mùa hiện tại. Cũng nhận chuỗi `"2025/26"`. |
| `limit` | integer 1–20, mặc định 10 | Cắt cục bộ (API-Football không có tham số `limit`, trả tối đa 20). |
| `country` | string, tuỳ chọn | Để phân biệt giải trùng tên ("Premier League" + "England"). Chuỗi rỗng = không truyền. |

Input sai (giải rỗng, `limit` ngoài 1–20, season không phải năm 4 chữ số, `country` không phải string)
-> trả `error: invalid_input` **trước khi** gọi HTTP.

## Providers

### 1. API-Football (primary)

- `GET https://v3.football.api-sports.io/leagues?name=...&country=...` (hoặc `?id=` / `?search=`) để lấy
  league id, danh sách mùa, mùa `current` và `coverage.top_scorers`.
- `GET /players/topscorers?league={id}&season={year}`, header `x-apisports-key: $API_FOOTBALL_KEY`.
- Free plan: 100 request/ngày, giới hạn mùa lịch sử (lỗi `plan` trả về trong body HTTP 200).
- Mỗi câu hỏi tốn 2 request (leagues + topscorers); cả hai được cache 24h trong bộ nhớ tiến trình.

### 2. SportScore (fallback, không cần key)

- `GET https://sportscore.com/api/widget/topscorers/?sport=football&slug={slug}&limit=20&stat=goals`
- Slug đã kiểm chứng ngày 2026-11-10 nằm trong `SPORTSCORE_COMPETITIONS` (EPL, Serie A, Bundesliga,
  Champions League, Europa League, Conference League, Nations League, Euro, World Cup, Asian Cup, Gold Cup).
  Giải khác được tìm qua `GET /api/v1/search/`, chỉ nhận tên khớp chính xác (và đúng quốc gia trong URL
  nếu có `country`); nhiều kết quả khớp -> `ambiguous_competition`. Không bao giờ đoán slug.
- **Không có season filter và không có season metadata** trong response. Vì vậy:
  - chỉ dùng khi user không nêu mùa, hoặc mùa được nêu chính là mùa `current` mà API-Football đã báo;
  - mọi trường hợp khác -> `season_unverifiable`, không thay bằng dữ liệu mùa hiện tại.
  - `season.verified` luôn `false`, `season.actual` luôn `null`.
- Không có: bàn phạt đền, quốc tịch, tuổi, vị trí, id -> trả `null` (không phải 0).
- ~10.000 request/24h/IP.

### Attribution (bắt buộc khi dùng SportScore)

Output có `attribution` = `{"text": "Powered by SportScore", "url": "https://sportscore.com/", "html": ...}`.
UI hiển thị dữ liệu này **phải** hiện link dofollow `Powered by SportScore`
(điều khoản: https://sportscore.com/developers/terms/).

## Limitations (kiểm chứng bằng gọi thật ngày 2026-11-10)

- **API-Football Free chỉ mở mùa 2022–2024.** Mùa hiện tại (2025) trả lỗi
  `"Free plans do not have access to this season, try from 2022 to 2024."` -> `plan_restriction` -> SportScore.
  Vì vậy: mùa hiện tại chỉ có từ SportScore (không verify mùa, thiếu phạt đền/quốc tịch/tuổi);
  mùa 2022–2024 lấy từ API-Football (`verified: true`); mùa ≤ 2021 -> `data_unavailable`.
- **Không có `API_FOOTBALL_KEY`**: chỉ trả lời được mùa hiện tại, và chỉ với giải có slug SportScore.
- **Số liệu được chuyển nguyên từ provider, tool không tự phát hiện lỗi dữ liệu phía nguồn.**
  Ví dụ đã thấy: `league=39&season=2024` của API-Football trả hạng 1 là
  "Matheus Cunha – Manchester United – 30 bàn – 66 trận" trong một khối `statistics` duy nhất
  (một mùa Premier League chỉ có 38 trận; mùa đó Cunha thi đấu cho Wolves). Có vẻ provider cộng trùng
  và gán sang CLB mới. Unit test và eval đều không bắt được lỗi loại này; khi trình bày kết quả nên
  ghi rõ nguồn và đối chiếu nếu số liệu bất thường.
- Slug SportScore đã gọi topscorers thành công: `english-premier-league`, `uefa-champions-league`.
  Slug khác trong `SPORTSCORE_COMPETITIONS` lấy từ search API / trang docs nhưng chưa gọi topscorers.
  La Liga chưa xác minh slug (tool tự tìm qua search lúc chạy).

## Fallback

API-Football thất bại vì `missing_api_key`, `auth_error` (401/403), `rate_limited` (429, không retry),
`plan_restriction`, `competition_not_found`, `unsupported_season`, `no_top_scorers_coverage`, `timeout`,
`connection_error`, `server_error` (5xx), `invalid_json`, `invalid_response` -> thử SportScore.
Mọi lần thử được ghi trong `attempts` (provider, reason, message, http_status);
`provider.fallback_used=true` và `provider.fallback_reason` cho biết vì sao phải fallback.
`ambiguous_competition` thì **không** fallback mà trả `candidates` để agent hỏi lại user.

## Output

Thành công:

```json
{"tool": "top_scorers", "status": "success",
 "competition": {"id": 39, "name": "Premier League", "country": "England", "slug": null},
 "season": {"requested": 2025, "actual": 2025, "verified": true},
 "provider": {"name": "API-Football", "fallback_used": false, "source_url": "https://www.api-football.com/"},
 "attribution": null, "count": 10, "warning": null,
 "scorers": [{"rank": 1, "player_id": 0, "player": "...", "nationality": "...", "age": 0, "position": "...",
              "photo": "...", "team_id": 0, "team": "...", "goals": 0, "assists": 0, "penalties": 0,
              "appearances": 0, "minutes": 0}],
 "attempts": [{"provider": "API-Football", "status": "success"}]}
```

(Giá trị trên chỉ minh hoạ schema.) Danh sách rỗng vẫn là `success` với `count: 0` và `warning`.

Lỗi: `{"tool": "top_scorers", "status": "error", "error": "<code>", "message": "...", "attempts": [...]}`
với `<code>` ∈ `invalid_input`, `ambiguous_competition` (kèm `candidates`), `data_unavailable`.
Tool không raise và không bao giờ đưa API key vào output.
