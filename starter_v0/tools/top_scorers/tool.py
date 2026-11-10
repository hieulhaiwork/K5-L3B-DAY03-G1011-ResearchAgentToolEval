from __future__ import annotations

import copy
import os
import re
import time
import unicodedata
from dataclasses import dataclass
from typing import Any

import requests


API_FOOTBALL_BASE_URL = "https://v3.football.api-sports.io"
SPORTSCORE_BASE_URL = "https://sportscore.com"
API_FOOTBALL_SOURCE_URL = "https://www.api-football.com/"
SPORTSCORE_SOURCE_URL = "https://sportscore.com/"
SPORTSCORE_ATTRIBUTION_HTML = (
    '<a href="https://sportscore.com/" rel="dofollow" '
    'title="Sports data by SportScore">Powered by SportScore</a>'
)
TIMEOUT = 15
CACHE_TTL_SECONDS = 24 * 60 * 60

# These are the competition slugs shown in SportScore's public API documentation.
SPORTSCORE_COMPETITIONS: dict[str, dict[str, str | None]] = {
    "premier league": {"slug": "premier-league", "name": "Premier League", "country": "England"},
    "epl": {"slug": "premier-league", "name": "Premier League", "country": "England"},
    "uefa champions league": {
        "slug": "uefa-champions-league",
        "name": "UEFA Champions League",
        "country": None,
    },
    "champions league": {
        "slug": "uefa-champions-league",
        "name": "UEFA Champions League",
        "country": None,
    },
    "ucl": {"slug": "uefa-champions-league", "name": "UEFA Champions League", "country": None},
}

_cache: dict[tuple[Any, ...], tuple[float, Any]] = {}


@dataclass
class _ProviderFailure(Exception):
    code: str
    message: str
    candidates: list[dict[str, Any]] | None = None


@dataclass
class _ResolvedCompetition:
    league_id: int
    name: str
    country: str | None
    slug: str | None
    season: int


def _normalized(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.casefold())
    return " ".join(
        "".join(char for char in decomposed if unicodedata.category(char) != "Mn").split()
    )


def _cached(key: tuple[Any, ...]) -> Any | None:
    entry = _cache.get(key)
    if entry is None:
        return None
    expires_at, value = entry
    if expires_at <= time.monotonic():
        _cache.pop(key, None)
        return None
    return copy.deepcopy(value)


def _cache_value(key: tuple[Any, ...], value: Any) -> None:
    _cache[key] = (time.monotonic() + CACHE_TTL_SECONDS, copy.deepcopy(value))


def _validate_inputs(
    competition: Any,
    season: Any,
    limit: Any,
    country: Any,
) -> dict[str, Any] | None:
    if not isinstance(competition, str) or not competition.strip():
        return _error("invalid_input", "competition must be a non-empty string.")
    if re.fullmatch(r"\d+", competition.strip()) and int(competition) < 1:
        return _error("invalid_input", "numeric competition IDs must be positive.")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 20:
        return _error("invalid_input", "limit must be an integer between 1 and 20.")
    if season is not None and (
        isinstance(season, bool) or not isinstance(season, int) or not 1000 <= season <= 9999
    ):
        return _error("invalid_input", "season must be a four-digit starting year.")
    if country is not None and (not isinstance(country, str) or not country.strip()):
        return _error("invalid_input", "country must be a non-empty string when supplied.")
    return None


def _error(
    code: str,
    message: str,
    *,
    provider_errors: list[dict[str, str]] | None = None,
    candidates: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "tool": "top_scorers",
        "status": "needs_clarification" if code == "ambiguous_competition" else "error",
        "error": code,
        "message": message,
    }
    if provider_errors:
        result["provider_errors"] = provider_errors
    if candidates:
        result["candidates"] = candidates
    return result


def _provider_error(name: str, failure: _ProviderFailure) -> dict[str, str]:
    return {"provider": name, "error": failure.code, "message": failure.message}


