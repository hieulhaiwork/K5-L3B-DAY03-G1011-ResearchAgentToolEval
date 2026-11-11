"""standings: league table of a football competition.

Provider order:
1. API-Football /standings (primary, needs API_FOOTBALL_KEY; Free plan = seasons 2022-2024 only).
2. SportScore /api/widget/standings/ (free fallback, no key, NO season metadata and no form).

Same rules as top_scorers: never invent stats (missing -> None), never swap a
requested season for current data, never put the API key in the output, never raise.
League lookup, HTTP, cache and error handling are shared with tools.top_scorers.tool.
"""
from __future__ import annotations

from typing import Any

from tools.top_scorers.tool import (
    API_FOOTBALL_SITE,
    SPORTSCORE_ATTRIBUTION,
    SPORTSCORE_BASE,
    SPORTSCORE_SITE,
    AmbiguousCompetition,
    ProviderError,
    _api_football_call,
    _api_football_key,
    _cache_get,
    _cache_set,
    _canonical_country,
    _get_json,
    _int_or_none,
    _known_sportscore_slug,
    _parse_season,
    _resolve_api_football_league,
    _safe,
    _search_sportscore_slug,
    _str_or_none,
)

TOOL_NAME = "standings"


# ---------------------------------------------------------------- API-Football

def _fetch_api_football(competition: str, season: int | None, country: str | None,
                        context: dict[str, Any]) -> dict[str, Any]:
    key = _api_football_key()
    item, chosen, year = _resolve_api_football_league(competition, season, country, key, context)
    league = item.get("league") or {}
    if not (chosen.get("coverage") or {}).get("standings"):
        raise ProviderError("no_standings_coverage", f"API-Football has no standings coverage for season {year}")

    cache_key = ("api_football", "standings", league.get("id"), year)
    response = _cache_get(cache_key)
    if response is None:
        response = _api_football_call("/standings", {"league": league.get("id"), "season": year}, key)
        _cache_set(cache_key, response)

    groups: list[dict[str, Any]] = []
    if response and isinstance(response[0], dict):
        tables = (response[0].get("league") or {}).get("standings") or []
        for table in tables:
            if not isinstance(table, list):
                continue
            rows = [_normalize_api_football_row(row) for row in table if isinstance(row, dict)]
            name = next((_str_or_none(row.get("group")) for row in table if isinstance(row, dict)), None)
            groups.append({"group": name, "rows": rows})

    return {
        "competition": {
            "id": league.get("id"),
            "name": league.get("name"),
            "country": (item.get("country") or {}).get("name"),
            "slug": None,
        },
        "season": {"requested": season, "actual": year, "verified": True},
        "provider": {"name": "API-Football", "fallback_used": False, "source_url": API_FOOTBALL_SITE},
        "attribution": None,
        "groups": groups,
    }


def _normalize_api_football_row(row: dict[str, Any]) -> dict[str, Any]:
    team = row.get("team") or {}
    totals = row.get("all") or {}
    goals = totals.get("goals") or {}
    return {
        "rank": _int_or_none(row.get("rank")),
        "team_id": _int_or_none(team.get("id")),
        "team": _str_or_none(team.get("name")),
        "played": _int_or_none(totals.get("played")),
        "win": _int_or_none(totals.get("win")),
        "draw": _int_or_none(totals.get("draw")),
        "lose": _int_or_none(totals.get("lose")),
        "goals_for": _int_or_none(goals.get("for")),
        "goals_against": _int_or_none(goals.get("against")),
        "goal_diff": _int_or_none(row.get("goalsDiff")),
        "points": _int_or_none(row.get("points")),
        # Last 5 results, MOST RECENT FIRST: Arsenal 2024 = "WWDLD" while its last 5 fixtures
        # in date order were D, L, D, W, W (checked against /fixtures on 2026-11-11).
        "form": _str_or_none(row.get("form")),
        "description": _str_or_none(row.get("description")),
    }


# ---------------------------------------------------------------- SportScore

