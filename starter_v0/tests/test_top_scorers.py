from __future__ import annotations

import importlib
from typing import Any

import pytest
import requests

from conftest import FakeResponse


top_scorers_module = importlib.import_module("tools.top_scorers.tool")


@pytest.fixture(autouse=True)
def clear_top_scorers_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(top_scorers_module, "_cache", {})


def install_http_responses(
    monkeypatch: pytest.MonkeyPatch,
    responses: list[FakeResponse | Exception],
) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    pending = iter(responses)

    def fake_get(url: str, **kwargs: Any) -> FakeResponse:
        calls.append({"url": url, **kwargs})
        response = next(pending)
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(requests, "get", fake_get)
    return calls


def api_league_response() -> FakeResponse:
    return FakeResponse({
        "response": [{
            "league": {"id": 39, "name": "Premier League"},
            "country": {"name": "England"},
            "seasons": [{
                "year": 2025,
                "current": False,
                "coverage": {"top_scorers": True},
            }],
        }]
    })


def api_scorers_response() -> FakeResponse:
    return FakeResponse({
        "response": [{
            "player": {
                "id": 7,
                "name": "Example Player",
                "nationality": "England",
                "age": 25,
                "photo": "https://example.test/player.png",
            },
            "statistics": [{
                "team": {"id": 70, "name": "Example FC"},
                "games": {"appearences": 20, "minutes": 1600, "position": "Attacker"},
                "goals": {"total": 15, "assists": 5},
                "penalty": {"scored": 2},
            }],
        }]
    })


def sportscore_goals_response(*, season: int | None = None) -> FakeResponse:
    payload: dict[str, Any] = {
        "competition": {"name": "Premier League"},
        "topscorers": [{
            "rank": 1,
            "player": {
                "id": 7,
                "name": "Example Player",
                "nationality": "England",
                "age": 25,
                "position": "Forward",
                "photo": "https://example.test/player.png",
            },
            "team": {"id": 70, "name": "Example FC"},
            "goals": 15,
            "assists": 3,
            "penalties": 2,
            "appearances": 20,
            "minutes": 1600,
        }],
    }
    if season is not None:
        payload["season"] = season
    return FakeResponse(payload)


def sportscore_assists_response() -> FakeResponse:
    return FakeResponse({
        "topscorers": [{
            "player": {"id": 7, "name": "Example Player"},
            "value": 6,
        }]
    })


