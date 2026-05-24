import base64
import json
import os
from typing import Any
from urllib.parse import parse_qs, unquote

from starlette.types import ASGIApp, Receive, Scope, Send


_ENV_MAP = {
    "twitterApiKey": "TWITTER_API_KEY",
    "twitterApiSecret": "TWITTER_API_SECRET",
    "twitterAccessToken": "TWITTER_ACCESS_TOKEN",
    "twitterAccessTokenSecret": "TWITTER_ACCESS_TOKEN_SECRET",
    "twitterBearerToken": "TWITTER_BEARER_TOKEN",
    "twitterOauth2UserAccessToken": "TWITTER_OAUTH2_USER_ACCESS_TOKEN",
    "searchBackend": "SEARCH_BACKEND",
    "xquikApiKey": "XQUIK_API_KEY",
    "hermesTweetApiKey": "HERMES_TWEET_API_KEY",
    "xquikBaseUrl": "XQUIK_BASE_URL",
    "hermesTweetBaseUrl": "HERMES_TWEET_BASE_URL",
    "xquikAuthScheme": "XQUIK_AUTH_SCHEME",
}


def _apply_config_env(config: dict[str, Any]) -> dict[str, str | None]:
    previous = {env_key: os.environ.get(env_key) for env_key in _ENV_MAP.values()}
    for key, env_key in _ENV_MAP.items():
        value = config.get(key)
        if value:
            os.environ[env_key] = str(value)
    return previous


def _restore_env(previous: dict[str, str | None]) -> None:
    for env_key, value in previous.items():
        if value is None:
            os.environ.pop(env_key, None)
        else:
            os.environ[env_key] = value


class SmitheryConfigMiddleware:
    """Middleware to inject Smithery per-request config into ASGI scope.

    Also maps known Twitter keys into process environment for compatibility
    with existing initialization that reads os.environ.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        previous_env: dict[str, str | None] | None = None
        if scope.get("type") == "http":
            query = scope.get("query_string", b"").decode()
            config: dict[str, Any] = {}

            if "config=" in query:
                try:
                    parsed = parse_qs(query)
                    enc = parsed.get("config", [""])[0]
                    raw = base64.b64decode(unquote(enc))
                    config = json.loads(raw)
                except Exception:
                    config = {}

            scope["smithery_config"] = config

            # Map config to env vars expected by server.initialize_twitter_clients
            previous_env = _apply_config_env(config)

        try:
            await self.app(scope, receive, send)
        finally:
            if previous_env is not None:
                _restore_env(previous_env)
