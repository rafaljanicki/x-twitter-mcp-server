import asyncio
import base64
import json
import os
import unittest
from typing import Any

from x_twitter_mcp.middleware import SmitheryConfigMiddleware


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
            self.assertEqual(os.environ["SEARCH_BACKEND"], "xquik")
            self.assertEqual(os.environ["HERMES_TWEET_API_KEY"], "request-key")

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
