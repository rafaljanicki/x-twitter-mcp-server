"""Optional Hermes Tweet search backend for X/Twitter reads."""

from __future__ import annotations

import os
from contextvars import ContextVar
from typing import Any, Callable, Mapping, Optional

import requests


DEFAULT_BASE_URL = "https://api.xquik.com"
SEARCH_PATH = "/api/v1/x/tweets/search"
TIMEOUT_SECONDS = 30

RequestGet = Callable[..., Any]
_request_config: ContextVar[dict[str, Any]] = ContextVar("hermes_tweet_config", default={})


def set_request_config(config: Mapping[str, Any]):
    """Set per-request Hermes Tweet config from Smithery middleware."""
    scoped = {
        "api_key": config.get("hermesTweetApiKey") or config.get("xquikApiKey"),
        "base_url": config.get("hermesTweetBaseUrl") or config.get("xquikBaseUrl"),
    }
    return _request_config.set(scoped)


def reset_request_config(token: object) -> None:
    """Reset per-request Hermes Tweet config after the ASGI request completes."""
    _request_config.reset(token)


def is_configured() -> bool:
    """Return True when Hermes Tweet credentials are present."""
    return bool(_api_key())


def search_tweets(
    query: str,
    count: int,
    cursor: Optional[str] = None,
    query_type: Optional[str] = None,
    *,
    request_get: RequestGet = requests.get,
) -> list[dict[str, Any]]:
    """Search tweets through Hermes Tweet and normalize common response shapes."""
    api_key = _api_key()
    if not api_key:
        raise EnvironmentError(
            "Missing HERMES_TWEET_API_KEY or XQUIK_API_KEY for Hermes Tweet search."
        )

    params: dict[str, Any] = {"q": query, "limit": count}
    if query_type in {"Top", "Latest"}:
        params["queryType"] = query_type
    if cursor:
        params["cursor"] = cursor

    response = request_get(
        _search_url(),
        headers=_auth_headers(api_key),
        params=params,
        timeout=TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload = response.json()
    return [_normalize_tweet(tweet) for tweet in _extract_tweets(payload)]


def _api_key() -> Optional[str]:
    configured = _request_config.get().get("api_key")
    if configured:
        return str(configured)
    return os.getenv("HERMES_TWEET_API_KEY") or os.getenv("XQUIK_API_KEY")


def _base_url() -> str:
    configured = _request_config.get().get("base_url")
    if configured:
        return str(configured).rstrip("/")
    configured = os.getenv("HERMES_TWEET_BASE_URL") or os.getenv("XQUIK_BASE_URL")
    return (configured or DEFAULT_BASE_URL).rstrip("/")


def _search_url() -> str:
    return f"{_base_url()}{SEARCH_PATH}"


def _auth_headers(api_key: str) -> dict[str, str]:
    return {
        "accept": "application/json",
        "x-api-key": api_key,
        "authorization": f"Bearer {api_key}",
    }


def _extract_tweets(payload: Any) -> list[Mapping[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, Mapping)]
    if not isinstance(payload, Mapping):
        return []
    for key in ("tweets", "data", "results", "items"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, Mapping)]
    nested = payload.get("result")
    if isinstance(nested, Mapping):
        return _extract_tweets(nested)
    return []


def _normalize_tweet(tweet: Mapping[str, Any]) -> dict[str, Any]:
    author = tweet.get("author") or tweet.get("user") or {}
    if not isinstance(author, Mapping):
        author = {}

    normalized: dict[str, Any] = {
        "id": _string_or_none(tweet.get("id") or tweet.get("tweet_id")),
        "text": _string_or_none(tweet.get("text") or tweet.get("full_text")),
        "created_at": _string_or_none(tweet.get("created_at") or tweet.get("createdAt")),
        "author_id": _string_or_none(
            tweet.get("author_id") or tweet.get("authorId") or author.get("id")
        ),
    }

    username = _string_or_none(author.get("username") or author.get("screen_name"))
    if username:
        normalized["username"] = username

    url = _string_or_none(tweet.get("url"))
    if url:
        normalized["url"] = url
    elif normalized["id"] and username:
        normalized["url"] = f"https://x.com/{username}/status/{normalized['id']}"

    return {key: value for key, value in normalized.items() if value is not None}


def _string_or_none(value: Any) -> Optional[str]:
    if value is None:
        return None
    return str(value)