def test_api_football_success_resolves_and_normalizes_player(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_FOOTBALL_KEY", "test-secret")
    calls = install_http_responses(
        monkeypatch,
        [api_league_response(), api_scorers_response()],
    )

    result = top_scorers_module.top_scorers("Premier League", season=2025, country="England", limit=1)

    assert result["status"] == "success"
    assert result["provider"]["name"] == "API-Football"
    assert result["provider"]["fallback_used"] is False
    assert result["competition"]["id"] == 39
    assert result["season"] == {"requested": 2025, "actual": 2025, "verified": True}
    assert calls[0]["params"]["search"] == "Premier League"
    assert calls[0]["params"]["season"] == 2025
    assert calls[1]["params"] == {"league": 39, "season": 2025}
    assert calls[1]["headers"]["x-apisports-key"] == "test-secret"
    assert result["scorers"][0] == {
        "rank": 1,
        "player_id": 7,
        "player": "Example Player",
        "nationality": "England",
        "age": 25,
        "position": "Attacker",
        "photo_url": "https://example.test/player.png",
        "team_id": 70,
        "team": "Example FC",
        "goals": 15,
        "assists": 5,
        "penalties": 2,
        "appearances": 20,
        "minutes": 1600,
    }


@pytest.mark.parametrize(
    ("api_key", "primary_response", "expected_error"),
    [
        (None, None, "missing_api_key"),
        ("bad-key", FakeResponse(status_code=403), "forbidden"),
        ("bad-key", FakeResponse(status_code=429), "rate_limited"),
    ],
)
def test_api_football_access_failures_trigger_sportscore_fallback(
    monkeypatch: pytest.MonkeyPatch,
    api_key: str | None,
    primary_response: FakeResponse | None,
    expected_error: str,
) -> None:
    if api_key:
        monkeypatch.setenv("API_FOOTBALL_KEY", api_key)
    responses = []
    if primary_response is not None:
        responses.append(primary_response)
    responses.extend([sportscore_goals_response(), sportscore_assists_response()])
    calls = install_http_responses(monkeypatch, responses)

    result = top_scorers_module.top_scorers("Premier League", limit=1)

    assert result["status"] == "success"
    assert result["provider"]["name"] == "SportScore"
    assert result["provider"]["fallback_used"] is True
    assert result["provider_errors"][0]["error"] == expected_error
    assert result["provider"]["attribution"]["url"] == "https://sportscore.com/"
    assert result["provider"]["attribution"]["rel"] == "dofollow"
    assert "Powered by SportScore" in result["provider"]["attribution"]["html"]
    assert result["season"] == {"requested": None, "actual": None, "verified": False}
    fallback_calls = calls[1:] if api_key else calls
    assert all(call["params"]["slug"] == "premier-league" for call in fallback_calls)
    assert fallback_calls[0]["params"] == {
        "sport": "football",
        "slug": "premier-league",
        "limit": 1,
        "stat": "goals",
    }
    assert fallback_calls[1]["params"]["stat"] == "assists"
    assert result["scorers"][0]["assists"] == 6


def test_sportscore_without_verifiable_historical_season_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = install_http_responses(monkeypatch, [sportscore_goals_response()])

    result = top_scorers_module.top_scorers("Premier League", season=2018)

    assert result["status"] == "error"
    assert result["error"] == "unsupported_season"
    assert result["provider_errors"][1]["error"] == "unsupported_season"
    assert "scorers" not in result
    assert len(calls) == 1
    assert calls[0]["params"]["stat"] == "goals"


def test_both_providers_unavailable_return_safe_structured_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = "never-return-this-key"
    monkeypatch.setenv("API_FOOTBALL_KEY", secret)
    install_http_responses(
        monkeypatch,
        [FakeResponse(status_code=500), FakeResponse(status_code=503)],
    )

    result = top_scorers_module.top_scorers("Premier League")

    assert result["status"] == "error"
    assert result["error"] == "data_unavailable"
    assert [item["provider"] for item in result["provider_errors"]] == ["API-Football", "SportScore"]
    assert [item["error"] for item in result["provider_errors"]] == [
        "provider_unavailable",
        "provider_unavailable",
    ]
    assert secret not in repr(result)


def test_ambiguous_api_football_competition_returns_candidates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("API_FOOTBALL_KEY", "test-secret")
    install_http_responses(monkeypatch, [FakeResponse({
        "response": [
            {
                "league": {"id": 39, "name": "Premier League"},
                "country": {"name": "England"},
                "seasons": [{"year": 2025, "current": True, "coverage": {"top_scorers": True}}],
            },
            {
                "league": {"id": 100, "name": "Premier League"},
                "country": {"name": "Another Country"},
                "seasons": [{"year": 2025, "current": True, "coverage": {"top_scorers": True}}],
            },
        ]
    })])

    result = top_scorers_module.top_scorers("Premier League")

    assert result["status"] == "needs_clarification"
    assert result["error"] == "ambiguous_competition"
    assert {candidate["id"] for candidate in result["candidates"]} == {39, 100}


def test_invalid_inputs_are_rejected_without_network_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = install_http_responses(monkeypatch, [])

    result = top_scorers_module.top_scorers("Premier League", season=2025, limit=21)

    assert result["error"] == "invalid_input"
    assert calls == []


def test_scorer_limit_is_applied_and_successful_response_is_cached(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("API_FOOTBALL_KEY", "test-secret")
    calls = install_http_responses(
        monkeypatch,
        [api_league_response(), FakeResponse({"response": [
            api_scorers_response().json()["response"][0],
            {
                "player": {"id": 8, "name": "Second Player"},
                "statistics": [{
                    "team": {"id": 80, "name": "Second FC"},
                    "games": {},
                    "goals": {"total": 12},
                    "penalty": {},
                }],
            },
        ]})],
    )

    first = top_scorers_module.top_scorers("Premier League", season=2025, limit=1)
    second = top_scorers_module.top_scorers("Premier League", season=2025, limit=2)

    assert first["count"] == 1
    assert second["count"] == 2
    assert second["scorers"][1]["assists"] is None
    assert len(calls) == 2
