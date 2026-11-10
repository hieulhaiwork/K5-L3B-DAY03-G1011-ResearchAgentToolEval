"""TODO CP3 (student): Tool Unit Test Challenge.

Each test below is a stub. Replace `pytest.skip(...)` with a real test.
Patterns to copy are in test_tools_examples.py. Fixtures are in conftest.py.

Rules:
- Offline only: mock HTTP with `fake_http`, set fake keys with `monkeypatch.setenv`.
- One behaviour per test. Name the test after the behaviour, not the function.
- Done = `pytest tests/ -v` shows 0 skipped, 0 failed.
"""
from __future__ import annotations

import pytest

from conftest import FakeResponse  # noqa: F401  (you will need it)
from tools import TOOL_FUNCTIONS  # noqa: F401

TODO = "TODO CP3 (student): implement this test"


# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    # Call clarify with response_type="choice" and 2 options.
    # Assert: options are returned unchanged, awaiting_user is True.
    pytest.skip(TODO)


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    # Items with section "A", "B", "A" -> markdown has exactly one "## A" and one "## B".
    pytest.skip(TODO)


def test_format_thread_numbers_items() -> None:
    # template="thread" -> lines start with "1/", "2/", ...
    pytest.skip(TODO)


def test_format_empty_items_does_not_crash() -> None:
    # items=None and items=[] -> item_count == 0, no exception.
    pytest.skip(TODO)


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    # Set TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID, mock HTTP.
    # Assert: exactly one POST, URL contains the token, json has chat_id + text, status == "sent".
    pytest.skip(TODO)


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    pytest.skip(TODO)


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    # timeframe=None -> request body has no "time_range" key.
    pytest.skip(TODO)


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    # Mock {"data": {"markdown": "...", "metadata": {"title": "T", "sourceURL": "https://..."}}}
    # Assert title/url/source/summary in result["items"][0].
    pytest.skip(TODO)


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    pytest.skip(TODO)


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    # Mock {"timeline": [...]} with 1 item missing tweet_id and 6 valid items, limit=3.
    # Assert 3 items, and each url looks like https://x.com/<handle>/status/<id>.
    pytest.skip(TODO)


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    # Assert the request params carry the query and search_type ("Top" / "Latest").
    pytest.skip(TODO)


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    pytest.skip(TODO)


def test_policy_area_filter_only_returns_that_area() -> None:
    # policy_area="data_privacy" -> every result has policy_area == "data_privacy".
    pytest.skip(TODO)


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    # One policy file contains a quoted line that tries to give the assistant orders.
    # Query that section (source_citation) and assert: that line is in untrusted_text, NOT in facts.
    pytest.skip(TODO)


# ---------------- YOUR NEW TOOL(S) ----------------
# Write at least 3 tests per tool your team adds:
#   1. happy path (mocked if it calls an API)
#   2. bad / missing input from the model (empty string, wrong type, out-of-enum value)
#   3. failure path (missing key, HTTP error, timeout) -> returns error dict, does not raise

def test_football_stats_happy_path_calculates_form_and_points() -> None:
    func = TOOL_FUNCTIONS["football_stats"]
    matches = [
        {"team": "Arsenal", "opponent": "Chelsea", "scored": 2, "conceded": 0},
        {"team": "Arsenal", "opponent": "Spurs", "scored": 3, "conceded": 1},
        {"team": "Arsenal", "opponent": "Man City", "scored": 1, "conceded": 1},
        {"team": "Chelsea", "opponent": "Fulham", "scored": 1, "conceded": 2},
    ]
    res = func(team_a="Arsenal", matches=matches, team_b="Chelsea", last_n=3)

    assert res["status"] == "success"
    assert res["team_a"]["team"] == "Arsenal"
    assert res["team_a"]["matches_analyzed"] == 3
    assert res["team_a"]["form"] == "W-W-D"
    assert res["team_a"]["points"] == 7  # 3 + 3 + 1
    assert res["team_a"]["goals_scored"] == 6
    assert res["team_a"]["goals_conceded"] == 2
    assert res["team_a"]["clean_sheets"] == 1

    assert res["team_b"]["team"] == "Chelsea"
    assert res["team_b"]["points"] == 0
    assert res["team_b"]["form"] == "L"

    assert "comparison" in res
    assert res["comparison"]["better_form_team"] == "Arsenal"
    assert res["comparison"]["points_diff"] == 7


def test_football_stats_bad_input_from_model() -> None:
    func = TOOL_FUNCTIONS["football_stats"]

    # Case 1: team_a is empty string
    res_empty_team = func(team_a="", matches=[])
    assert res_empty_team["status"] == "error"
    assert "team_a" in res_empty_team["error"]

    # Case 2: matches is not a list
    res_bad_matches = func(team_a="Arsenal", matches="not-a-list")
    assert res_bad_matches["status"] == "error"
    assert "matches" in res_bad_matches["error"]

    # Case 3: last_n is <= 0 or invalid string
    res_invalid_n = func(team_a="Arsenal", matches=[], last_n=-5)
    assert res_invalid_n["status"] == "error"
    assert "last_n" in res_invalid_n["error"]


def test_football_stats_empty_matches_does_not_crash() -> None:
    func = TOOL_FUNCTIONS["football_stats"]
    # Model sends team with no matches played yet
    res = func(team_a="Liverpool", matches=[])
    assert res["status"] == "success"
    assert res["team_a"]["matches_analyzed"] == 0
    assert res["team_a"]["form"] == "N/A"
    assert res["team_a"]["points"] == 0
    assert res["team_a"]["win_rate_percent"] == 0.0