def _http_failure(status_code: int) -> _ProviderFailure:
    if status_code in (401, 403):
        return _ProviderFailure("invalid_api_key" if status_code == 401 else "forbidden", f"HTTP {status_code}.")
    if status_code == 429:
        return _ProviderFailure("rate_limited", "HTTP 429; the provider request quota may be exhausted.")
    if status_code >= 500:
        return _ProviderFailure("provider_unavailable", f"HTTP {status_code}.")
    return _ProviderFailure("http_error", f"HTTP {status_code}.")


def _get_json(
    url: str,
    *,
    params: dict[str, Any],
    headers: dict[str, str] | None = None,
    provider: str,
) -> dict[str, Any] | list[Any]:
    try:
        response = requests.get(url, params=params, headers=headers or {}, timeout=TIMEOUT)
    except requests.Timeout as exc:
        raise _ProviderFailure("timeout", f"{provider} request timed out.") from exc
    except requests.ConnectionError as exc:
        raise _ProviderFailure("connection_error", f"Could not connect to {provider}.") from exc
    except requests.RequestException as exc:
        raise _ProviderFailure("request_error", f"{provider} request failed ({type(exc).__name__}).") from exc

    if response.status_code >= 400:
        raise _http_failure(response.status_code)
    try:
        data = response.json()
    except ValueError as exc:
        raise _ProviderFailure("invalid_json", f"{provider} returned invalid JSON.") from exc
    if not isinstance(data, (dict, list)):
        raise _ProviderFailure("invalid_response", f"{provider} returned an unsupported JSON response.")
    return data


def _api_football_get(path: str, params: dict[str, Any]) -> dict[str, Any] | list[Any]:
    key = os.getenv("API_FOOTBALL_KEY")
    if not key:
        raise _ProviderFailure("missing_api_key", "API_FOOTBALL_KEY is not configured.")
    data = _get_json(
        f"{API_FOOTBALL_BASE_URL}{path}",
        params=params,
        headers={"x-apisports-key": key},
        provider="API-Football",
    )
    if isinstance(data, dict) and data.get("errors"):
        errors = data["errors"]
        if isinstance(errors, dict):
            first = next(iter(errors.values()), "API request was rejected.")
        elif isinstance(errors, list):
            first = errors[0] if errors else "API request was rejected."
        else:
            first = errors
        message = str(first)
        if key in message:
            message = message.replace(key, "[redacted]")
        raise _ProviderFailure("api_error", message[:300])
    return data


def _response_rows(data: dict[str, Any] | list[Any], provider: str) -> list[dict[str, Any]]:
    if isinstance(data, list):
        rows = data
    else:
        rows = data.get("response")
        if rows is None:
            rows = data.get("data")
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise _ProviderFailure("invalid_response", f"{provider} response did not contain a valid result list.")
    return rows


def _competition_id(value: str) -> int | None:
    if not re.fullmatch(r"\d+", value.strip()):
        return None
    return int(value)


def _season_for_league(
    league: dict[str, Any],
    requested_season: int | None,
) -> dict[str, Any] | None:
    seasons = league.get("seasons")
    if not isinstance(seasons, list):
        return None
    if requested_season is None:
        matches = [item for item in seasons if isinstance(item, dict) and item.get("current") is True]
    else:
        matches = [
            item for item in seasons
            if isinstance(item, dict) and str(item.get("year", "")) == str(requested_season)
        ]
    return matches[0] if len(matches) == 1 else None


