"""Unit tests for the top_scorers tool (offline: every HTTP call is mocked).

Payload shapes mirror real responses captured on 2026-11-10:
- API-Football without key -> HTTP 403 + {"errors": {"token": ...}, "response": []}
- SportScore /api/widget/topscorers/ -> {"competition", "stat_type", "scorers": [{rank, player, team, goals, assists, matches, minutes, ...}]}
Player names below are fake.
"""
from __future__ import annotations

import json
from typing import Any

import pytest
import requests

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS
from tools.top_scorers import tool as top_scorers_module

top_scorers = TOOL_FUNCTIONS["top_scorers"]

API_KEY = "secret-test-key-123"
AF_LEAGUES = "v3.football.api-sports.io/leagues"
AF_TOPSCORERS = "v3.football.api-sports.io/players/topscorers"
SS_TOPSCORERS = "sportscore.com/api/widget/topscorers/"
SS_SEARCH = "sportscore.com/api/v1/search/"


@pytest.fixture(autouse=True)
def fresh_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """No cache carry-over between tests, and no real key from the developer's shell."""
    top_scorers_module.clear_cache()
    monkeypatch.delenv("API_FOOTBALL_KEY", raising=False)


class BadJsonResponse(FakeResponse):
    def json(self) -> Any:
        raise ValueError("not json")


@pytest.fixture
def http_routes(monkeypatch: pytest.MonkeyPatch):
    """Route requests.get by URL substring. Unrouted URLs fail the test."""

    def _install(routes: dict[str, FakeResponse | Exception]) -> list[dict[str, Any]]:
        calls: list[dict[str, Any]] = []

        def _fake_get(url: str, **kwargs: Any) -> FakeResponse:
            calls.append({"url": url, **kwargs})
            for fragment, response in routes.items():
                if fragment in url:
                    if isinstance(response, Exception):
                        raise response
                    return response
            raise AssertionError(f"Unexpected HTTP call: {url}")

        monkeypatch.setattr(requests, "get", _fake_get)
        return calls

    return _install


