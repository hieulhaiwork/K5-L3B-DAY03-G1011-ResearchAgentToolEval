"""top_scorers: football top-scorer leaderboard.

Provider order:
1. API-Football (primary, needs API_FOOTBALL_KEY, free plan 100 req/day).
2. SportScore (free fallback, no key, NO season metadata -> current leaderboard only).

Rules: never invent stats (missing -> None), never swap a requested season for
current data, never put the API key in the returned dict, never raise.
"""
from __future__ import annotations

import os
import re
import time
from typing import Any

import requests

from tools._shared import TIMEOUT, fold_text

TOOL_NAME = "top_scorers"

API_FOOTBALL_BASE = "https://v3.football.api-sports.io"
API_FOOTBALL_SITE = "https://www.api-football.com/"
SPORTSCORE_BASE = "https://sportscore.com"
SPORTSCORE_SITE = "https://sportscore.com/"
SPORTSCORE_ATTRIBUTION = {
    "required": True,
    "text": "Powered by SportScore",
    "url": SPORTSCORE_SITE,
    "html": '<a href="https://sportscore.com/" rel="dofollow">Powered by SportScore</a>',
}

MAX_LIMIT = 20          # API-Football returns at most 20 scorers
CACHE_TTL_SECONDS = 24 * 3600

# Country names the user may type -> English name used by both providers.
COUNTRY_ALIASES = {
    "england": "england", "anh": "england",
    "spain": "spain", "tay ban nha": "spain",
    "italy": "italy", "y": "italy",
    "germany": "germany", "duc": "germany",
    "france": "france", "phap": "france",
    "world": "world", "the gioi": "world", "europe": "world", "chau au": "world",
}

# SportScore slugs verified against the live API / developer docs on 2026-11-10.
# `aliases` match on their own; `country_aliases` (generic names such as
# "premier league") only match when the caller also gives the right country.
SPORTSCORE_COMPETITIONS: list[dict[str, Any]] = [
    {"slug": "english-premier-league", "name": "English Premier League", "country": "england",
     "aliases": ["english premier league", "epl", "ngoai hang anh"], "country_aliases": ["premier league"]},
    {"slug": "italian-serie-a", "name": "Italian Serie A", "country": "italy",
     "aliases": ["italian serie a"], "country_aliases": ["serie a"]},
    {"slug": "bundesliga", "name": "Bundesliga", "country": "germany",
     "aliases": ["german bundesliga"], "country_aliases": ["bundesliga"]},
    {"slug": "uefa-champions-league", "name": "UEFA Champions League", "country": "world",
     "aliases": ["uefa champions league", "champions league", "ucl", "cup c1"]},
    {"slug": "uefa-europa-league", "name": "UEFA Europa League", "country": "world",
     "aliases": ["uefa europa league", "europa league", "cup c2"]},
    {"slug": "uefa-europa-conference-league", "name": "UEFA Europa Conference League", "country": "world",
     "aliases": ["uefa europa conference league", "europa conference league", "conference league"]},
    {"slug": "uefa-nations-league", "name": "UEFA Nations League", "country": "world",
     "aliases": ["uefa nations league", "nations league"]},
    {"slug": "uefa-european-championship", "name": "UEFA European Championship", "country": "world",
     "aliases": ["uefa european championship", "euro"]},
    {"slug": "fifa-world-cup", "name": "FIFA World Cup", "country": "world",
     "aliases": ["fifa world cup", "world cup"]},
    {"slug": "afc-asian-cup", "name": "AFC Asian Cup", "country": "world", "aliases": ["afc asian cup", "asian cup"]},
    {"slug": "concacaf-gold-cup", "name": "CONCACAF Gold Cup", "country": "world",
     "aliases": ["concacaf gold cup", "gold cup"]},
]

_CACHE: dict[tuple[Any, ...], tuple[float, Any]] = {}


def clear_cache() -> None:
    """Drop all cached provider responses (used by tests)."""
    _CACHE.clear()


def _cache_get(key: tuple[Any, ...]) -> Any | None:
    hit = _CACHE.get(key)
    if hit and time.time() - hit[0] < CACHE_TTL_SECONDS:
        return hit[1]
    _CACHE.pop(key, None)
    return None


def _cache_set(key: tuple[Any, ...], value: Any) -> None:
    _CACHE[key] = (time.time(), value)


class ProviderError(Exception):
    """A provider could not supply the data. `reason` is a stable machine-readable code."""

    def __init__(self, reason: str, message: str, http_status: int | None = None) -> None:
        super().__init__(message)
        self.reason = reason
        self.http_status = http_status


class AmbiguousCompetition(Exception):
    def __init__(self, provider: str, candidates: list[dict[str, Any]]) -> None:
        super().__init__("ambiguous competition")
        self.provider = provider
        self.candidates = candidates