def _resolve_competition(
    competition: str,
    season: int | None,
    country: str | None,
) -> _ResolvedCompetition:
    cache_key = ("league", _normalized(competition), _normalized(country or ""), season)
    cached = _cached(cache_key)
    if cached is not None:
        return cached

    league_id = _competition_id(competition)
    params: dict[str, Any] = {"id": league_id} if league_id is not None else {"search": competition.strip()}
    if country:
        params["country"] = country.strip()
    if season is not None:
        params["season"] = season
    else:
        params["current"] = "true"

    payload = _api_football_get("/leagues", params)
    candidates = _response_rows(payload, "API-Football")
    matches: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for candidate in candidates:
        league = candidate.get("league") or {}
        league_country = candidate.get("country") or {}
        if not isinstance(league, dict) or not isinstance(league_country, dict):
            continue
        candidate_id = league.get("id")
        if league_id is not None:
            if str(candidate_id) != str(league_id):
                continue
        elif _normalized(str(league.get("name") or "")) != _normalized(competition):
            continue
        candidate_country = str(league_country.get("name") or "")
        if country and _normalized(candidate_country) != _normalized(country):
            continue
        matches.append((candidate, league))

    unique: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    for candidate, league in matches:
        unique[str(league.get("id"))] = (candidate, league)
    matches = list(unique.values())
    if not matches:
        raise _ProviderFailure("competition_not_found", "No exact competition match was returned.")
    if len(matches) > 1:
        raise _ProviderFailure(
            "ambiguous_competition",
            "Multiple competitions match; specify a country or league ID.",
            candidates=[
                {
                    "id": league.get("id"),
                    "name": league.get("name"),
                    "country": (entry.get("country") or {}).get("name"),
                }
                for entry, league in matches
            ],
        )

    entry, league = matches[0]
    season_info = _season_for_league(entry, season)
    if season_info is None:
        raise _ProviderFailure("unsupported_season", "The requested/current season could not be verified.")
    coverage = season_info.get("coverage")
    if not isinstance(coverage, dict) or coverage.get("top_scorers") is not True:
        raise _ProviderFailure("unsupported_competition", "Top-scorer coverage is not available for this season.")
    actual_season = season_info.get("year")
    try:
        actual_season = int(actual_season)
        resolved_id = int(league["id"])
    except (TypeError, ValueError, KeyError) as exc:
        raise _ProviderFailure("invalid_response", "API-Football returned incomplete competition metadata.") from exc

    resolved = _ResolvedCompetition(
        league_id=resolved_id,
        name=str(league.get("name") or competition),
        country=str((entry.get("country") or {}).get("name") or "") or None,
        slug=None,
        season=actual_season,
    )
    _cache_value(cache_key, resolved)
    return resolved


def _first_value(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _stat_value(value: Any) -> int | float | None:
    if isinstance(value, dict):
        value = _first_value(value.get("total"), value.get("value"))
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str) and re.fullmatch(r"\s*\d+(?:\.\d+)?\s*", value):
        number = float(value)
        return int(number) if number.is_integer() else number
    return None


def _rank_value(value: Any, fallback: int) -> int:
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        return value
    if isinstance(value, str) and value.isdigit() and int(value) > 0:
        return int(value)
    return fallback


def _normalize_api_football_scorer(row: dict[str, Any], rank: int) -> dict[str, Any]:
    player = row.get("player") if isinstance(row.get("player"), dict) else {}
    statistics = row.get("statistics")
    stats = statistics[0] if isinstance(statistics, list) and statistics and isinstance(statistics[0], dict) else {}
    team = stats.get("team") if isinstance(stats.get("team"), dict) else {}
    games = stats.get("games") if isinstance(stats.get("games"), dict) else {}
    goals = stats.get("goals") if isinstance(stats.get("goals"), dict) else {}
    penalty = stats.get("penalty") if isinstance(stats.get("penalty"), dict) else {}
    return {
        "rank": _rank_value(row.get("rank"), rank),
        "player_id": player.get("id"),
        "player": player.get("name"),
        "nationality": player.get("nationality"),
        "age": player.get("age"),
        "position": games.get("position"),
        "photo_url": player.get("photo"),
        "team_id": team.get("id"),
        "team": team.get("name"),
        "goals": goals.get("total"),
        "assists": goals.get("assists"),
        "penalties": penalty.get("scored"),
        "appearances": games.get("appearences", games.get("appearances")),
        "minutes": games.get("minutes"),
    }


