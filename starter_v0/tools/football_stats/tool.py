from __future__ import annotations

from typing import Any

from .research import canonical_team, find_recent_matches


def analyze_football_form(
    team_a: str,
    matches: list[dict[str, Any]] | None = None,
    team_b: str | None = None,
    last_n: int = 5,
) -> dict[str, Any]:
    """Find recent results when no matches are supplied, then calculate football form.

    Args:
        team_a: Name of the primary team to analyze.
        matches: Omit to discover current results via Tavily/Firecrawl. When explicitly
                 supplied, this is a list of match dicts. Each dict should have:
                 - 'team' or 'home_team'/'away_team'
                 - 'scored' and 'conceded' (or 'home_score' and 'away_score')
        team_b: Optional second team name to compare against.
        last_n: Number of most recent matches to consider (default 5, must be > 0).
                Matches must be ordered oldest to newest; this tool does not sort dates.

    Returns:
        Dict containing form string (e.g. W-W-D-L), points, stats, and optional comparison.
    """
    if not team_a or not isinstance(team_a, str) or not team_a.strip():
        return {"status": "error", "error": "team_a must be a non-empty string"}

    if matches is not None and not isinstance(matches, list):
        return {"status": "error", "error": "matches must be a list of match records"}

    if team_b is not None and (not isinstance(team_b, str) or not team_b.strip()):
        return {"status": "error", "error": "team_b must be a non-empty string when provided"}

    if isinstance(last_n, bool) or not isinstance(last_n, (int, str)):
        return {"status": "error", "error": "last_n must be a positive integer"}
    try:
        n = int(last_n)
        if n <= 0:
            return {"status": "error", "error": "last_n must be a positive integer greater than 0"}
    except (ValueError, TypeError):
        return {"status": "error", "error": "last_n must be an integer"}

    if matches is None:
        if n > 20:
            return {"status": "error", "error": "Automatic research supports last_n from 1 to 20"}
        teams = [canonical_team(team_a)]
        if team_b:
            teams.append(canonical_team(team_b))
        if len(teams) == 2 and teams[0].casefold() == teams[1].casefold():
            return {"status": "error", "error": "Choose two different teams to compare"}
        research = [find_recent_matches(team, n) for team in teams]
        if any(item["status"] == "error" for item in research):
            return {"status": "error", "error": "research_failed", "research": research,
                    "message": "Could not retrieve enough supported source data to analyze the requested team(s)"}
        result = analyze_football_form(teams[0], matches=[m for item in research for m in item["matches"]],
                                       team_b=teams[1] if len(teams) == 2 else None, last_n=n)
        result.update(data_mode="automatic_research", research=research,
                      matches_used=[m for item in research for m in item["matches"]])
        if "comparison" in result:
            result["comparison"]["goals_scored_difference"] = result["team_a"]["goals_scored"] - result["team_b"]["goals_scored"]
            result["comparison"]["points_a"] = result["team_a"]["points"]
            result["comparison"]["points_b"] = result["team_b"]["points"]
        if any(item["status"] == "partial" for item in research):
            result["status"] = "partial"
            result["warning"] = "Fewer than requested matches found; totals are based only on the listed matches"
            if "comparison" in result:
                result["comparison"] = {"better_form_team": None, "reason": "Insufficient equal-size samples for comparison"}
        return result

    clean_team_a = team_a.strip().lower()

    # Reject incomplete records rather than silently inventing 0-0 scores or
    # returning success with zero analyzed matches (as in group run G01).
    def _score(value: Any) -> int:
        if isinstance(value, bool) or not isinstance(value, (int, str)):
            raise ValueError("scores must be non-negative integers")
        score = int(value)
        if score < 0:
            raise ValueError("scores must be non-negative integers")
        return score

    for index, match in enumerate(matches):
        try:
            if not isinstance(match, dict):
                raise ValueError("each match must be an object")
            if "team" in match:
                names, scores = ("team",), ("scored", "conceded")
            else:
                names = ("home_team", "away_team")
                scores = ("home_score", "away_score")
            for key in names:
                if not isinstance(match.get(key), str) or not match[key].strip():
                    raise ValueError(f"{key} must be a non-empty string")
            for key in scores:
                if key not in match:
                    raise ValueError(f"missing {key}")
                _score(match[key])
        except (ValueError, TypeError) as exc:
            return {"status": "error", "error": f"matches[{index}]: {exc}"}

    def _extract_team_matches(team_name: str) -> list[tuple[int, int]]:
        """Extract (scored, conceded) pairs for a team from the matches list."""
        records: list[tuple[int, int]] = []
        t_lower = team_name.strip().lower()

        for m in matches:
            if not isinstance(m, dict):
                continue

            # Format 1: explicitly has 'team' with 'scored' and 'conceded'
            if "team" in m and str(m["team"]).strip().lower() == t_lower:
                try:
                    s = int(m.get("scored", 0))
                    c = int(m.get("conceded", 0))
                    records.append((s, c))
                except (ValueError, TypeError):
                    continue

            # Format 2: fixture style {'home_team': ..., 'away_team': ..., 'home_score': ..., 'away_score': ...}
            elif "home_team" in m and "away_team" in m:
                home = str(m["home_team"]).strip().lower()
                away = str(m["away_team"]).strip().lower()
                try:
                    h_score = int(m.get("home_score", 0))
                    a_score = int(m.get("away_score", 0))
                except (ValueError, TypeError):
                    continue

                if home == t_lower:
                    records.append((h_score, a_score))
                elif away == t_lower:
                    records.append((a_score, h_score))

        return records

    def _calc_stats(team_display: str, records: list[tuple[int, int]]) -> dict[str, Any]:
        recent = records[-n:]
        form_tokens: list[str] = []
        points = 0
        goals_scored = 0
        goals_conceded = 0
        clean_sheets = 0
        wins = 0
        draws = 0
        losses = 0

        for scored, conceded in recent:
            goals_scored += scored
            goals_conceded += conceded
            if conceded == 0:
                clean_sheets += 1

            if scored > conceded:
                form_tokens.append("W")
                points += 3
                wins += 1
            elif scored == conceded:
                form_tokens.append("D")
                points += 1
                draws += 1
            else:
                form_tokens.append("L")
                losses += 1

        total_analyzed = len(recent)
        max_points = total_analyzed * 3
        win_rate = round((wins / total_analyzed) * 100, 1) if total_analyzed > 0 else 0.0

        return {
            "team": team_display,
            "matches_analyzed": total_analyzed,
            "form": "-".join(form_tokens) if form_tokens else "N/A",
            "points": points,
            "max_possible_points": max_points,
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "goals_scored": goals_scored,
            "goals_conceded": goals_conceded,
            "goal_diff": goals_scored - goals_conceded,
            "clean_sheets": clean_sheets,
            "win_rate_percent": win_rate,
        }

    stat_a = _calc_stats(team_a.strip(), _extract_team_matches(clean_team_a))
    result: dict[str, Any] = {
        "status": "success",
        "team_a": stat_a,
    }

    if team_b and isinstance(team_b, str) and team_b.strip():
        stat_b = _calc_stats(team_b.strip(), _extract_team_matches(team_b.strip()))
        result["team_b"] = stat_b

        # Compare form
        pts_diff = stat_a["points"] - stat_b["points"]
        if pts_diff > 0:
            better = stat_a["team"]
        elif pts_diff < 0:
            better = stat_b["team"]
        else:
            # tie break by goal diff
            gd_diff = stat_a["goal_diff"] - stat_b["goal_diff"]
            if gd_diff > 0:
                better = stat_a["team"]
            elif gd_diff < 0:
                better = stat_b["team"]
            else:
                better = "Level (Tie)"

        result["comparison"] = {
            "better_form_team": better,
            "points_diff": abs(pts_diff),
            "goal_diff_gap": stat_a["goal_diff"] - stat_b["goal_diff"],
        }

    return result