# ---------------------------------------------------------------- helpers

def _safe(text: str) -> str:
    """Remove the API key from any message before it leaves the tool."""
    key = os.getenv("API_FOOTBALL_KEY")
    if key:
        text = text.replace(key, "***")
    return text[:300]


def _get_json(url: str, *, params: dict[str, Any], headers: dict[str, str] | None = None) -> Any:
    try:
        response = requests.get(url, params=params, headers=headers or {}, timeout=TIMEOUT)
    except requests.Timeout:
        raise ProviderError("timeout", "Request timed out") from None
    except requests.RequestException as exc:
        raise ProviderError("connection_error", _safe(f"{type(exc).__name__}: {exc}")) from None

    status = response.status_code
    if status in (401, 403):
        raise ProviderError("auth_error", f"HTTP {status}: API key missing, invalid or not allowed", status)
    if status == 429:
        raise ProviderError("rate_limited", "HTTP 429: request quota exhausted, not retrying", status)
    if status >= 500:
        raise ProviderError("server_error", f"HTTP {status}: provider server error", status)
    try:
        data = response.json()
    except ValueError:
        raise ProviderError("invalid_json", f"HTTP {status}: response is not valid JSON", status) from None
    if status == 404:
        detail = data.get("error") if isinstance(data, dict) else None
        raise ProviderError("not_found", _safe(f"HTTP 404: {detail or 'not found'}"), status)
    if status >= 400:
        raise ProviderError("http_error", f"HTTP {status}", status)
    return data