def _source_result(
    scorers: list[dict[str, Any]],
    competition: dict[str, Any],
    season: dict[str, Any],
    provider: dict[str, Any],
    limit: int,
) -> dict[str, Any]:
    selected = copy.deepcopy(scorers[:limit])
    return {
        "tool": "top_scorers",
        "status": "success",
        "competition": competition,
        "season": season,
        "provider": provider,
        "count": len(selected),
        "scorers": selected,
    }


def _api_football_result(resolved: _ResolvedCompetition, season_requested: int | None) -> dict[str, Any]:
    key = ("api_scorers", resolved.league_id, resolved.season)
    scorers = _cached(key)
    if scorers is None:
        payload = _api_football_get(
            "/players/topscorers",
            {"league": resolved.league_id, "season": resolved.season},
        )
        rows = _response_rows(payload, "API-Football")
        if not rows:
            raise _ProviderFailure("empty_scorer_list", "API-Football returned no top scorers.")
        scorers = [_normalize_api_football_scorer(row, index) for index, row in enumerate(rows, start=1)]
        if not all(scorer["player"] for scorer in scorers):
            raise _ProviderFailure("invalid_response", "API-Football returned a scorer without a player name.")
        _cache_value(key, scorers)
    return _source_result(
        scorers,
        {"id": resolved.league_id, "name": resolved.name, "country": resolved.country, "slug": None},
        {"requested": season_requested, "actual": resolved.season, "verified": True},
        {
            "name": "API-Football",
            "fallback_used": False,
            "source_url": API_FOOTBALL_SOURCE_URL,
        },
        20,
    )


def _sportscore_competition(competition: str, country: str | None) -> dict[str, str | None] | None:
    info = SPORTSCORE_COMPETITIONS.get(_normalized(competition))
    if not info:
        return None
    if country and info.get("country") and _normalized(country) != _normalized(str(info["country"])):
        return None
    return dict(info)


def _sportscore_rows(payload: dict[str, Any] | list[Any]) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        rows: Any = payload
    else:
        rows = None
        for key in ("topscorers", "top_scorers", "players", "results", "data"):
            candidate = payload.get(key)
            if isinstance(candidate, list):
                rows = candidate
                break
            if isinstance(candidate, dict):
                nested = candidate.get("topscorers") or candidate.get("players") or candidate.get("results")
                if isinstance(nested, list):
                    rows = nested
                    break
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise _ProviderFailure("invalid_response", "SportScore response did not contain a recognized scorer list.")
    return rows


def _sportscore_actual_season(
    payload: dict[str, Any] | list[Any],
    rows: list[dict[str, Any]],
) -> int | None:
    values: list[Any] = []
    if isinstance(payload, dict):
        for key in ("season", "season_year", "year"):
            values.append(payload.get(key))
        for key in ("competition", "league", "meta", "metadata"):
            node = payload.get(key)
            if isinstance(node, dict):
                values.extend(node.get(name) for name in ("season", "season_year", "year"))
        nested_data = payload.get("data")
        if isinstance(nested_data, dict):
            values.extend(nested_data.get(name) for name in ("season", "season_year", "year"))
            for key in ("competition", "league", "meta", "metadata"):
                node = nested_data.get(key)
                if isinstance(node, dict):
                    values.extend(node.get(name) for name in ("season", "season_year", "year"))
    if rows:
        row_seasons = [row.get("season") or row.get("season_year") for row in rows]
        if row_seasons and all(value is not None for value in row_seasons) and len(set(map(str, row_seasons))) == 1:
            values.append(row_seasons[0])
    for value in values:
        if isinstance(value, dict):
            value = value.get("year") or value.get("start_year")
        match = re.match(r"^\s*(\d{4})", str(value or ""))
        if match:
            return int(match.group(1))
    return None


