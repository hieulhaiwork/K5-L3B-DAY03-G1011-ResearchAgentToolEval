from __future__ import annotations

import re
from typing import Any

from tools.timeline.tool import _twitter_get


def collect_football_mentions(
    handles: list[str], keyword: str, per_account: int = 10, max_results: int = 20,
) -> dict[str, Any]:
    """Filter recent timelines from specified accounts by one literal phrase."""
    tool = "football_mentions"
    try:
        if not isinstance(handles, list) or not 1 <= len(handles) <= 5:
            raise ValueError("handles must contain 1 to 5 X handles")
        clean = []
        for handle in handles:
            if not isinstance(handle, str) or not re.fullmatch(r"@?[A-Za-z0-9_]{1,15}", handle.strip()):
                raise ValueError("Each handle must have 1 to 15 letters, digits or underscores, optionally starting with @")
            name = handle.strip().lstrip("@").lower()
            if name not in clean:
                clean.append(name)
        if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200:
            raise ValueError("keyword must be a non-empty phrase of at most 200 characters")
        for name, value, high in (("per_account", per_account, 20), ("max_results", max_results, 50)):
            if type(value) is not int or not 1 <= value <= high:
                raise ValueError(f"{name} must be an integer from 1 to {high}")
    except (ValueError, TypeError) as exc:
        return {"tool": tool, "status": "error", "error": "ValueError", "message": str(exc)}

    items, errors, seen = [], [], set()
    successful_accounts = 0
    scanned = 0
    for handle in clean:
        try:
            data = _twitter_get("/timeline.php", {"screenname": handle})
            raw = data.get("timeline") if "timeline" in data else data.get("tweets")
            if not isinstance(raw, list):
                raise ValueError("Missing timeline list")
            records = [tweet for tweet in raw if isinstance(tweet, dict) and (tweet.get("tweet_id") or tweet.get("id"))][:per_account]
            account_items = []
            for tweet in records:
                text = tweet.get("text") or ""
                if not isinstance(text, str):
                    raise ValueError("Invalid tweet text")
                if keyword.strip().casefold() not in text.casefold():
                    continue
                tweet_id = str(tweet.get("tweet_id") or tweet["id"])
                if not tweet_id.isdigit():
                    continue
                author = tweet.get("screen_name") or (tweet.get("author") or {}).get("screen_name") or handle
                if not isinstance(author, str) or not re.fullmatch(r"[A-Za-z0-9_]{1,15}", author):
                    author = handle
                account_items.append({"tweet_id": tweet_id, "account": handle, "author": author,
                                      "text": text, "url": f"https://x.com/{author}/status/{tweet_id}",
                                      "date": tweet.get("created_at")})
            scanned += len(records)
            successful_accounts += 1
            for item in account_items:
                if item["tweet_id"] not in seen:
                    seen.add(item["tweet_id"])
                    items.append(item)
        except Exception as exc:
            errors.append({"handle": handle, "error": type(exc).__name__,
                           "message": "Could not read timeline; check API key, quota or account"})
    return {"tool": tool, "status": "partial" if errors and successful_accounts else "error" if errors else "success",
            "handles": clean, "keyword": keyword.strip(), "items": items[:max_results], "errors": errors,
            "scanned_count": scanned, "matched_count": len(items), "truncated": len(items) > max_results,
            "note": "Literal phrase match in recent fetched timelines only; no pagination, no completeness or fact verification guarantee"}
