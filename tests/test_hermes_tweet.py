import os
import unittest
from unittest.mock import patch

from x_twitter_mcp.hermes_tweet import (
    is_configured,
    reset_request_config,
    search_tweets,
    set_request_config,
)


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class HermesTweetSearchTests(unittest.TestCase):
    def test_is_configured_checks_both_key_names(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(is_configured())

        with patch.dict(os.environ, {"XQUIK_API_KEY": "example_key"}, clear=True):
            self.assertTrue(is_configured())

    def test_search_tweets_builds_request_and_normalizes_results(self):
        calls = []

        def fake_get(url, headers, params, timeout):
            calls.append(
                {
                    "url": url,
                    "headers": headers,
                    "params": params,
                    "timeout": timeout,
                }
            )
            return FakeResponse(
                {
                    "tweets": [
                        {
                            "tweet_id": 123,
                            "full_text": "Hermes Agent launch notes",
                            "createdAt": "2026-06-06T10:00:00Z",
                            "author": {"id": 456, "screen_name": "hermes"},
                        }
                    ]
                }
            )

        with patch.dict(
            os.environ,
            {
                "HERMES_TWEET_API_KEY": "example_key",
                "HERMES_TWEET_BASE_URL": "https://api.example.test/",
            },
            clear=True,
        ):
            tweets = search_tweets(
                "Hermes Agent",
                5,
                "next",
                "Top",
                request_get=fake_get,
            )

        self.assertEqual(
            calls,
            [
                {
                    "url": "https://api.example.test/api/v1/x/tweets/search",
                    "headers": {
                        "accept": "application/json",
                        "x-api-key": "example_key",
                        "authorization": "Bearer example_key",
                    },
                    "params": {
                        "q": "Hermes Agent",
                        "limit": 5,
                        "queryType": "Top",
                        "cursor": "next",
                    },
                    "timeout": 30,
                }
            ],
        )
        self.assertEqual(
            tweets,
            [
                {
                    "id": "123",
                    "text": "Hermes Agent launch notes",
                    "created_at": "2026-06-06T10:00:00Z",
                    "author_id": "456",
                    "username": "hermes",
                    "url": "https://x.com/hermes/status/123",
                }
            ],
        )

    def test_search_tweets_requires_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(EnvironmentError):
                search_tweets("Hermes Agent", 5)

    def test_request_config_does_not_leak_after_reset(self):
        with patch.dict(os.environ, {}, clear=True):
            token = set_request_config({"hermesTweetApiKey": "example_key"})
            self.assertTrue(is_configured())
            reset_request_config(token)
            self.assertFalse(is_configured())


if __name__ == "__main__":
    unittest.main()