def _int_or_none(value: Any) -> int | None:
    """Keep missing stats as None; never turn them into 0."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str) and value.strip().lstrip("-").isdigit():
        return int(value.strip())
    return None


def _str_or_none(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _canonical_country(country: str | None) -> str | None:
    if country is None:
        return None
    folded = fold_text(country).strip()
    return COUNTRY_ALIASES.get(folded, folded)


def _parse_season(season: Any) -> int | None:
    """Accept 2025, "2025", "2025/26", "2025-2026" -> 2025. Raise ValueError otherwise."""
    if season is None or (isinstance(season, str) and not season.strip()):
        return None
    if isinstance(season, bool):
        raise ValueError("season must be a four-digit starting year, e.g. 2025 for 2025/26")
    if isinstance(season, int):
        year = season
    elif isinstance(season, str):
        match = re.fullmatch(r"\s*(\d{4})(?:\s*[/-]\s*(?:\d{2}|\d{4}))?\s*", season)
        if not match:
            raise ValueError("season must be a four-digit starting year, e.g. 2025 for 2025/26")
        year = int(match.group(1))
    else:
        raise ValueError("season must be a four-digit starting year, e.g. 2025 for 2025/26")
    if not 1900 <= year <= 2100:
        raise ValueError("season must be a four-digit starting year between 1900 and 2100")
    return year


def _parse_limit(limit: Any) -> int:
    if isinstance(limit, bool):
        raise ValueError("limit must be an integer between 1 and 20")
    value = _int_or_none(limit)
    if value is None or not 1 <= value <= MAX_LIMIT:
        raise ValueError("limit must be an integer between 1 and 20")
    return value


# ---------------------------------------------------------------- API-Football

def _api_football_leagues(params: dict[str, Any], key: str) -> list[dict[str, Any]]:
    cache_key = ("api_football", "leagues", tuple(sorted(params.items())))
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    data = _api_football_call("/leagues", params, key)
    _cache_set(cache_key, data)
    return data


def _api_football_call(path: str, params: dict[str, Any], key: str) -> list[dict[str, Any]]:
    data = _get_json(f"{API_FOOTBALL_BASE}{path}", params=params, headers={"x-apisports-key": key})
    if not isinstance(data, dict):
        raise ProviderError("invalid_response", "API-Football response is not a JSON object")
    errors = data.get("errors")
    if errors:  # API-Football reports most failures as HTTP 200 + non-empty `errors`
        text = " ".join(str(v) for v in (errors.values() if isinstance(errors, dict) else errors))
        names = set(errors) if isinstance(errors, dict) else set()
        if "token" in names:
            reason = "auth_error"
        elif "plan" in names:
            reason = "plan_restriction"
        elif names & {"requests", "rateLimit"}:
            reason = "rate_limited"
        else:
            reason = "provider_error"
        raise ProviderError(reason, _safe(f"API-Football: {text}"))
    response = data.get("response")
    if not isinstance(response, list):
        raise ProviderError("invalid_response", "API-Football response has no `response` list")
    return response


def _fetch_api_football(competition: str, season: int | None, limit: int, country: str | None,
                        context: dict[str, Any]) -> dict[str, Any]:
    key = os.getenv("API_FOOTBALL_KEY")
    if not key:
        raise ProviderError("missing_api_key", "API_FOOTBALL_KEY is not configured")

    if competition.isdigit():
        params: dict[str, Any] = {"id": int(competition)}
        leagues = _api_football_leagues(params, key)
    else:
        params = {"name": competition}
        if country:
            params["country"] = country
        leagues = _api_football_leagues(params, key)
        if not leagues and len(competition) >= 3:
            search_params = {"search": competition, **({"country": country} if country else {})}
            leagues = _api_football_leagues(search_params, key)

    unique: dict[Any, dict[str, Any]] = {}
    for item in leagues:
        league_id = (item.get("league") or {}).get("id")
        if league_id is not None:
            unique[league_id] = item
    if not unique:
        raise ProviderError("competition_not_found", f"No API-Football competition matches {competition!r}")
    if len(unique) > 1:
        raise AmbiguousCompetition("API-Football", [{
            "id": item["league"].get("id"),
            "name": item["league"].get("name"),
            "country": (item.get("country") or {}).get("name"),
            "type": item["league"].get("type"),
        } for item in unique.values()])

    item = next(iter(unique.values()))
    league = item.get("league") or {}
    seasons = [s for s in item.get("seasons") or [] if isinstance(s, dict)]
    current = next((s for s in seasons if s.get("current")), None)
    if current is not None:
        context["current_season"] = _int_or_none(current.get("year"))

    if season is None:
        if current is None:
            raise ProviderError("unsupported_season", "API-Football does not report a current season for this competition")
        chosen = current
    else:
        chosen = next((s for s in seasons if _int_or_none(s.get("year")) == season), None)
        if chosen is None:
            raise ProviderError("unsupported_season", f"Season {season} is not available for this competition on API-Football")
    year = _int_or_none(chosen.get("year"))
    if not (chosen.get("coverage") or {}).get("top_scorers"):
        raise ProviderError("no_top_scorers_coverage", f"API-Football has no top-scorer coverage for season {year}")

    cache_key = ("api_football", "topscorers", league.get("id"), year)
    rows = _cache_get(cache_key)
    if rows is None:
        rows = _api_football_call("/players/topscorers", {"league": league.get("id"), "season": year}, key)
        _cache_set(cache_key, rows)

    scorers = [_normalize_api_football_row(index, row) for index, row in enumerate(rows[:limit], start=1)
               if isinstance(row, dict)]
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
        "scorers": scorers,
    }


def _normalize_api_football_row(rank: int, row: dict[str, Any]) -> dict[str, Any]:
    player = row.get("player") or {}
    stats_list = row.get("statistics") or []
    stats = stats_list[0] if stats_list and isinstance(stats_list[0], dict) else {}
    team = stats.get("team") or {}
    games = stats.get("games") or {}
    goals = stats.get("goals") or {}
    penalty = stats.get("penalty") or {}
    return {
        "rank": rank,  # provider order preserved, including its tie-breaking
        "player_id": _int_or_none(player.get("id")),
        "player": _str_or_none(player.get("name")),
        "nationality": _str_or_none(player.get("nationality")),
        "age": _int_or_none(player.get("age")),
        "position": _str_or_none(games.get("position")),
        "photo": _str_or_none(player.get("photo")),
        "team_id": _int_or_none(team.get("id")),
        "team": _str_or_none(team.get("name")),
        "goals": _int_or_none(goals.get("total")),
        "assists": _int_or_none(goals.get("assists")),
        "penalties": _int_or_none(penalty.get("scored")),
        "appearances": _int_or_none(games.get("appearences")),  # sic: API-Football spelling
        "minutes": _int_or_none(games.get("minutes")),
    }


# ---------------------------------------------------------------- SportScore

def _known_sportscore_slug(competition: str, country: str | None) -> dict[str, Any] | None:
    name = fold_text(competition).strip()
    for entry in SPORTSCORE_COMPETITIONS:
        if country and entry["country"] not in (country, "world"):
            continue
        if name in entry["aliases"] or name == entry["slug"]:
            return entry
        if country == entry["country"] and name in entry.get("country_aliases", []):
            return entry
    return None


def _search_sportscore_slug(competition: str, country: str | None) -> dict[str, Any]:
    """Resolve an unlisted competition through SportScore search. Only exact name
    matches (or '<Country adjective> <name>' inside the given country) are accepted."""
    cache_key = ("sportscore", "search", fold_text(competition), country)
    data = _cache_get(cache_key)
    if data is None:
        data = _get_json(f"{SPORTSCORE_BASE}/api/v1/search/",
                         params={"q": competition, "sport": "football", "limit": 20})
        _cache_set(cache_key, data)
    target = fold_text(competition).strip()
    matches: list[dict[str, Any]] = []
    for item in (data.get("competitions") if isinstance(data, dict) else None) or []:
        url_match = re.match(r"^/football/competition/([^/]+)/([^/]+)/", str(item.get("url", "")))
        if not url_match or not item.get("slug"):
            continue
        url_country = url_match.group(1)
        found = fold_text(str(item.get("name", ""))).strip()
        if country:
            if url_country != country:
                continue
            ok = found == target or found.endswith(" " + target)
        else:
            ok = found == target
        if ok:
            matches.append({"slug": item["slug"], "name": item.get("name"), "country": url_country,
                            "url": f"{SPORTSCORE_BASE}{item['url']}"})
    if not matches:
        hint = "" if country else " Try again with the competition's country."
        raise ProviderError("competition_not_found", f"No verified SportScore slug for {competition!r}.{hint}")
    if len(matches) > 1:
        raise AmbiguousCompetition("SportScore", matches)
    return matches[0]


def _fetch_sportscore(competition: str, season: int | None, limit: int, country: str | None,
                      context: dict[str, Any]) -> dict[str, Any]:
    # SportScore returns only the provider's current leaderboard and no season field.
    current_hint = context.get("current_season")
    if season is not None and season != current_hint:
        raise ProviderError(
            "season_unverifiable",
            f"SportScore has no season filter or season metadata, so season {season} cannot be verified; "
            "current-season data is not used as a substitute",
        )

    entry = _known_sportscore_slug(competition, country) or _search_sportscore_slug(competition, country)
    slug = entry["slug"]
    cache_key = ("sportscore", "topscorers", slug)
    data = _cache_get(cache_key)
    if data is None:
        data = _get_json(f"{SPORTSCORE_BASE}/api/widget/topscorers/",
                         params={"sport": "football", "slug": slug, "limit": MAX_LIMIT, "stat": "goals"})
        if not isinstance(data, dict) or not isinstance(data.get("scorers"), list):
            raise ProviderError("invalid_response", "SportScore response has no `scorers` list")
        if data.get("stat_type") not in (None, "goals"):
            raise ProviderError("invalid_response", f"SportScore returned stat_type={data.get('stat_type')!r}")
        _cache_set(cache_key, data)

    scorers = [_normalize_sportscore_row(row) for row in data["scorers"][:limit] if isinstance(row, dict)]
    note = "SportScore returns its current leaderboard without season metadata."
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
        "scorers": scorers,
    }


def _normalize_sportscore_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "rank": _int_or_none(row.get("rank")),
        "player_id": None,
        "player": _str_or_none(row.get("player")),
        "nationality": None,
        "age": None,
        "position": None,
        "photo": _str_or_none(row.get("player_logo")),
        "team_id": None,
        "team": _str_or_none(row.get("team")),
        "goals": _int_or_none(row.get("goals")),
        "assists": _int_or_none(row.get("assists")),
        "penalties": None,  # SportScore does not provide penalty goals
        "appearances": _int_or_none(row.get("matches")),
        "minutes": _int_or_none(row.get("minutes")),
    }


# ---------------------------------------------------------------- entry point

PROVIDERS = [("API-Football", _fetch_api_football), ("SportScore", _fetch_sportscore)]


def _error(code: str, message: str, **extra: Any) -> dict[str, Any]:
    return {"tool": TOOL_NAME, "status": "error", "error": code, "message": message, **extra}


def top_scorers(
    competition: str = "",
    season: int | str | None = None,
    limit: int = 10,
    country: str | None = None,
) -> dict[str, Any]:
    """Top goal scorers of a football competition, API-Football first, SportScore as fallback."""
    try:
        if isinstance(competition, int) and not isinstance(competition, bool):
            competition = str(competition)
        if not isinstance(competition, str) or not competition.strip():
            raise ValueError("competition must be a non-empty string (name or numeric league id)")
        competition = competition.strip()
        if country is not None and not isinstance(country, str):
            raise ValueError("country must be a string such as 'England'")
        country_name = country.strip() if country and country.strip() else None  # "" from the model = not given
        season_year = _parse_season(season)
        limit_value = _parse_limit(limit)
    except ValueError as exc:
        return _error("invalid_input", str(exc))

    canonical = _canonical_country(country_name)
    attempts: list[dict[str, Any]] = []
    context: dict[str, Any] = {}

    for provider_name, fetch in PROVIDERS:
        try:
            if provider_name == "API-Football":
                api_country = canonical.title() if canonical else None
                result = fetch(competition, season_year, limit_value, api_country, context)
            else:
                result = fetch(competition, season_year, limit_value, canonical, context)
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
        warning = None if result["scorers"] else "Provider returned an empty scorer list."
        return {
            "tool": TOOL_NAME,
            "status": "success",
            **result,
            "count": len(result["scorers"]),
            "warning": warning,
            "attempts": attempts,
        }

    return _error(
        "data_unavailable",
        "No provider could supply verified top-scorer data: "
        + "; ".join(f"{a['provider']}: {a['reason']}" for a in attempts),
        attempts=attempts,
    )
