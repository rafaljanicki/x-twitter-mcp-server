import os
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests


_DEFAULT_BASE_URL = "https://xquik.com"
_XQUIK_BACKENDS = {"xquik"}


def _non_empty(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def xquik_search_enabled() -> bool:
    backend = _non_empty(os.getenv("SEARCH_BACKEND"))
    return backend is not None and backend.lower() in _XQUIK_BACKENDS


def _api_key() -> Optional[str]:
    return _non_empty(os.getenv("XQUIK_API_KEY"))


def _base_url() -> str:
    configured = _non_empty(os.getenv("XQUIK_BASE_URL"))
    return configured or _DEFAULT_BASE_URL


def _auth_scheme() -> str:
    return (_non_empty(os.getenv("XQUIK_AUTH_SCHEME")) or "api-key").lower()


def _search_url() -> str:
    return urljoin(_base_url().rstrip("/") + "/", "api/v1/x/tweets/search")


def _headers() -> Dict[str, str]:
    api_key = _api_key()
    if not api_key:
        return {}
    if _auth_scheme() == "bearer":
        return {"Authorization": f"Bearer {api_key}"}
    return {"X-API-Key": api_key}


def _tweet_items(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []

    for key in ("tweets", "data", "results", "items"):
        items = payload.get(key)
        if isinstance(items, list):
            return [item for item in items if isinstance(item, dict)]

    nested = payload.get("timeline") or payload.get("content")
    if isinstance(nested, dict):
        return _tweet_items(nested)

    return []


def _first_string(*values: Any) -> Optional[str]:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def _author_id(tweet: Dict[str, Any]) -> Optional[str]:
    author = tweet.get("author") or tweet.get("user")
    if isinstance(author, dict):
        return _first_string(
            author.get("id"),
            author.get("id_str"),
            author.get("rest_id"),
        )
    return _first_string(tweet.get("author_id"), tweet.get("user_id"), tweet.get("userId"))


def normalize_xquik_tweet(tweet: Dict[str, Any]) -> Dict[str, Any]:
    normalized: Dict[str, Any] = {}
    tweet_id = _first_string(
        tweet.get("id"),
        tweet.get("id_str"),
        tweet.get("tweet_id"),
        tweet.get("tweetId"),
    )
    text = _first_string(tweet.get("text"), tweet.get("full_text"), tweet.get("content"))
    created_at = _first_string(tweet.get("created_at"), tweet.get("createdAt"), tweet.get("date"))
    author_id = _author_id(tweet)

    if tweet_id:
        normalized["id"] = tweet_id
    if text:
        normalized["text"] = text
    if created_at:
        normalized["created_at"] = created_at
    if author_id:
        normalized["author_id"] = author_id

    return normalized or dict(tweet)


def search_with_xquik(
    query: str,
    product: Optional[str],
    count: Optional[int],
    cursor: Optional[str],
) -> List[Dict[str, Any]]:
    if count is None:
        effective_count = 100
    elif count < 1:
        effective_count = 1
    elif count > 100:
        effective_count = 100
    else:
        effective_count = count

    params: Dict[str, Any] = {
        "q": query,
        "limit": effective_count,
    }
    if product:
        params["queryType"] = "Latest" if product == "Latest" else "Top"
    if cursor:
        params["cursor"] = cursor

    response = requests.get(_search_url(), headers=_headers(), params=params, timeout=30)
    response.raise_for_status()
    return [normalize_xquik_tweet(tweet) for tweet in _tweet_items(response.json())]
