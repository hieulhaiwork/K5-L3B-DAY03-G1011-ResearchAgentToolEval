---
name: football_stats
track: core
kind: local_formatter
provider: local
requires_env: []
inputs: [team_a, matches, team_b, last_n]
outputs: [status, team_a, team_b, comparison]
side_effect: false
requires_confirmation: false
---

# football_stats

Calculate and compare recent football (soccer) form, points, and goal statistics for teams over their recent matches.

## When to use

- User wants to analyze recent form (e.g. last 3 or 5 matches) of a football team.
- User wants to compare head-to-head or recent form between two teams (`team_a` and `team_b`) before an upcoming match.
- User wants metrics like Win-Draw-Loss form string (W-D-L), points earned, goal difference, clean sheets, and win rates.

## When NOT to use

- User wants general web search for football news -> use `lookup`.
- User wants to fetch a match report web page -> use `fetch`.
- User asks about non-football subjects.

## Input and limitations

- Supply `matches` in oldest-to-newest order; the last `last_n` records for each team are analyzed. No dates are inferred or sorted.
- Each record must contain either `team`, `scored`, `conceded`, or `home_team`, `away_team`, `home_score`, `away_score`.
- Scores must be non-negative integers (integer strings are accepted). Missing fields, fractional scores and booleans return an error dict rather than an invented score.
- `last_n` must be a positive integer; `team_b`, when provided, must be a non-empty team name.
- An empty list returns zero analyzed matches and `form: N/A`; fewer available matches are not extrapolated to the requested window.
- This local tool does not fetch live data or validate source accuracy. Comparisons use total points then goal difference; different sample sizes can bias the comparison.
