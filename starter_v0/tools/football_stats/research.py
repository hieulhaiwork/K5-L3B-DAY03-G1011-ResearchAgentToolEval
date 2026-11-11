"""Discover ESPN results via Tavily and parse visible score tables via Firecrawl.

No LLM creates match records. Unsupported layouts fail closed.
"""
from __future__ import annotations

import os
import re
import unicodedata
from datetime import date, datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import requests

from tools.lookup.tool import web_search

ALIASES = {"mu": "Manchester United", "man utd": "Manchester United",
           "manchester utd": "Manchester United", "man united": "Manchester United",
           "liverpool fc": "Liverpool", "manchester united fc": "Manchester United"}
MONTHS = {name.lower(): i for i, name in enumerate(
    ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], 1)}


def canonical_team(team: str) -> str:
    return ALIASES.get(team.strip().casefold(), team.strip())


def _name(team: str) -> str:
    team = canonical_team(team).casefold()
    return "".join(c for c in unicodedata.normalize("NFKD", team) if not unicodedata.combining(c))


def _results_url(url: Any) -> str | None:
    if not isinstance(url, str):
        return None
    try:
        parsed = urlsplit(url)
    except ValueError:
        return None
    if parsed.scheme != "https" or parsed.hostname not in {"www.espn.com", "espn.com"} or parsed.username or parsed.password:
        return None
    if not re.fullmatch(r"/soccer/team/results/_/id/\d+/[a-z0-9-]+/?", parsed.path):
        return None
    return urlunsplit(("https", "www.espn.com", parsed.path.rstrip("/"), "", ""))


def parse_results(markdown: str, team: str, source_url: str, as_of: date) -> list[dict[str, Any]]:
    """Parse only full-time rows below an exact team Results heading and dated month."""
    if not isinstance(markdown, str):
        raise ValueError("Source has no readable text")
    headings = list(re.finditer(r"^#+\s+(.+?)\s+Results\s*$", markdown, re.M))
    heading = next((match for match in headings if _name(match.group(1)) == _name(team)), None)
    if heading is None:
        raise ValueError("Results page does not identify the requested team")
    month = year = None
    records = {}
    for line in markdown[heading.end():].splitlines():
        heading_date = re.fullmatch(r"\s*(?:#+\s*)?([A-Za-z]+),?\s+(\d{4})\s*", line)
        if heading_date and heading_date[1].lower() in MONTHS:
            month, year = MONTHS[heading_date[1].lower()], int(heading_date[2])
            continue
        if not line.strip().startswith("|") or not month or not year:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 6:
            continue
        # ESPN's visible full-time result, not the penalty shootout tally or a fixture.
        state = re.match(r"\[(FT(?:-Pens|-AET)?|AET)\]\(", cells[4])
        score = re.search(r"\[(\d+)\s*[-–]\s*(\d+)\]\((https://www\.espn\.com/soccer/match/_/gameId/(\d+)[^)]*)\)", cells[2])
        home = re.fullmatch(r"\[([^\]]+)\]\(https://www\.espn\.com/soccer/team/[^)]+\)", cells[1])
        away = re.fullmatch(r"\[([^\]]+)\]\(https://www\.espn\.com/soccer/team/[^)]+\)", cells[3])
        day = re.fullmatch(r"[A-Za-z]{3},\s*([A-Za-z]{3})\s+(\d{1,2})", cells[0])
        if not all((state, score, home, away, day)) or "friendly" in cells[5].casefold():
            continue
        if day[1].lower() != list(MONTHS)[month - 1][:3]:
            continue
        try:
            played = date(year, month, int(day[2]))
        except ValueError:
            continue
        if not 0 <= (as_of - played).days <= 120:
            continue
        if _name(home[1]) == _name(team):
            scored, conceded, opponent = int(score[1]), int(score[2]), away[1]
        elif _name(away[1]) == _name(team):
            scored, conceded, opponent = int(score[2]), int(score[1]), home[1]
        else:
            continue
        row = {"team": canonical_team(team), "opponent": opponent, "scored": scored,
               "conceded": conceded, "date": played.isoformat(), "competition": cells[5],
               "home_team": home[1], "away_team": away[1], "home_score": int(score[1]), "away_score": int(score[2]),
               "match_id": score[4], "source_url": score[3], "results_url": source_url,
               "result_status": state[1]}
        if score[4] in records and records[score[4]] != row:
            raise ValueError("Conflicting scores for the same match")
        records[score[4]] = row
    return sorted(records.values(), key=lambda row: (row["date"], row["match_id"]))


def find_recent_matches(team: str, last_n: int, *, as_of: date | None = None) -> dict[str, Any]:
    team = canonical_team(team)
    as_of = as_of or datetime.now(timezone(timedelta(hours=7))).date()
    for key in ("TAVILY_API_KEY", "FIRECRAWL_API_KEY"):
        if not os.getenv(key, "").strip():
            return {"status": "error", "error": "missing_api_key", "message": f"Missing {key} env var", "team": team}
    search = web_search(
        query=f'site:espn.com/soccer/team/results/ "{team}" latest completed results {as_of.isoformat()}',
        topic="general", timeframe=None, max_results=5,
    )
    if search.get("error") or not isinstance(search.get("items"), list):
        return {"status": "error", "error": "search_failed", "message": "Could not search results; check Tavily connection/quota", "team": team}
    urls = list(dict.fromkeys(url for item in search["items"] if isinstance(item, dict) and (url := _results_url(item.get("url")))))[:2]
    errors = []
    for url in urls:
        try:
            response = requests.post(
                "https://api.firecrawl.dev/v1/scrape", json={"url": url, "formats": ["markdown"]},
                headers={"Authorization": f"Bearer {os.environ['FIRECRAWL_API_KEY']}"}, timeout=60,
            )
            response.raise_for_status()
            payload = response.json()
            if payload.get("success") is False:
                raise ValueError("Scrape failed")
            records = parse_results(payload["data"]["markdown"], team, url, as_of)
            if not records:
                raise ValueError("No recent completed competitive matches in supported table")
            # Use one team's identified results page as a consistent list, rather than
            # merging incomplete search snippets from unrelated pages.
            return {"status": "success" if len(records) >= last_n else "partial", "team": team,
                    "matches": records[-last_n:], "requested_matches": last_n, "as_of": as_of.isoformat(),
                    "source_url": url, "errors": errors,
                    "note": "Latest completed competitive fixtures in the fetched ESPN table; shootouts excluded from W-D-L scores"}
        except Exception as exc:
            errors.append({"source_url": url, "error": type(exc).__name__, "message": "Could not read a supported results table"})
    return {"status": "error", "error": "results_unavailable", "team": team, "errors": errors,
            "message": "Could not find readable recent results for this team; no scores were invented"}
