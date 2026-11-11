"""Unit tests for the standings tool (offline: every HTTP call is mocked).

Payload shapes mirror real responses captured on 2026-11-11:
- API-Football /standings -> {"response": [{"league": {"standings": [[{rank, team, points, goalsDiff, form, all: {...}}]]}}]}
- API-Football season 2025 on the Free plan -> HTTP 200 + {"errors": {"plan": "Free plans do not have access ..."}}
- SportScore /api/widget/standings/ -> {"competition", "competition_slug", "tables": [{"group", "rows": [{pos, team, p, w, d, l, gf, ga, gd, pts, promo_name}]}]}
Team names below are fake.
"""
from __future__ import annotations

import json
from typing import Any, Callable

import pytest
import requests

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS
from tools.top_scorers import tool as shared_module

standings = TOOL_FUNCTIONS["standings"]

API_KEY = "secret-test-key-123"
AF_LEAGUES = "v3.football.api-sports.io/leagues"
AF_STANDINGS = "v3.football.api-sports.io/standings"
SS_STANDINGS = "sportscore.com/api/widget/standings/"
SS_SEARCH = "sportscore.com/api/v1/search/"

Route = FakeResponse | Exception | Callable[[dict[str, Any]], FakeResponse]


@pytest.fixture(autouse=True)
def fresh_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """No cache carry-over between tests (the cache is shared with top_scorers), no real key."""
    shared_module.clear_cache()
    monkeypatch.delenv("API_FOOTBALL_KEY", raising=False)


@pytest.fixture
def http_routes(monkeypatch: pytest.MonkeyPatch):
    """Route requests.get by URL substring. Unrouted URLs fail the test."""

    def _install(routes: dict[str, Route]) -> list[dict[str, Any]]:
        calls: list[dict[str, Any]] = []

        def _fake_get(url: str, **kwargs: Any) -> FakeResponse:
            calls.append({"url": url, **kwargs})
            for fragment, response in routes.items():
                if fragment in url:
                    if isinstance(response, Exception):
                        raise response
                    if callable(response) and not isinstance(response, FakeResponse):
                        return response(kwargs.get("params") or {})
                    return response
            raise AssertionError(f"Unexpected HTTP call: {url}")

        monkeypatch.setattr(requests, "get", _fake_get)
        return calls

    return _install


def af_ok(response: list[dict[str, Any]]) -> FakeResponse:
    return FakeResponse({"errors": [], "results": len(response), "response": response})


def league_payload(current: int = 2025, standings_coverage: bool = True) -> dict[str, Any]:
    return {"league": {"id": 39, "name": "Premier League", "type": "League"}, "country": {"name": "England"},
            "seasons": [{"year": year, "current": year == current, "coverage": {"standings": standings_coverage}}
                        for year in (2022, 2023, 2024, 2025)]}


def af_row(rank: int, team_id: int, name: str, points: int, **overrides: Any) -> dict[str, Any]:
    row = {"rank": rank, "team": {"id": team_id, "name": name}, "points": points, "goalsDiff": 10 - rank,
           "group": "Premier League", "form": "WWDLD", "description": "Champions League",
           "all": {"played": 38, "win": 20, "draw": 14 - rank, "lose": 4, "goals": {"for": 69, "against": 34}}}
    row.update(overrides)
    return row


def af_standings(tables: list[list[dict[str, Any]]]) -> FakeResponse:
    return af_ok([{"league": {"id": 39, "season": 2024, "standings": tables}}])


AF_TABLE = [af_row(1, 40, "Club Red", 84), af_row(2, 42, "Club Cannon", 74)]

SS_TABLE = FakeResponse({
    "sport": "football", "competition": "English Premier League", "competition_slug": "english-premier-league",
    "tables": [{"group": "", "rows": [
        {"pos": 1, "team": "Club Cannon", "team_slug": "club-cannon", "p": 10, "w": 9, "d": 0, "l": 1,
         "gf": 15, "ga": 5, "gd": 10, "pts": 27, "promo_name": "Champions League league stage"},
        {"pos": 2, "team": "Club Seagull", "team_slug": "club-seagull", "p": 10, "w": 7, "d": 1, "l": 2,
         "gf": 26, "ga": 7, "gd": 19, "pts": 22},
    ]}],
})

PLAN_ERROR = FakeResponse({"errors": {"plan": "Free plans do not have access to this season, try from 2022 to 2024."},
                           "results": 0, "response": []})


def urls(calls: list[dict[str, Any]], fragment: str) -> list[dict[str, Any]]:
    return [c for c in calls if fragment in c["url"]]


# ---------------------------------------------------------------- API-Football

