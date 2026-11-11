"""team_fixtures: the last N finished matches of a football team in ONE season.

Provider: API-Football only (needs API_FOOTBALL_KEY).
- /teams?search=  -> resolve the team id (exact name match only, never guess).
- /fixtures?team=&season=[&league=] -> whole season, filtered and sliced locally,
  because the Free plan rejects the `last` / `next` parameters.
Free plan = seasons 2022-2024 only; the current season fails with a `plan` error.
There is no fallback: SportScore's /api/widget/team/ returned placeholder data
(the same "Arsenal vs Chelsea" fixture for every team) when checked on 2026-11-11.

Output `matches` uses the fixture format of football_stats (home_team, away_team,
home_score, away_score), oldest first, so it can be passed straight to that tool.
Never raises, never puts the API key in the output.
"""
from __future__ import annotations

import re
from typing import Any

from tools._shared import fold_text
from tools.top_scorers.tool import (
    API_FOOTBALL_SITE,
    AmbiguousCompetition,
    ProviderError,
    _api_football_call,
    _api_football_key,
    _cache_get,
    _cache_set,
    _canonical_country,
    _int_or_none,
    _parse_season,
    _resolve_api_football_league,
    _safe,
    _str_or_none,
)

TOOL_NAME = "team_fixtures"
MAX_LAST_N = 50
MAX_CANDIDATES = 10

# Finished statuses. `goals` is the score after 90' or extra time; shoot-outs are separate.
FINISHED_STATUSES = {"FT": "regular_time", "AET": "extra_time", "PEN": "penalties"}


class AmbiguousTeam(Exception):
    def __init__(self, candidates: list[dict[str, Any]], exact: bool) -> None:
        super().__init__("ambiguous team")
        self.candidates = candidates
        self.exact = exact


def _country_key(name: Any) -> str:
    return fold_text(str(name or "")).replace("-", " ").strip()


def _search_term(team: str) -> str:
    """API-Football search accepts only letters, digits and spaces (min 3 chars)."""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", fold_text(team))).strip()


def _team_summary(item: dict[str, Any]) -> dict[str, Any]:
    team = item.get("team") or {}
    return {"id": _int_or_none(team.get("id")), "name": _str_or_none(team.get("name")),
            "country": _str_or_none(team.get("country")), "national": team.get("national")}


def _resolve_team(team: str, country: str | None, key: str) -> dict[str, Any]:
    if team.isdigit():
        return {"id": int(team), "name": None, "country": None, "national": None}

    term = _search_term(team)
    if len(term) < 3:
        raise ProviderError("invalid_team_name", "Team name needs at least 3 letters or digits for API-Football search")
    cache_key = ("api_football", "teams_search", term)
    items = _cache_get(cache_key)
    if items is None:
        items = _api_football_call("/teams", {"search": term}, key)
        _cache_set(cache_key, items)

    teams = [_team_summary(item) for item in items if isinstance(item, dict)]
    teams = [t for t in teams if t["id"] is not None]
    if country:
        teams = [t for t in teams if _country_key(t["country"]) == country]
    target = fold_text(team).strip()
    exact = [t for t in teams if fold_text(t["name"] or "").strip() == target]
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        raise AmbiguousTeam(exact[:MAX_CANDIDATES], exact=True)
    if teams:  # only partial matches: list them, do not pick one
        raise AmbiguousTeam(teams[:MAX_CANDIDATES], exact=False)
    where = f" in {country.title()}" if country else ""
    raise ProviderError("team_not_found", f"No API-Football team named {team!r}{where}")


def _resolve_league(competition: str, season: int, team_country: str | None, key: str) -> dict[str, Any]:
    """Prefer the team's country (domestic league), then try without it (cups / continental)."""
    attempts = [team_country.title(), None] if team_country else [None]
    last_error: ProviderError | None = None
    for country in attempts:
        try:
            item = _resolve_api_football_league(competition, season, country, key, {})[0]
        except ProviderError as exc:
            if exc.reason != "competition_not_found":
                raise
            last_error = exc
            continue
        league = item.get("league") or {}
        return {"id": league.get("id"), "name": league.get("name"),
                "country": (item.get("country") or {}).get("name")}
    assert last_error is not None
    raise last_error


def _normalize_fixture(item: dict[str, Any], team_id: int) -> dict[str, Any] | None:
    fixture = item.get("fixture") or {}
    status = (fixture.get("status") or {}).get("short")
    if status not in FINISHED_STATUSES:
        return None
    teams = item.get("teams") or {}
    home, away = teams.get("home") or {}, teams.get("away") or {}
    goals = item.get("goals") or {}
    home_score, away_score = _int_or_none(goals.get("home")), _int_or_none(goals.get("away"))
    home_name, away_name = _str_or_none(home.get("name")), _str_or_none(away.get("name"))
    if None in (home_score, away_score, home_name, away_name):
        return None  # never hand football_stats an invented score
    league = item.get("league") or {}
    penalty = ((item.get("score") or {}).get("penalty")) or {}
    shootout = None
    if status == "PEN":
        shootout = {"home": _int_or_none(penalty.get("home")), "away": _int_or_none(penalty.get("away"))}
    return {
        "fixture_id": _int_or_none(fixture.get("id")),
        "date": _str_or_none(fixture.get("date")),
        "competition": _str_or_none(league.get("name")),
        "round": _str_or_none(league.get("round")),
        "home_team": home_name,
        "away_team": away_name,
        "home_score": home_score,
        "away_score": away_score,
        "venue": "home" if _int_or_none(home.get("id")) == team_id else "away",
        "decided_by": FINISHED_STATUSES[status],
        "penalty_shootout": shootout,
        "_timestamp": _int_or_none(fixture.get("timestamp")) or 0,
    }


