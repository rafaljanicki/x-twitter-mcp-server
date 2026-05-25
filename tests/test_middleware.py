import asyncio
import base64
import json
import os
import unittest
from typing import Any
from unittest.mock import Mock, patch

from x_twitter_mcp.middleware import SmitheryConfigMiddleware
from x_twitter_mcp.xquik_search import search_with_xquik, xquik_search_enabled


class SmitheryConfigMiddlewareTests(unittest.TestCase):
    def setUp(self) -> None:
        self._env = os.environ.copy()
        for key in (
            "SEARCH_BACKEND",
            "HERMES_TWEET_API_KEY",
            "XQUIK_API_KEY",
            "XQUIK_BASE_URL",
            "XQUIK_AUTH_SCHEME",
        ):
            os.environ.pop(key, None)

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._env)

    def test_config_env_is_restored_after_http_request(self) -> None:
        async def app(scope: dict[str, Any], receive: Any, send: Any) -> None:
            self.assertEqual(scope["smithery_config"]["searchBackend"], "xquik")
            self.assertTrue(xquik_search_enabled())
            self.assertIsNone(os.environ.get("SEARCH_BACKEND"))
            self.assertIsNone(os.environ.get("HERMES_TWEET_API_KEY"))

        config = base64.b64encode(
            json.dumps(
                {
                    "searchBackend": "xquik",
                    "hermesTweetApiKey": "request-key",
                }
            ).encode()
        )
        middleware = SmitheryConfigMiddleware(app)
        scope = {"type": "http", "query_string": b"config=" + config}

        asyncio.run(middleware(scope, None, None))

        self.assertIsNone(os.environ.get("SEARCH_BACKEND"))
        self.assertIsNone(os.environ.get("HERMES_TWEET_API_KEY"))

    def test_concurrent_requests_keep_search_backend_config_isolated(self) -> None:
        async def main() -> None:
            started = 0
            both_started = asyncio.Event()

            async def invoke(config: dict[str, str]) -> None:
                nonlocal started

                async def app(scope: dict[str, Any], receive: Any, send: Any) -> None:
                    nonlocal started
                    started += 1
                    if started == 2:
                        both_started.set()
                    await both_started.wait()
                    self.assertEqual(scope["smithery_config"]["searchBackend"], "xquik")
                    self.assertTrue(xquik_search_enabled())
                    search_with_xquik("AI", "Top", 5, None)

                encoded_config = base64.b64encode(json.dumps(config).encode())
                middleware = SmitheryConfigMiddleware(app)
                scope = {"type": "http", "query_string": b"config=" + encoded_config}
                await middleware(scope, None, None)

            await asyncio.gather(
                invoke(
                    {
                        "searchBackend": "xquik",
                        "hermesTweetApiKey": "request-key-a",
                        "xquikBaseUrl": "https://a.example",
                    }
                ),
                invoke(
                    {
                        "searchBackend": "xquik",
                        "hermesTweetApiKey": "request-key-b",
                        "xquikBaseUrl": "https://b.example",
                    }
                ),
            )

        response = Mock()
        response.json.return_value = [{"id": "1", "text": "one"}]
        response.raise_for_status.return_value = None

        with patch("x_twitter_mcp.xquik_search.requests.get", return_value=response) as get:
            asyncio.run(main())

        calls = [
            (call.args[0], call.kwargs["headers"])
            for call in get.call_args_list
        ]
        self.assertCountEqual(
            calls,
            [
                ("https://a.example/api/v1/x/tweets/search", {"X-API-Key": "request-key-a"}),
                ("https://b.example/api/v1/x/tweets/search", {"X-API-Key": "request-key-b"}),
            ],
        )

    def test_missing_request_config_does_not_keep_stale_search_backend(self) -> None:
        os.environ["SEARCH_BACKEND"] = "xquik"
        os.environ["XQUIK_API_KEY"] = "existing-key"

        async def app(scope: dict[str, Any], receive: Any, send: Any) -> None:
            self.assertEqual(scope["smithery_config"], {})
            self.assertEqual(os.environ["SEARCH_BACKEND"], "xquik")
            self.assertEqual(os.environ["XQUIK_API_KEY"], "existing-key")

        middleware = SmitheryConfigMiddleware(app)
        scope = {"type": "http", "query_string": b""}

        asyncio.run(middleware(scope, None, None))

        self.assertEqual(os.environ["SEARCH_BACKEND"], "xquik")
        self.assertEqual(os.environ["XQUIK_API_KEY"], "existing-key")


if __name__ == "__main__":
    unittest.main()
