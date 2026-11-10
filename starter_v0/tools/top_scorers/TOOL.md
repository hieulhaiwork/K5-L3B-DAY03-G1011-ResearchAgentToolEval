---
name: top_scorers
track: bonus
kind: live_api
provider: API-Football with SportScore fallback
requires_env: [API_FOOTBALL_KEY]
inputs: [competition, season, limit, country]
outputs: [competition, season, provider, scorers]
side_effect: false
---
# top_scorers

Returns ranked football competition scorers with player, team, goals, assists,
penalties, appearances, and minutes when the source provides them. Missing
statistics remain `null`; the tool never invents values.

Use for football top-scorer, Golden Boot, goals, and scorer-assist leaderboard
requests. Do not use for an unspecified/ambiguous competition; ask the user to
choose one. `season` is the starting year (for example, 2025 means 2025/26).
Keep an explicitly requested season unchanged.

API-Football is the primary source (`/leagues`, then `/players/topscorers`) and
requires `API_FOOTBALL_KEY`. When it is unavailable, the tool may use the
documented SportScore leaderboard endpoint for a competition with a verified
local slug. SportScore has no documented season filter: historical results are
returned only if the response itself verifies the requested season. Current
leaderboard results without season metadata are labeled unverified.

The provider metadata reports the final source and any primary-provider
failure. SportScore results include a visible `Powered by SportScore` dofollow
attribution link (`provider.attribution.html`); interfaces displaying these
results must render that attribution. Errors are structured and include
provider failure codes without exposing credentials.