def _sportscore_scorer(row: dict[str, Any], rank: int, goals_value: Any = None) -> dict[str, Any]:
    player_data = row.get("player")
    player = player_data if isinstance(player_data, dict) else {}
    team_data = row.get("team")
    team = team_data if isinstance(team_data, dict) else {}
    stats = row.get("statistics") if isinstance(row.get("statistics"), dict) else {}
    return {
        "rank": _rank_value(row.get("rank"), rank),
        "player_id": _first_value(player.get("id"), row.get("player_id")),
        "player": _first_value(player.get("name"), player_data if isinstance(player_data, str) else None, row.get("player_name"), row.get("name")),
        "nationality": _first_value(player.get("nationality"), row.get("nationality")),
        "age": _first_value(player.get("age"), row.get("age")),
        "position": _first_value(player.get("position"), row.get("position_name")),
        "photo_url": _first_value(player.get("photo"), player.get("photo_url"), row.get("photo")),
        "team_id": _first_value(team.get("id"), row.get("team_id")),
        "team": _first_value(team.get("name"), team_data if isinstance(team_data, str) else None, row.get("team_name")),
        "goals": _stat_value(_first_value(goals_value, row.get("goals"), row.get("total_goals"), stats.get("goals"))),
        "assists": _stat_value(_first_value(row.get("assists"), row.get("total_assists"), stats.get("assists"))),
        "penalties": _stat_value(_first_value(row.get("penalties"), row.get("penalty_goals"), stats.get("penalties"))),
        "appearances": _stat_value(_first_value(row.get("appearances"), row.get("apps"), stats.get("appearances"))),
        "minutes": _stat_value(_first_value(row.get("minutes"), stats.get("minutes"))),
    }


def _player_keys(scorer: dict[str, Any]) -> list[str]:
    keys: list[str] = []
    player_id = scorer.get("player_id")
    if player_id is not None:
        keys.append(f"id:{player_id}")
    player_name = _normalized(str(scorer.get("player") or ""))
    if player_name:
        keys.append(f"name:{player_name}")
    return keys


