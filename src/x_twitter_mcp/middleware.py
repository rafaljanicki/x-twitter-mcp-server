import base64
import json
from typing import Any
from urllib.parse import parse_qs, unquote

from starlette.types import ASGIApp, Receive, Scope, Send


class SmitheryConfigMiddleware:
    """Middleware to inject Smithery per-request config into ASGI scope.

    Also maps known Twitter keys into process environment for compatibility
    with existing initialization that reads os.environ.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
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
            import os

            env_map = {
                "twitterApiKey": "TWITTER_API_KEY",
                "twitterApiSecret": "TWITTER_API_SECRET",
                "twitterAccessToken": "TWITTER_ACCESS_TOKEN",
                "twitterAccessTokenSecret": "TWITTER_ACCESS_TOKEN_SECRET",
                "twitterBearerToken": "TWITTER_BEARER_TOKEN",
            }

            for key, env_key in env_map.items():
                value = config.get(key)
                if value:
                    os.environ[env_key] = str(value)

        await self.app(scope, receive, send)