def _error(code: str, message: str, **extra: Any) -> dict[str, Any]:
    return {"tool": TOOL_NAME, "status": "error", "error": code, "message": message, **extra}


def team_fixtures(
    team: str = "",
    season: int | str | None = None,
    competition: str | None = None,
    country: str | None = None,
    last_n: int = 5,
) -> dict[str, Any]:
    """Last N finished matches of a team in one season (API-Football), oldest first."""
    try:
        if isinstance(team, int) and not isinstance(team, bool):
            team = str(team)
        if not isinstance(team, str) or not team.strip():
            raise ValueError("team must be a non-empty string (team name or numeric API-Football team id)")
        team = team.strip()
        season_year = _parse_season(season)
        if season_year is None:
            raise ValueError("season is required: the starting year of the season, e.g. 2024 for 2024/25")
        if competition is not None and not isinstance(competition, str):
            raise ValueError("competition must be a string such as 'Premier League'")
        competition_name = competition.strip() if competition and competition.strip() else None
        if country is not None and not isinstance(country, str):
            raise ValueError("country must be a string such as 'England'")
        country_name = country.strip() if country and country.strip() else None
        n = None if isinstance(last_n, bool) else _int_or_none(last_n)
        if n is None or not 1 <= n <= MAX_LAST_N:
            raise ValueError(f"last_n must be an integer between 1 and {MAX_LAST_N}")
    except ValueError as exc:
        return _error("invalid_input", str(exc))

    canonical = _canonical_country(country_name)
    attempts: list[dict[str, Any]] = []
    try:
        key = _api_football_key()
        team_info = _resolve_team(team, canonical, key)
        league = None
        if competition_name:
            league = _resolve_league(competition_name, season_year, _country_key(team_info["country"]) or canonical, key)

        params: dict[str, Any] = {"team": team_info["id"], "season": season_year}
        if league:
            params["league"] = league["id"]
        cache_key = ("api_football", "fixtures", team_info["id"], season_year, params.get("league"))
        items = _cache_get(cache_key)
        if items is None:
            items = _api_football_call("/fixtures", params, key)
            _cache_set(cache_key, items)
    except AmbiguousTeam as exc:
        kind = "several teams named" if exc.exact else "no exact match, only similar teams, for"
        return _error("ambiguous_team",
                      f"API-Football found {kind} {team!r}; ask the user which one (or pass country / team id).",
                      candidates=exc.candidates, attempts=attempts)
    except AmbiguousCompetition as exc:
        return _error("ambiguous_competition",
                      f"{exc.provider} found several competitions named {competition_name!r}; ask the user which one.",
                      candidates=exc.candidates, attempts=attempts)
    except ProviderError as exc:
        attempts.append({"provider": "API-Football", "status": "failed", "reason": exc.reason,
                         "message": _safe(str(exc)), "http_status": exc.http_status})
        return _error("data_unavailable", f"API-Football could not supply fixtures: {exc.reason} ({_safe(str(exc))})",
                      attempts=attempts)
    except Exception as exc:  # unexpected payload shape etc.: report, never crash the agent
        attempts.append({"provider": "API-Football", "status": "failed", "reason": "unexpected_error",
                         "message": _safe(f"{type(exc).__name__}: {exc}"), "http_status": None})
        return _error("data_unavailable", "API-Football could not supply fixtures: unexpected_error",
                      attempts=attempts)

    attempts.append({"provider": "API-Football", "status": "success"})
    team_id = team_info["id"]
    if team_info["name"] is None:  # numeric id given: take the name from the fixtures
        for item in items:
            for side in ("home", "away"):
                side_team = ((item.get("teams") or {}).get(side)) or {}
                if _int_or_none(side_team.get("id")) == team_id and _str_or_none(side_team.get("name")):
                    team_info["name"] = side_team["name"]
                    break
            if team_info["name"]:
                break

    finished = [m for m in (_normalize_fixture(item, team_id) for item in items if isinstance(item, dict)) if m]
    finished.sort(key=lambda m: m["_timestamp"])
    selected = finished[-n:]
    for match in selected:
        match.pop("_timestamp")

    warning = None
    if not selected:
        warning = "No finished matches with a score were found for this team and season."
    elif len(selected) < n:
        warning = f"Only {len(selected)} finished matches were available (asked for {n})."
    if not league:
        note = "All competitions are included (friendlies too); pass `competition` to keep one league or cup."
        warning = f"{warning} {note}" if warning else note

    return {
        "tool": TOOL_NAME,
        "status": "success",
        "team": {"id": team_id, "name": team_info["name"], "country": team_info["country"]},
        "competition": league,
        "season": {"requested": season_year, "actual": season_year, "verified": True},
        "provider": {"name": "API-Football", "fallback_used": False, "source_url": API_FOOTBALL_SITE},
        "order": "oldest_first",
        "count": len(selected),
        "fixtures_in_season": len(items),
        "finished_in_season": len(finished),
        "matches": selected,
        "warning": warning,
        "attempts": attempts,
    }