def league_payload(league_id: int = 39, name: str = "Premier League", country: str = "England",
                   seasons: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    if seasons is None:
        seasons = [
            {"year": 2024, "current": False, "coverage": {"top_scorers": True}},
            {"year": 2025, "current": True, "coverage": {"top_scorers": True}},
        ]
    return {"league": {"id": league_id, "name": name, "type": "League"}, "country": {"name": country},
            "seasons": seasons}


def af_ok(response: list[dict[str, Any]]) -> FakeResponse:
    return FakeResponse({"errors": [], "results": len(response), "response": response})


AF_SCORERS = [
    {"player": {"id": 1100, "name": "Player One", "nationality": "Norway", "age": 26, "photo": "https://img/1.png"},
     "statistics": [{"team": {"id": 50, "name": "Club Blue"},
                     "games": {"appearences": 10, "minutes": 890, "position": "Attacker"},
                     "goals": {"total": 9, "assists": None},
                     "penalty": {"scored": 2}}]},
    {"player": {"id": 2200, "name": "Player Two", "nationality": "Sweden", "age": 27},
     "statistics": [{"team": {"id": 40, "name": "Club Red"},
                     "games": {"appearences": 9, "minutes": 750, "position": "Attacker"},
                     "goals": {"total": 7, "assists": 1},
                     "penalty": {"scored": 0}}]},
]

SS_PAYLOAD = {
    "sport": "football",
    "competition": "English Premier League",
    "stat_type": "goals",
    "scorers": [
        {"rank": 1, "player": "Player One", "player_slug": "player-one", "team": "Club Blue",
         "goals": 9, "assists": 0, "matches": 10, "rating": 3000, "minutes": 890},
        {"rank": 2, "player": "Player Two", "player_slug": "player-two", "team": "Club Red",
         "goals": 7, "assists": 0, "matches": 9, "rating": 2900, "minutes": 750},
        {"rank": 3, "player": "Player Three", "player_slug": "player-three", "team": "Club Green",
         "goals": 6, "assists": 2, "matches": 10, "rating": 2800, "minutes": 800},
    ],
}


# 1. API-Football happy path ------------------------------------------------

def test_api_football_success_resolves_league_and_maps_scorers(monkeypatch, http_routes) -> None:
    monkeypatch.setenv("API_FOOTBALL_KEY", API_KEY)
    calls = http_routes({AF_LEAGUES: af_ok([league_payload()]), AF_TOPSCORERS: af_ok(AF_SCORERS)})

    result = top_scorers(competition="Premier League", season=2025, limit=1, country="England")

    assert result["status"] == "success"
    assert calls[0]["params"] == {"name": "Premier League", "country": "England"}
    assert calls[0]["headers"] == {"x-apisports-key": API_KEY}
    assert calls[1]["params"] == {"league": 39, "season": 2025}
    assert all(call["timeout"] for call in calls)
    assert not any("sportscore" in call["url"] for call in calls)

    assert result["competition"] == {"id": 39, "name": "Premier League", "country": "England", "slug": None}
    assert result["season"] == {"requested": 2025, "actual": 2025, "verified": True}
    assert result["provider"]["name"] == "API-Football"
    assert result["provider"]["fallback_used"] is False
    assert result["attribution"] is None
    assert result["count"] == 1  # limit applied locally: API returned 2 rows
    scorer = result["scorers"][0]
    assert scorer["rank"] == 1
    assert scorer["player"] == "Player One"
    assert scorer["team"] == "Club Blue"
    assert scorer["goals"] == 9
    assert scorer["assists"] is None  # missing stat stays None, never 0
    assert scorer["penalties"] == 2
    assert scorer["appearances"] == 10


def test_api_football_without_season_uses_current_season(monkeypatch, http_routes) -> None:
    monkeypatch.setenv("API_FOOTBALL_KEY", API_KEY)
    calls = http_routes({AF_LEAGUES: af_ok([league_payload()]), AF_TOPSCORERS: af_ok(AF_SCORERS)})

    result = top_scorers(competition="Premier League", country="England")

    assert calls[1]["params"]["season"] == 2025
    assert result["season"] == {"requested": None, "actual": 2025, "verified": True}
    assert result["count"] == 2


def test_season_string_2025_26_is_parsed_as_start_year(monkeypatch, http_routes) -> None:
    monkeypatch.setenv("API_FOOTBALL_KEY", API_KEY)
    calls = http_routes({AF_LEAGUES: af_ok([league_payload()]), AF_TOPSCORERS: af_ok(AF_SCORERS)})

    result = top_scorers(competition="Premier League", season="2025/26", country="England")

    assert result["status"] == "success"
    assert calls[1]["params"]["season"] == 2025


# 2. API-Football failures trigger fallback ---------------------------------

def test_missing_key_falls_back_to_sportscore_without_calling_api_football(http_routes) -> None:
    calls = http_routes({SS_TOPSCORERS: FakeResponse(SS_PAYLOAD)})

    result = top_scorers(competition="Premier League", limit=2, country="England")

    assert result["status"] == "success"
    assert len(calls) == 1
    assert calls[0]["params"] == {"sport": "football", "slug": "english-premier-league", "limit": 20, "stat": "goals"}
    assert result["attempts"][0]["reason"] == "missing_api_key"
    assert result["provider"]["fallback_reason"] == "missing_api_key"


@pytest.mark.parametrize("status_code, reason", [(403, "auth_error"), (401, "auth_error"), (429, "rate_limited")])
def test_api_football_http_errors_trigger_fallback_without_retry(monkeypatch, http_routes, status_code, reason) -> None:
    monkeypatch.setenv("API_FOOTBALL_KEY", API_KEY)
    calls = http_routes({
        AF_LEAGUES: FakeResponse({"errors": {"token": "x"}, "response": []}, status_code=status_code),
        SS_TOPSCORERS: FakeResponse(SS_PAYLOAD),
    })

    result = top_scorers(competition="Premier League", country="England")

    assert result["status"] == "success"
    assert result["provider"]["name"] == "SportScore"
    assert result["attempts"][0] == {"provider": "API-Football", "status": "failed", "reason": reason,
                                     "message": result["attempts"][0]["message"], "http_status": status_code}
    assert sum(1 for call in calls if "api-sports" in call["url"]) == 1  # no retry loop on quota/auth errors


def test_api_football_plan_error_in_http_200_body_is_detected(monkeypatch, http_routes) -> None:
    monkeypatch.setenv("API_FOOTBALL_KEY", API_KEY)
    http_routes({
        AF_LEAGUES: af_ok([league_payload()]),
        AF_TOPSCORERS: FakeResponse({"errors": {"plan": "Free plans do not have access to this season."},
                                     "response": []}),
        SS_TOPSCORERS: FakeResponse(SS_PAYLOAD),
    })

    # 2025 is the current season per API-Football, so SportScore's current leaderboard may answer it.
    result = top_scorers(competition="Premier League", season=2025, country="England")

    assert result["attempts"][0]["reason"] == "plan_restriction"
    assert result["provider"]["name"] == "SportScore"
    assert result["season"]["requested"] == 2025
    assert result["season"]["actual"] is None
    assert result["season"]["verified"] is False


# 3. SportScore fallback mapping --------------------------------------------

def test_sportscore_fallback_maps_stats_and_sets_attribution(http_routes) -> None:
    http_routes({SS_TOPSCORERS: FakeResponse(SS_PAYLOAD)})

    result = top_scorers(competition="EPL", limit=3)

    assert result["provider"] == {"name": "SportScore", "fallback_used": True, "source_url": "https://sportscore.com/",
                                  "fallback_reason": "missing_api_key"}
    assert result["attribution"]["text"] == "Powered by SportScore"
    assert result["attribution"]["url"] == "https://sportscore.com/"
    assert 'rel="dofollow"' in result["attribution"]["html"]
    assert result["competition"]["slug"] == "english-premier-league"
    assert result["competition"]["country"] == "England"
    assert [s["rank"] for s in result["scorers"]] == [1, 2, 3]  # provider order preserved
    third = result["scorers"][2]
    assert (third["player"], third["team"], third["goals"], third["assists"]) == ("Player Three", "Club Green", 6, 2)
    assert third["appearances"] == 10 and third["minutes"] == 800
    assert third["penalties"] is None and third["nationality"] is None  # not provided -> None, not 0


def test_sportscore_unlisted_competition_resolved_by_exact_search_match(http_routes) -> None:
    search = FakeResponse({"competitions": [
        {"name": "Laliga Hope Cup", "slug": "laliga-hope-cup", "url": "/football/competition/spain/laliga-hope-cup/a/"},
        {"name": "Spanish La Liga", "slug": "spanish-la-liga", "url": "/football/competition/spain/spanish-la-liga/b/"},
        {"name": "Mexican La Liga", "slug": "mexican-la-liga", "url": "/football/competition/mexico/mexican-la-liga/c/"},
    ]})
    calls = http_routes({SS_SEARCH: search, SS_TOPSCORERS: FakeResponse(SS_PAYLOAD)})

    result = top_scorers(competition="La Liga", country="Spain")

    assert result["status"] == "success"
    assert calls[1]["params"]["slug"] == "spanish-la-liga"
    assert result["provider"]["source_url"].endswith("/spain/spanish-la-liga/b/")


def test_sportscore_unknown_competition_without_country_is_not_guessed(http_routes) -> None:
    search = FakeResponse({"competitions": [
        {"name": "Armenian Premier League", "slug": "armenian-premier-league",
         "url": "/football/competition/armenia/armenian-premier-league/x/"},
    ]})
    calls = http_routes({SS_SEARCH: search})

    result = top_scorers(competition="Premier League")

    assert result["status"] == "error"
    assert result["error"] == "data_unavailable"
    assert result["attempts"][1]["reason"] == "competition_not_found"
    assert not any(SS_TOPSCORERS in call["url"] for call in calls)


# 4. Historical season protection -------------------------------------------

def test_historical_season_is_not_replaced_by_current_sportscore_data(http_routes) -> None:
    calls = http_routes({SS_TOPSCORERS: FakeResponse(SS_PAYLOAD)})

    result = top_scorers(competition="Premier League", season=2022, country="England")

    assert result["status"] == "error"
    assert result["error"] == "data_unavailable"
    assert "scorers" not in result
    assert result["attempts"][1]["provider"] == "SportScore"
    assert result["attempts"][1]["reason"] == "season_unverifiable"
    assert calls == []  # SportScore was never queried for a season it cannot verify


def test_unsupported_season_on_api_football_does_not_fall_back_to_current_data(monkeypatch, http_routes) -> None:
    monkeypatch.setenv("API_FOOTBALL_KEY", API_KEY)
    calls = http_routes({AF_LEAGUES: af_ok([league_payload()]), SS_TOPSCORERS: FakeResponse(SS_PAYLOAD)})

    result = top_scorers(competition="Premier League", season=2019, country="England")

    assert result["error"] == "data_unavailable"
    assert [a["reason"] for a in result["attempts"]] == ["unsupported_season", "season_unverifiable"]
    assert not any(SS_TOPSCORERS in call["url"] for call in calls)


# 5. Both providers unavailable ---------------------------------------------

def test_both_providers_fail_returns_structured_error_without_leaking_key(monkeypatch, http_routes) -> None:
    monkeypatch.setenv("API_FOOTBALL_KEY", API_KEY)
    http_routes({
        AF_LEAGUES: FakeResponse({}, status_code=500),
        SS_TOPSCORERS: requests.Timeout(f"timed out, key={API_KEY}"),
    })

    result = top_scorers(competition="Premier League", country="England")

    assert result["status"] == "error"
    assert result["error"] == "data_unavailable"
    assert [(a["provider"], a["reason"]) for a in result["attempts"]] == [
        ("API-Football", "server_error"), ("SportScore", "timeout")]
    assert API_KEY not in json.dumps(result)


def test_invalid_json_from_provider_is_reported(http_routes) -> None:
    http_routes({SS_TOPSCORERS: BadJsonResponse()})

    result = top_scorers(competition="Champions League")

    assert result["error"] == "data_unavailable"
    assert result["attempts"][1]["reason"] == "invalid_json"


# Input validation, ambiguity, cache ----------------------------------------

@pytest.mark.parametrize("kwargs", [
    {"competition": ""},
    {"competition": "   "},
    {"competition": None},
    {"competition": "Premier League", "limit": 0},
    {"competition": "Premier League", "limit": 21},
    {"competition": "Premier League", "limit": "ten"},
    {"competition": "Premier League", "season": 99},
    {"competition": "Premier League", "season": "last season"},
    {"competition": "Premier League", "country": 123},
])
def test_invalid_input_is_rejected_before_any_request(monkeypatch, http_routes, kwargs) -> None:
    monkeypatch.setenv("API_FOOTBALL_KEY", API_KEY)
    calls = http_routes({})

    result = top_scorers(**kwargs)

    assert result["status"] == "error"
    assert result["error"] == "invalid_input"
    assert calls == []


def test_ambiguous_competition_returns_candidates_and_stops(monkeypatch, http_routes) -> None:
    monkeypatch.setenv("API_FOOTBALL_KEY", API_KEY)
    calls = http_routes({AF_LEAGUES: af_ok([
        league_payload(39, "Premier League", "England"),
        league_payload(333, "Premier League", "Ukraine"),
    ])})

    result = top_scorers(competition="Premier League")

    assert result["error"] == "ambiguous_competition"
    assert {c["country"] for c in result["candidates"]} == {"England", "Ukraine"}
    assert len(calls) == 1  # no top-scorer request and no fallback with a guessed league


def test_successful_responses_are_cached(monkeypatch, http_routes) -> None:
    monkeypatch.setenv("API_FOOTBALL_KEY", API_KEY)
    calls = http_routes({AF_LEAGUES: af_ok([league_payload()]), AF_TOPSCORERS: af_ok(AF_SCORERS)})

    first = top_scorers(competition="Premier League", country="England", limit=2)
    second = top_scorers(competition="Premier League", country="England", limit=1)

    assert len(calls) == 2  # second call served from cache (free plan: 100 req/day)
    assert first["count"] == 2 and second["count"] == 1