def test_api_football_happy_path_maps_table(http_routes, monkeypatch) -> None:
    monkeypatch.setenv("API_FOOTBALL_KEY", API_KEY)
    calls = http_routes({AF_LEAGUES: af_ok([league_payload()]), AF_STANDINGS: af_standings([AF_TABLE])})

    result = standings("Premier League", season="2024/25", country="England")

    assert result["status"] == "success"
    assert result["season"] == {"requested": 2024, "actual": 2024, "verified": True}
    assert result["provider"]["name"] == "API-Football" and result["attribution"] is None
    assert result["competition"]["id"] == 39 and result["count"] == 2
    first = result["groups"][0]["rows"][0]
    assert first == {"rank": 1, "team_id": 40, "team": "Club Red", "played": 38, "win": 20, "draw": 13, "lose": 4,
                     "goals_for": 69, "goals_against": 34, "goal_diff": 9, "points": 84, "form": "WWDLD",
                     "description": "Champions League"}
    standings_call = urls(calls, AF_STANDINGS)[0]
    assert standings_call["params"] == {"league": 39, "season": 2024}
    assert standings_call["headers"] == {"x-apisports-key": API_KEY}
    assert urls(calls, AF_LEAGUES)[0]["params"] == {"name": "Premier League", "country": "England"}


def test_missing_provider_fields_stay_none_not_zero(http_routes, monkeypatch) -> None:
    monkeypatch.setenv("API_FOOTBALL_KEY", API_KEY)
    sparse = {"rank": 1, "team": {"id": 7, "name": "Club Sparse"}, "points": 3, "all": {}}
    http_routes({AF_LEAGUES: af_ok([league_payload()]), AF_STANDINGS: af_standings([[sparse]])})

    row = standings("Premier League", season=2024)["groups"][0]["rows"][0]

    assert row["points"] == 3
    for field in ("played", "win", "draw", "lose", "goals_for", "goals_against", "goal_diff", "form", "description"):
        assert row[field] is None, field


def test_several_groups_are_kept_separately(http_routes, monkeypatch) -> None:
    monkeypatch.setenv("API_FOOTBALL_KEY", API_KEY)
    group_a = [af_row(1, 1, "Club A1", 9, group="Group A"), af_row(2, 2, "Club A2", 6, group="Group A")]
    group_b = [af_row(1, 3, "Club B1", 7, group="Group B")]
    http_routes({AF_LEAGUES: af_ok([league_payload()]), AF_STANDINGS: af_standings([group_a, group_b])})

    result = standings("Premier League", season=2024)

    assert [g["group"] for g in result["groups"]] == ["Group A", "Group B"]
    assert result["count"] == 3


def test_empty_table_is_success_with_warning(http_routes, monkeypatch) -> None:
    monkeypatch.setenv("API_FOOTBALL_KEY", API_KEY)
    http_routes({AF_LEAGUES: af_ok([league_payload()]), AF_STANDINGS: af_ok([])})

    result = standings("Premier League", season=2024)

    assert result["status"] == "success" and result["count"] == 0 and result["warning"]


# ---------------------------------------------------------------- fallback

def test_missing_key_falls_back_to_sportscore(http_routes) -> None:
    calls = http_routes({SS_STANDINGS: SS_TABLE})

    result = standings("Premier League", country="England")

    assert result["status"] == "success"
    assert result["provider"]["name"] == "SportScore"
    assert result["provider"]["fallback_reason"] == "missing_api_key"
    assert result["attribution"]["text"] == "Powered by SportScore"
    assert result["season"]["verified"] is False and result["season"]["actual"] is None
    rows = result["groups"][0]["rows"]
    assert rows[0]["team"] == "Club Cannon" and rows[0]["points"] == 27
    assert rows[0]["form"] is None and rows[0]["team_id"] is None  # SportScore has no form / ids
    assert rows[1]["description"] is None
    assert not urls(calls, "api-sports.io")
    assert urls(calls, SS_STANDINGS)[0]["params"] == {"sport": "football", "slug": "english-premier-league"}


def test_free_plan_current_season_falls_back(http_routes, monkeypatch) -> None:
    monkeypatch.setenv("API_FOOTBALL_KEY", API_KEY)
    http_routes({AF_LEAGUES: af_ok([league_payload(current=2025)]), AF_STANDINGS: PLAN_ERROR, SS_STANDINGS: SS_TABLE})

    result = standings("Premier League", country="England")

    assert result["provider"]["name"] == "SportScore"
    assert result["provider"]["fallback_reason"] == "plan_restriction"
    assert "Free plans" in result["attempts"][0]["message"]


def test_requested_season_equal_to_current_is_accepted_on_sportscore(http_routes, monkeypatch) -> None:
    monkeypatch.setenv("API_FOOTBALL_KEY", API_KEY)
    http_routes({AF_LEAGUES: af_ok([league_payload(current=2025)]), AF_STANDINGS: PLAN_ERROR, SS_STANDINGS: SS_TABLE})

    result = standings("Premier League", season=2025, country="England")

    assert result["provider"]["name"] == "SportScore"
    assert "2025" in result["season"]["note"]


