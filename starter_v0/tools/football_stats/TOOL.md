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