def _fetch_sportscore(competition: str, season: int | None, country: str | None,
                      context: dict[str, Any]) -> dict[str, Any]:
    # SportScore returns only its current table and no season field.
    current_hint = context.get("current_season")
    if season is not None and season != current_hint:
        raise ProviderError(
            "season_unverifiable",
            f"SportScore has no season filter or season metadata, so season {season} cannot be verified; "
            "current-season data is not used as a substitute",
        )

    entry = _known_sportscore_slug(competition, country) or _search_sportscore_slug(competition, country)
    slug = entry["slug"]
    cache_key = ("sportscore", "standings", slug)
    data = _cache_get(cache_key)
    if data is None:
        data = _get_json(f"{SPORTSCORE_BASE}/api/widget/standings/", params={"sport": "football", "slug": slug})
        if not isinstance(data, dict) or not isinstance(data.get("tables"), list):
            raise ProviderError("invalid_response", "SportScore response has no `tables` list")
        _cache_set(cache_key, data)

    groups = []
    for table in data["tables"]:
        if not isinstance(table, dict):
            continue
        rows = [_normalize_sportscore_row(row) for row in table.get("rows") or [] if isinstance(row, dict)]
        groups.append({"group": _str_or_none(table.get("group")), "rows": rows})

    note = "SportScore returns its current table without season metadata or form."
    if season is not None:
        note += f" Season {season} was accepted only because API-Football reports it as the current season."
    return {
        "competition": {
            "id": None,
            "name": _str_or_none(data.get("competition")) or entry.get("name"),
            "country": entry["country"].title() if entry.get("country") else None,
            "slug": slug,
        },
        "season": {"requested": season, "actual": None, "verified": False, "note": note},
        "provider": {"name": "SportScore", "fallback_used": True, "source_url": entry.get("url") or SPORTSCORE_SITE},
        "attribution": SPORTSCORE_ATTRIBUTION,
        "groups": groups,
    }


def _normalize_sportscore_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "rank": _int_or_none(row.get("pos")),
        "team_id": None,
        "team": _str_or_none(row.get("team")),
        "played": _int_or_none(row.get("p")),
        "win": _int_or_none(row.get("w")),
        "draw": _int_or_none(row.get("d")),
        "lose": _int_or_none(row.get("l")),
        "goals_for": _int_or_none(row.get("gf")),
        "goals_against": _int_or_none(row.get("ga")),
        "goal_diff": _int_or_none(row.get("gd")),
        "points": _int_or_none(row.get("pts")),
        "form": None,  # SportScore does not provide recent form
        "description": _str_or_none(row.get("promo_name")),
    }


# ---------------------------------------------------------------- entry point

PROVIDERS = [("API-Football", _fetch_api_football), ("SportScore", _fetch_sportscore)]


def _error(code: str, message: str, **extra: Any) -> dict[str, Any]:
    return {"tool": TOOL_NAME, "status": "error", "error": code, "message": message, **extra}


def standings(
    competition: str = "",
    season: int | str | None = None,
    country: str | None = None,
) -> dict[str, Any]:
    """League table of a football competition, API-Football first, SportScore as fallback."""
    try:
        if isinstance(competition, int) and not isinstance(competition, bool):
            competition = str(competition)
        if not isinstance(competition, str) or not competition.strip():
            raise ValueError("competition must be a non-empty string (name or numeric league id)")
        competition = competition.strip()
        if country is not None and not isinstance(country, str):
            raise ValueError("country must be a string such as 'England'")
        country_name = country.strip() if country and country.strip() else None
        season_year = _parse_season(season)
    except ValueError as exc:
        return _error("invalid_input", str(exc))

    canonical = _canonical_country(country_name)
    attempts: list[dict[str, Any]] = []
    context: dict[str, Any] = {}

    for provider_name, fetch in PROVIDERS:
        try:
            if provider_name == "API-Football":
                result = fetch(competition, season_year, canonical.title() if canonical else None, context)
            else:
                result = fetch(competition, season_year, canonical, context)
        except AmbiguousCompetition as exc:
            return _error(
                "ambiguous_competition",
                f"{exc.provider} found several competitions named {competition!r}; ask the user which one.",
                candidates=exc.candidates,
                attempts=attempts,
            )
        except ProviderError as exc:
            attempts.append({"provider": provider_name, "status": "failed", "reason": exc.reason,
                             "message": _safe(str(exc)), "http_status": exc.http_status})
            continue
        except Exception as exc:  # unexpected payload shape etc.: report, never crash the agent
            attempts.append({"provider": provider_name, "status": "failed", "reason": "unexpected_error",
                             "message": _safe(f"{type(exc).__name__}: {exc}"), "http_status": None})
            continue

        attempts.append({"provider": provider_name, "status": "success"})
        if attempts[0]["status"] == "failed":
            result["provider"]["fallback_reason"] = attempts[0]["reason"]
        count = sum(len(group["rows"]) for group in result["groups"])
        return {
            "tool": TOOL_NAME,
            "status": "success",
            **result,
            "count": count,
            "warning": None if count else "Provider returned an empty standings table.",
            "attempts": attempts,
        }

    return _error(
        "data_unavailable",
        "No provider could supply verified standings: "
        + "; ".join(f"{a['provider']}: {a['reason']}" for a in attempts),
        attempts=attempts,
    )