def test_rate_limit_is_not_retried(http_routes, monkeypatch) -> None:
    monkeypatch.setenv("API_FOOTBALL_KEY", API_KEY)
    calls = http_routes({AF_LEAGUES: af_ok([league_payload()]), AF_STANDINGS: FakeResponse({}, status_code=429),
                         SS_STANDINGS: SS_TABLE})

    result = standings("Premier League", season=2025, country="England")

    assert len(urls(calls, AF_STANDINGS)) == 1
    assert result["provider"]["fallback_reason"] == "rate_limited"


def test_no_standings_coverage_falls_back(http_routes, monkeypatch) -> None:
    monkeypatch.setenv("API_FOOTBALL_KEY", API_KEY)
    calls = http_routes({AF_LEAGUES: af_ok([league_payload(standings_coverage=False)]), SS_STANDINGS: SS_TABLE})

    result = standings("Premier League", country="England")

    assert result["provider"]["fallback_reason"] == "no_standings_coverage"
    assert not urls(calls, AF_STANDINGS)


def test_old_season_is_never_replaced_by_current_table(http_routes, monkeypatch) -> None:
    monkeypatch.setenv("API_FOOTBALL_KEY", API_KEY)
    calls = http_routes({AF_LEAGUES: af_ok([league_payload(current=2025)]),
                         AF_STANDINGS: FakeResponse({}, status_code=500), SS_STANDINGS: SS_TABLE})

    result = standings("Premier League", season=2022, country="England")

    assert result["status"] == "error" and result["error"] == "data_unavailable"
    assert [a["reason"] for a in result["attempts"]] == ["server_error", "season_unverifiable"]
    assert not urls(calls, SS_STANDINGS)


def test_both_providers_fail_without_leaking_key(http_routes, monkeypatch) -> None:
    monkeypatch.setenv("API_FOOTBALL_KEY", API_KEY)
    http_routes({AF_LEAGUES: FakeResponse({}, status_code=503),
                 SS_STANDINGS: requests.Timeout(f"timeout for key {API_KEY}")})

    result = standings("Premier League", country="England")

    assert result["status"] == "error" and result["error"] == "data_unavailable"
    assert [a["reason"] for a in result["attempts"]] == ["server_error", "timeout"]
    assert API_KEY not in json.dumps(result)


def test_sportscore_payload_without_tables_is_invalid(http_routes) -> None:
    http_routes({SS_STANDINGS: FakeResponse({"error": "No current season"})})

    result = standings("Premier League", country="England")

    assert result["error"] == "data_unavailable"
    assert result["attempts"][-1]["reason"] == "invalid_response"


# ---------------------------------------------------------------- no guessing / input / cache

def test_ambiguous_competition_returns_candidates_without_fallback(http_routes, monkeypatch) -> None:
    monkeypatch.setenv("API_FOOTBALL_KEY", API_KEY)
    other = {"league": {"id": 169, "name": "Premier League", "type": "League"}, "country": {"name": "Ukraine"},
             "seasons": []}
    calls = http_routes({AF_LEAGUES: af_ok([league_payload(), other])})

    result = standings("Premier League")

    assert result["error"] == "ambiguous_competition"
    assert {c["country"] for c in result["candidates"]} == {"England", "Ukraine"}
    assert not urls(calls, SS_STANDINGS) and not urls(calls, AF_STANDINGS)


@pytest.mark.parametrize("kwargs", [
    {"competition": ""},
    {"competition": None},
    {"competition": "   "},
    {"competition": "Premier League", "season": 99},
    {"competition": "Premier League", "season": "last year"},
    {"competition": "Premier League", "season": True},
    {"competition": "Premier League", "country": 123},
])
def test_invalid_input_is_rejected_before_any_request(http_routes, monkeypatch, kwargs) -> None:
    monkeypatch.setenv("API_FOOTBALL_KEY", API_KEY)
    calls = http_routes({})

    result = standings(**kwargs)

    assert result["status"] == "error" and result["error"] == "invalid_input"
    assert calls == []


def test_second_call_is_served_from_cache(http_routes, monkeypatch) -> None:
    monkeypatch.setenv("API_FOOTBALL_KEY", API_KEY)
    calls = http_routes({AF_LEAGUES: af_ok([league_payload()]), AF_STANDINGS: af_standings([AF_TABLE])})

    first = standings("Premier League", season=2024, country="England")
    second = standings("Premier League", season=2024, country="England")

    assert first["groups"] == second["groups"]
    assert len(calls) == 2  # leagues + standings, once each
