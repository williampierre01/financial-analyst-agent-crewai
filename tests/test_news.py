"""No network: publication metadata must not become invented dates or sources."""
import json
import asyncio
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import mcp_server as server
from news_data import news_date, news_url

NOW = datetime(2026, 10, 14, 23, 30, tzinfo=timezone.utc)


class NewsDateTests(unittest.TestCase):
    def test_explicit_timezone_converts_to_brasilia(self):
        result = news_date("2026-10-15T01:00:00+02:00", NOW)
        self.assertEqual(result["date_status"], "reported")
        self.assertEqual(result["published_at"], "2026-10-14T23:00:00+00:00")
        self.assertIn("14/10/2026 20:00", result["date_label"])
        self.assertIn("não verificada", result["date_label"])
        self.assertEqual(result["date_raw"], "2026-10-15T01:00:00+02:00")

    def test_future_instant_is_not_published_at(self):
        for raw in ["2026-10-15T00:00:00Z", "2026-10-14T21:00:00-03:00"]:
            with self.subTest(raw=raw):
                result = news_date(raw, NOW)
                self.assertEqual(result["date_status"], "future")
                self.assertIsNone(result["published_at"])
                self.assertEqual(result["date_raw"], raw)
                self.assertIn("não confirmada", result["date_label"])

    def test_date_only_and_naive_times_never_assume_timezone(self):
        for raw in ["2026-10-14", "2026-10-15", "2026-10-14T09:00:00"]:
            with self.subTest(raw=raw):
                result = news_date(raw, NOW)
                self.assertEqual(result["date_status"], "timezone_missing")
                self.assertIsNone(result["published_at"])

    def test_missing_dates_stay_missing(self):
        for raw in [None, ""]:
            self.assertEqual(news_date(raw, NOW)["date_status"], "missing")

    def test_invalid_and_relative_dates_are_not_guessed(self):
        for raw in ["há 2 horas", "15/10/2026", "2026-02-30T00:00:00Z", 123, True, {}, []]:
            with self.subTest(raw=raw):
                result = news_date(raw, NOW)
                self.assertEqual(result["date_status"], "invalid")
                self.assertIsNone(result["published_at"])

    def test_old_dates_are_preserved_without_claiming_recency(self):
        result = news_date("2020-01-01T00:00:00Z", NOW)
        self.assertEqual(result["published_at"], "2020-01-01T00:00:00+00:00")
        self.assertIn("31/12/2019 21:00", result["date_label"])

    def test_exact_collection_time_is_not_future(self):
        self.assertEqual(news_date(NOW.isoformat(), NOW)["date_status"], "reported")

    def test_naive_collection_time_is_rejected(self):
        with self.assertRaises(ValueError):
            news_date(None, NOW.replace(tzinfo=None))


class NewsToolTests(unittest.TestCase):
    def test_registered_mcp_tool_delivers_date_provenance(self):
        client = MagicMock()
        client.__enter__.return_value.news.return_value = [
            {"title": "Notícia", "url": "https://example.com", "date": "2026-10-15T00:00:00Z"}
        ]
        with patch.object(server, "DDGS", return_value=client), patch.object(server, "datetime") as clock:
            clock.now.return_value = NOW
            content = asyncio.run(server.mcp.call_tool("get_market_news", {"ticker": "PETR4.SA"}))
        structured = json.loads(content[0].text)
        item = structured["items"][0]
        self.assertEqual(item["date_status"], "future")
        self.assertIsNone(item["published_at"])
        self.assertIn("não confirmada", item["date_label"])
        server.MarketNews.model_validate(structured)

    def fetch(self, raw):
        client = MagicMock()
        client.__enter__.return_value.news.return_value = raw
        with patch.object(server, "DDGS", return_value=client), patch.object(server, "datetime") as clock:
            clock.now.return_value = NOW
            result = server.get_market_news("PETR4.SA")
        client.__enter__.return_value.news.assert_called_once_with("PETR4.SA acoes", max_results=3)
        return result

    def test_tool_preserves_provenance_and_marks_unverified_article(self):
        result = self.fetch([{"title": "Notícia", "url": "https://example.com/noticia?x=1",
                              "body": "Resumo", "source": "Veículo", "date": "2026-10-14T20:00:00Z"}])
        item = result["items"][0]
        self.assertEqual(item["source"], "Veículo")
        self.assertEqual(item["url"], "https://example.com/noticia?x=1")
        self.assertEqual(item["date_origin"], "ddgs.news.date")
        self.assertFalse(item["article_verified"])
        self.assertEqual(item["date_status"], "reported")
        self.assertEqual(result["query"], "PETR4.SA acoes")
        self.assertEqual(result["provider"], "ddgs")
        self.assertEqual(datetime.fromisoformat(result["retrieved_at"]), NOW)
        json.dumps(result, allow_nan=False)
        server.MarketNews.model_validate(result)

    def test_title_snippet_and_url_do_not_supply_a_missing_date(self):
        result = self.fetch([{"title": "Resultados de 15/10/2026", "body": "Publicado hoje",
                              "url": "https://example.com/2026/10/15/noticia"}])
        item = result["items"][0]
        self.assertEqual(item["date_status"], "missing")
        self.assertIsNone(item["published_at"])
        self.assertEqual(item["source"], "")

    def test_malformed_item_does_not_discard_other_news(self):
        result = self.fetch([None, {"title": "Sem URL"}, {"url": "https://example.com"},
                             {"title": "Boa", "url": "https://example.com", "body": None,
                              "source": None, "date": "2026-10-15T00:00:00Z"}])
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["date_status"], "future")
        self.assertEqual(len(result["warnings"]), 2)

    def test_empty_search_has_no_invented_items(self):
        self.assertEqual(self.fetch([])["items"], [])

    def test_search_error_does_not_expose_exception_or_fabricate_news(self):
        with patch.object(server, "DDGS", side_effect=RuntimeError("secret-token")):
            result = server.get_market_news("PETR4.SA")
        self.assertIn("error", result)
        self.assertNotIn("secret-token", json.dumps(result))
        self.assertNotIn("items", result)

    def test_only_returned_http_links_are_accepted(self):
        for value in [None, "", "javascript:alert(1)", "/noticia", "https://",
                      "https://user:password@example.com", "https://example.com:bad",
                      "https://example.com/a b", "https://[invalid"]:
            with self.subTest(value=value):
                self.assertIsNone(news_url(value))
        self.assertEqual(news_url("https://example.com/a#b"), "https://example.com/a#b")
