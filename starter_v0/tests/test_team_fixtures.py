"""Unit tests for the team_fixtures tool (offline: every HTTP call is mocked).

Payload shapes mirror real responses captured on 2026-11-11:
- /teams?search=Arsenal -> 25 teams, 3 named exactly "Arsenal" (England, Guadeloupe national team, Belarus)
- /fixtures?team=&season= -> {"response": [{fixture: {id, date, timestamp, status: {short}}, league: {name, round},
  teams: {home: {id, name}, away: {id, name}}, goals: {home, away}, score: {penalty: {home, away}}}]}
- Free plan: `last` / `next` params and seasons outside 2022-2024 -> HTTP 200 + {"errors": {"plan": ...}}
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

team_fixtures = TOOL_FUNCTIONS["team_fixtures"]
football_stats = TOOL_FUNCTIONS["football_stats"]

API_KEY = "secret-test-key-123"
AF_TEAMS = "v3.football.api-sports.io/teams"
AF_LEAGUES = "v3.football.api-sports.io/leagues"
AF_FIXTURES = "v3.football.api-sports.io/fixtures"

Route = FakeResponse | Exception | Callable[[dict[str, Any]], FakeResponse]


@pytest.fixture(autouse=True)
def fresh_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """No cache carry-over between tests (the cache is shared with top_scorers); key set by default."""
    shared_module.clear_cache()
    monkeypatch.setenv("API_FOOTBALL_KEY", API_KEY)


@pytest.fixture
def http_routes(monkeypatch: pytest.MonkeyPatch):
    """Route requests.get by URL substring; a route may be a callable taking the query params."""

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


def team(team_id: int, name: str, country: str, national: bool = False) -> dict[str, Any]:
    return {"team": {"id": team_id, "name": name, "country": country, "national": national}, "venue": {}}


TEAMS_SEARCH = af_ok([
    team(42, "Club Cannon", "England"),
    team(459, "Club Cannon Sarandi", "Argentina"),
    team(4403, "Club Cannon", "Guadeloupe", national=True),
    team(9419, "Club Cannon", "Belarus"),
])

LEAGUE = {"league": {"id": 39, "name": "Premier League", "type": "League"}, "country": {"name": "England"},
          "seasons": [{"year": 2024, "current": False, "coverage": {}}]}
UCL = {"league": {"id": 2, "name": "UEFA Champions League", "type": "Cup"}, "country": {"name": "World"},
       "seasons": [{"year": 2024, "current": False, "coverage": {}}]}


def fixture(fid: int, ts: int, home: tuple[int, str], away: tuple[int, str], goals: tuple[Any, Any],
            status: str = "FT", competition: str = "Premier League", penalty: tuple[Any, Any] = (None, None)) -> dict:
    return {
        "fixture": {"id": fid, "date": f"2025-01-{fid:02d}T15:00:00+00:00", "timestamp": ts, "status": {"short": status}},
        "league": {"id": 39, "name": competition, "round": f"Regular Season - {fid}"},
        "teams": {"home": {"id": home[0], "name": home[1]}, "away": {"id": away[0], "name": away[1]}},
        "goals": {"home": goals[0], "away": goals[1]},
        "score": {"penalty": {"home": penalty[0], "away": penalty[1]}},
    }


CANNON, RED, BLUE, GULL = (42, "Club Cannon"), (40, "Club Red"), (50, "Club Blue"), (51, "Club Gull")
# Deliberately out of order: the tool must sort by timestamp.
SEASON = [
    fixture(3, 300, RED, CANNON, (2, 2)),
    fixture(1, 100, CANNON, BLUE, (2, 0)),
    fixture(4, 400, CANNON, GULL, (1, 2)),
    fixture(2, 200, BLUE, CANNON, (0, 1)),
    fixture(5, 500, CANNON, RED, (3, 1)),
]


def urls(calls: list[dict[str, Any]], fragment: str) -> list[dict[str, Any]]:
    return [c for c in calls if fragment in c["url"]]


# ---------------------------------------------------------------- happy path

def test_last_n_finished_matches_oldest_first(http_routes) -> None:
    calls = http_routes({AF_TEAMS: TEAMS_SEARCH, AF_LEAGUES: af_ok([LEAGUE]), AF_FIXTURES: af_ok(SEASON)})

    result = team_fixtures("Club Cannon", season="2024/25", competition="Premier League", country="England", last_n=3)

    assert result["status"] == "success"
    assert result["team"] == {"id": 42, "name": "Club Cannon", "country": "England"}
    assert result["competition"] == {"id": 39, "name": "Premier League", "country": "England"}
    assert result["season"] == {"requested": 2024, "actual": 2024, "verified": True}
    assert result["order"] == "oldest_first" and result["count"] == 3
    assert [m["fixture_id"] for m in result["matches"]] == [3, 4, 5]
    assert [m["venue"] for m in result["matches"]] == ["away", "home", "home"]
    assert result["matches"][0] == {
        "fixture_id": 3, "date": "2025-01-03T15:00:00+00:00", "competition": "Premier League",
        "round": "Regular Season - 3", "home_team": "Club Red", "away_team": "Club Cannon",
        "home_score": 2, "away_score": 2, "venue": "away", "decided_by": "regular_time", "penalty_shootout": None}
    assert result["warning"] is None
    fixtures_call = urls(calls, AF_FIXTURES)[0]
    assert fixtures_call["params"] == {"team": 42, "season": 2024, "league": 39}
    assert fixtures_call["headers"] == {"x-apisports-key": API_KEY}
    assert "last" not in fixtures_call["params"] and "next" not in fixtures_call["params"]  # blocked on Free plan
    assert urls(calls, AF_TEAMS)[0]["params"] == {"search": "club cannon"}


def test_output_chains_into_football_stats(http_routes) -> None:
    http_routes({AF_TEAMS: TEAMS_SEARCH, AF_LEAGUES: af_ok([LEAGUE]), AF_FIXTURES: af_ok(SEASON)})
    fixtures = team_fixtures("Club Cannon", season=2024, competition="Premier League", country="England", last_n=5)

    stats = football_stats(team_a=fixtures["team"]["name"], matches=fixtures["matches"], last_n=5)

    assert stats["status"] == "success"
    assert stats["team_a"]["form"] == "W-W-D-L-W"  # 2-0, 1-0 away, 2-2 away, 1-2, 3-1
    assert stats["team_a"]["goals_scored"] == 9 and stats["team_a"]["goals_conceded"] == 5


def test_unfinished_and_scoreless_fixtures_are_skipped(http_routes) -> None:
    season = [SEASON[1], SEASON[3]] + [  # fixtures 1 and 2
        fixture(6, 600, CANNON, RED, (None, None), status="NS"),
        fixture(7, 700, CANNON, BLUE, (None, None), status="PST"),
        fixture(8, 800, GULL, CANNON, (None, 1), status="FT"),  # broken provider row
    ]
    http_routes({AF_TEAMS: TEAMS_SEARCH, AF_FIXTURES: af_ok(season)})

    result = team_fixtures("Club Cannon", season=2024, country="England", last_n=5)

    assert [m["fixture_id"] for m in result["matches"]] == [1, 2]
    assert result["fixtures_in_season"] == 5 and result["finished_in_season"] == 2
    assert "Only 2 finished matches" in result["warning"]


def test_penalty_shootout_is_kept_out_of_the_score(http_routes) -> None:
    season = [
        fixture(1, 100, CANNON, RED, (1, 1), status="PEN", competition="FA Cup", penalty=(3, 5)),
        fixture(2, 200, BLUE, CANNON, (1, 2), status="AET", competition="League Cup"),
    ]
    http_routes({AF_TEAMS: TEAMS_SEARCH, AF_FIXTURES: af_ok(season)})

    first, second = team_fixtures("Club Cannon", season=2024, country="England")["matches"]

    assert (first["home_score"], first["away_score"]) == (1, 1)
    assert first["decided_by"] == "penalties" and first["penalty_shootout"] == {"home": 3, "away": 5}
    assert second["decided_by"] == "extra_time" and second["penalty_shootout"] is None


def test_without_competition_all_competitions_are_included_with_warning(http_routes) -> None:
    calls = http_routes({AF_TEAMS: TEAMS_SEARCH, AF_FIXTURES: af_ok(SEASON)})

    result = team_fixtures("Club Cannon", season=2024, country="England")

    assert result["competition"] is None
    assert "friendlies" in result["warning"]
    assert not urls(calls, AF_LEAGUES)
    assert urls(calls, AF_FIXTURES)[0]["params"] == {"team": 42, "season": 2024}


def test_numeric_team_id_skips_search_and_takes_name_from_fixtures(http_routes) -> None:
    calls = http_routes({AF_FIXTURES: af_ok(SEASON)})

    result = team_fixtures("42", season=2024)

    assert result["team"]["id"] == 42 and result["team"]["name"] == "Club Cannon"
    assert not urls(calls, AF_TEAMS)


def test_accented_name_matches_and_search_term_is_sanitized(http_routes) -> None:
    calls = http_routes({AF_TEAMS: af_ok([team(530, "Atletico Madrid", "Spain")]), AF_FIXTURES: af_ok([])})

    result = team_fixtures("Atlético Madrid", season=2024)
    team_fixtures("Brighton & Hove", season=2024)

    assert result["status"] == "success" and result["team"]["id"] == 530
    assert result["count"] == 0 and "No finished matches" in result["warning"]
    searches = [c["params"]["search"] for c in urls(calls, AF_TEAMS)]
    assert searches == ["atletico madrid", "brighton hove"]  # API accepts letters, digits, spaces only


def test_competition_outside_team_country_is_retried_without_country(http_routes) -> None:
    def leagues(params: dict[str, Any]) -> FakeResponse:
        return af_ok([] if "country" in params else [UCL])

    calls = http_routes({AF_TEAMS: TEAMS_SEARCH, AF_LEAGUES: leagues, AF_FIXTURES: af_ok(SEASON)})

    result = team_fixtures("Club Cannon", season=2024, competition="UEFA Champions League", country="England")

    assert result["competition"]["id"] == 2
    league_params = [c["params"] for c in urls(calls, AF_LEAGUES)]
    assert league_params[0] == {"name": "UEFA Champions League", "country": "England"}
    assert league_params[-1] == {"name": "UEFA Champions League"}
    assert urls(calls, AF_FIXTURES)[0]["params"]["league"] == 2


# ---------------------------------------------------------------- no guessing

def test_several_exact_team_matches_return_candidates(http_routes) -> None:
    calls = http_routes({AF_TEAMS: TEAMS_SEARCH})

    result = team_fixtures("Club Cannon", season=2024)

    assert result["status"] == "error" and result["error"] == "ambiguous_team"
    assert {c["country"] for c in result["candidates"]} == {"England", "Guadeloupe", "Belarus"}
    assert not urls(calls, AF_FIXTURES)


def test_only_partial_matches_are_listed_not_picked(http_routes) -> None:
    http_routes({AF_TEAMS: af_ok([team(459, "Club Cannon Sarandi", "Argentina")])})

    result = team_fixtures("Club Cannon", season=2024, country="Argentina")

    assert result["error"] == "ambiguous_team"
    assert [c["name"] for c in result["candidates"]] == ["Club Cannon Sarandi"]


def test_unknown_team_is_data_unavailable(http_routes) -> None:
    http_routes({AF_TEAMS: af_ok([])})

    result = team_fixtures("Nobody FC", season=2024)

    assert result["error"] == "data_unavailable"
    assert result["attempts"][0]["reason"] == "team_not_found"


def test_ambiguous_competition_returns_candidates(http_routes) -> None:
    other = {"league": {"id": 169, "name": "Premier League", "type": "League"}, "country": {"name": "Ukraine"},
             "seasons": []}
    http_routes({AF_FIXTURES: af_ok(SEASON), AF_LEAGUES: af_ok([LEAGUE, other])})

    result = team_fixtures("42", season=2024, competition="Premier League")

    assert result["error"] == "ambiguous_competition"
    assert len(result["candidates"]) == 2


# ---------------------------------------------------------------- provider errors

def test_free_plan_season_is_reported_not_invented(http_routes) -> None:
    plan = FakeResponse({"errors": {"plan": "Free plans do not have access to this season, try from 2022 to 2024."},
                         "results": 0, "response": []})
    http_routes({AF_TEAMS: TEAMS_SEARCH, AF_FIXTURES: plan})

    result = team_fixtures("Club Cannon", season=2025, country="England")

    assert result["status"] == "error" and result["error"] == "data_unavailable"
    assert result["attempts"][0]["reason"] == "plan_restriction"
    assert "2022 to 2024" in result["message"]
    assert "matches" not in result


def test_missing_key_makes_no_request(http_routes, monkeypatch) -> None:
    monkeypatch.delenv("API_FOOTBALL_KEY")
    calls = http_routes({})

    result = team_fixtures("Club Cannon", season=2024)

    assert result["error"] == "data_unavailable"
    assert result["attempts"][0]["reason"] == "missing_api_key"
    assert calls == []


@pytest.mark.parametrize("response, reason", [
    (FakeResponse({}, status_code=429), "rate_limited"),
    (FakeResponse({}, status_code=500), "server_error"),
    (requests.Timeout("slow"), "timeout"),
])
def test_http_failures_are_structured_and_not_retried(http_routes, response, reason) -> None:
    calls = http_routes({AF_TEAMS: TEAMS_SEARCH, AF_FIXTURES: response})

    result = team_fixtures("Club Cannon", season=2024, country="England")

    assert result["error"] == "data_unavailable" and result["attempts"][0]["reason"] == reason
    assert len(urls(calls, AF_FIXTURES)) == 1
    assert API_KEY not in json.dumps(result)


def test_connection_error_message_does_not_leak_key(http_routes) -> None:
    http_routes({AF_TEAMS: requests.ConnectionError(f"refused for key={API_KEY}")})

    result = team_fixtures("Club Cannon", season=2024)

    assert result["attempts"][0]["reason"] == "connection_error"
    assert API_KEY not in json.dumps(result)


# ---------------------------------------------------------------- input / cache

@pytest.mark.parametrize("kwargs", [
    {"team": "", "season": 2024},
    {"team": None, "season": 2024},
    {"team": "Club Cannon"},                       # season is required
    {"team": "Club Cannon", "season": "recent"},
    {"team": "Club Cannon", "season": 2024, "last_n": 0},
    {"team": "Club Cannon", "season": 2024, "last_n": 51},
    {"team": "Club Cannon", "season": 2024, "last_n": "five"},
    {"team": "Club Cannon", "season": 2024, "last_n": True},
    {"team": "Club Cannon", "season": 2024, "competition": 39},
    {"team": "Club Cannon", "season": 2024, "country": 1},
])
def test_invalid_input_is_rejected_before_any_request(http_routes, kwargs) -> None:
    calls = http_routes({})

    result = team_fixtures(**kwargs)

    assert result["status"] == "error" and result["error"] == "invalid_input"
    assert calls == []


def test_short_team_name_is_rejected_by_provider_rules(http_routes) -> None:
    calls = http_routes({})

    result = team_fixtures("FC", season=2024)

    assert result["attempts"][0]["reason"] == "invalid_team_name"
    assert calls == []


def test_second_call_is_served_from_cache(http_routes) -> None:
    calls = http_routes({AF_TEAMS: TEAMS_SEARCH, AF_FIXTURES: af_ok(SEASON)})

    team_fixtures("Club Cannon", season=2024, country="England", last_n=2)
    again = team_fixtures("Club Cannon", season=2024, country="England", last_n=4)

    assert again["count"] == 4
    assert len(calls) == 2  # teams + fixtures, once each
