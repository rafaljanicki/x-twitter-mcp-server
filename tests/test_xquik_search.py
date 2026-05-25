import os
import unittest
from unittest.mock import Mock, patch

from x_twitter_mcp.xquik_search import (
    normalize_xquik_tweet,
    search_with_xquik,
    xquik_search_enabled,
)


class XquikSearchTests(unittest.TestCase):
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

    def test_xquik_backend_enables_xquik_search(self) -> None:
        os.environ["SEARCH_BACKEND"] = "xquik"

        self.assertTrue(xquik_search_enabled())

    def test_blank_xquik_key_omits_auth_header(self) -> None:
        os.environ["XQUIK_API_KEY"] = " "
        os.environ["XQUIK_BASE_URL"] = "https://example.test/base"
        response = Mock()
        response.json.return_value = {
            "tweets": [
                {
                    "tweet_id": "123",
                    "full_text": "Hello from Xquik",
                    "createdAt": "2026-05-24T00:00:00Z",
                    "author": {"id_str": "42"},
                }
            ]
        }
        response.raise_for_status.return_value = None

        with patch("x_twitter_mcp.xquik_search.requests.get", return_value=response) as get:
            tweets = search_with_xquik("Xquik", "Latest", 0, "cursor-1")

        self.assertEqual(
            tweets,
            [
                {
                    "id": "123",
                    "text": "Hello from Xquik",
                    "created_at": "2026-05-24T00:00:00Z",
                    "author_id": "42",
                }
            ],
        )
        get.assert_called_once_with(
            "https://example.test/base/api/v1/x/tweets/search",
            headers={},
            params={
                "q": "Xquik",
                "limit": 1,
                "queryType": "Latest",
                "cursor": "cursor-1",
            },
            timeout=30,
        )

    def test_bearer_auth_scheme(self) -> None:
        os.environ["HERMES_TWEET_API_KEY"] = "hermes-key"
        os.environ["XQUIK_API_KEY"] = "xquik-key"
        os.environ["XQUIK_AUTH_SCHEME"] = "bearer"
        response = Mock()
        response.json.return_value = [{"id": "1", "text": "one"}]
        response.raise_for_status.return_value = None

        with patch("x_twitter_mcp.xquik_search.requests.get", return_value=response) as get:
            tweets = search_with_xquik("AI", "Top", 101, None)

        self.assertEqual(tweets, [{"id": "1", "text": "one"}])
        self.assertEqual(get.call_args.kwargs["headers"], {"Authorization": "Bearer hermes-key"})
        self.assertEqual(
            get.call_args.kwargs["params"],
            {"q": "AI", "limit": 100, "queryType": "Top"},
        )

    def test_normalize_preserves_unknown_tweet_shapes(self) -> None:
        tweet = {"unexpected": "value"}

        self.assertEqual(normalize_xquik_tweet(tweet), tweet)


if __name__ == "__main__":
    unittest.main()