def _sportscore_result(
    competition: str,
    country: str | None,
    season_requested: int | None,
    limit: int,
) -> dict[str, Any]:
    info = _sportscore_competition(competition, country)
    if info is None:
        raise _ProviderFailure(
            "unverified_competition_slug",
            "SportScore has no verified slug for this competition and country.",
        )
    cache_key = ("sportscore", info["slug"], season_requested, limit)
    cached = _cached(cache_key)
    if cached is not None:
        return _source_result(
            cached["scorers"],
            cached["competition"],
            cached["season"],
            cached["provider"],
            limit,
        )

    base_params = {"sport": "football", "slug": info["slug"], "limit": limit}
    payload = _get_json(
        f"{SPORTSCORE_BASE_URL}/api/widget/topscorers/",
        params={**base_params, "stat": "goals"},
        provider="SportScore",
    )
    rows = _sportscore_rows(payload)
    if not rows:
        raise _ProviderFailure("empty_scorer_list", "SportScore returned no top scorers.")
    actual_season = _sportscore_actual_season(payload, rows)
    if season_requested is not None and actual_season != season_requested:
        raise _ProviderFailure(
            "unsupported_season",
            "SportScore did not verify the requested historical season; current data was not substituted.",
        )

    goal_scorers = [_sportscore_scorer(row, index) for index, row in enumerate(rows, start=1)]
    if not all(scorer["player"] for scorer in goal_scorers):
        raise _ProviderFailure("invalid_response", "SportScore returned a scorer without a player name.")

    warnings: list[dict[str, str]] = []
    try:
        assists_payload = _get_json(
            f"{SPORTSCORE_BASE_URL}/api/widget/topscorers/",
            params={**base_params, "stat": "assists"},
            provider="SportScore",
        )
        assists_rows = _sportscore_rows(assists_payload)
        assists_by_player: dict[str, int | float] = {}
        for index, row in enumerate(assists_rows, start=1):
            assist_scorer = _sportscore_scorer(row, index)
            assist_value = _stat_value(
                _first_value(row.get("assists"), row.get("total_assists"), row.get("value"))
            )
            if assist_value is not None:
                for key in _player_keys(assist_scorer):
                    assists_by_player[key] = assist_value
        for scorer in goal_scorers:
            scorer["assists"] = _first_value(
                *(assists_by_player[key] for key in _player_keys(scorer) if key in assists_by_player),
                scorer["assists"],
            )
    except _ProviderFailure as exc:
        warnings.append({"provider": "SportScore", "error": exc.code, "message": exc.message})

    season_result = {
        "requested": season_requested,
        "actual": actual_season,
        "verified": actual_season is not None and (
            season_requested is None or actual_season == season_requested
        ),
    }
    competition_metadata: dict[str, Any] = {}
    if isinstance(payload, dict):
        for key in ("competition", "league"):
            candidate = payload.get(key)
            if isinstance(candidate, dict):
                competition_metadata = candidate
                break
        if not competition_metadata and isinstance(payload.get("data"), dict):
            for key in ("competition", "league"):
                candidate = payload["data"].get(key)
                if isinstance(candidate, dict):
                    competition_metadata = candidate
                    break
    competition_result = {
        "id": None,
        "name": competition_metadata.get("name") or info["name"],
        "country": country or competition_metadata.get("country") or info["country"],
        "slug": competition_metadata.get("slug") or info["slug"],
    }
    provider_result = {
        "name": "SportScore",
        "fallback_used": True,
        "source_url": SPORTSCORE_SOURCE_URL,
        "attribution": {
            "label": "Powered by SportScore",
            "url": SPORTSCORE_SOURCE_URL,
            "rel": "dofollow",
            "html": SPORTSCORE_ATTRIBUTION_HTML,
        },
    }
    if warnings:
        provider_result["warnings"] = warnings
    result = _source_result(goal_scorers, competition_result, season_result, provider_result, 20)
    _cache_value(
        cache_key,
        {"scorers": result["scorers"], "competition": competition_result, "season": season_result, "provider": provider_result},
    )
    return _source_result(result["scorers"], competition_result, season_result, provider_result, limit)


def top_scorers(
    competition: str,
    season: int | None = None,
    limit: int = 10,
    country: str | None = None,
) -> dict[str, Any]:
    """Return verified top-scorer data, using SportScore only as a safe fallback."""
    invalid = _validate_inputs(competition, season, limit, country)
    if invalid:
        return invalid

    provider_errors: list[dict[str, str]] = []
    try:
        resolved = _resolve_competition(competition, season, country)
        result = _api_football_result(resolved, season)
        result["scorers"] = result["scorers"][:limit]
        result["count"] = len(result["scorers"])
        return result
    except _ProviderFailure as exc:
        if exc.code == "ambiguous_competition":
            return _error(exc.code, exc.message, candidates=exc.candidates)
        provider_errors.append(_provider_error("API-Football", exc))

    try:
        result = _sportscore_result(competition, country, season, limit)
        result["provider_errors"] = provider_errors
        return result
    except _ProviderFailure as exc:
        provider_errors.append(_provider_error("SportScore", exc))

    if any(item["error"] == "unsupported_season" for item in provider_errors):
        code = "unsupported_season"
        message = "The requested season is unavailable from the configured providers; no substitute season was used."
    elif any(item["error"] == "unverified_competition_slug" for item in provider_errors):
        code = "data_unavailable"
        message = "No provider could verify this competition and season."
    else:
        code = "data_unavailable"
        message = "Neither API-Football nor SportScore could provide verified top-scorer data."
    return _error(code, message, provider_errors=provider_errors)
