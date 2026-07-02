"""Tests for crawler_bridge module."""

import builtins
import importlib
import json
import os
import shutil
import stat
import sys
import unittest
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

# Add scripts to path (lib resolves under scripts/)
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import lib.crawler_bridge as crawler_bridge


@contextmanager
def _temp_path():
    root = Path(__file__).parent.parent / ".codex-test-tmp"
    root.mkdir(exist_ok=True)
    path = root / uuid.uuid4().hex
    path.mkdir()
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def _reset_playwright_cache():
    crawler_bridge._playwright_available = None


class TestIsPlaywrightAvailable(unittest.TestCase):
    def tearDown(self):
        _reset_playwright_cache()

    def test_is_playwright_available(self):
        _reset_playwright_cache()
        real_import = builtins.__import__

        def import_playwright_fails(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "playwright.sync_api":
                raise ImportError("mock: playwright not installed")
            return real_import(name, globals, locals, fromlist, level)

        with patch.object(builtins, "__import__", side_effect=import_playwright_fails):
            importlib.reload(crawler_bridge)
            self.assertFalse(crawler_bridge.is_playwright_available())

        importlib.reload(crawler_bridge)


class TestParseCount(unittest.TestCase):
    def test_parse_count(self):
        p = crawler_bridge._parse_count
        self.assertEqual(p("1.2万"), 12000)
        self.assertEqual(p("1.2w"), 12000)
        self.assertEqual(p("1.2W"), 12000)
        self.assertEqual(p("12k"), 12000)
        self.assertEqual(p("12K"), 12000)
        self.assertEqual(p("1000"), 1000)
        self.assertEqual(p("1,234"), 1234)
        self.assertEqual(p("1亿"), 100000000)
        self.assertEqual(p("2.5亿"), 250000000)
        self.assertEqual(p(""), 0)
        self.assertEqual(p(None), 0)


class TestParseRelativeDate(unittest.TestCase):
    def test_parse_relative_date(self):
        fixed_now = datetime(2026, 4, 10, 15, 30, 0)
        prd = crawler_bridge._parse_relative_date

        with patch("lib.crawler_bridge.datetime") as mock_dt:
            mock_dt.now.return_value = fixed_now
            mock_dt.strptime = datetime.strptime

            self.assertEqual(
                prd("Thu Apr 10 10:00:00 +0800 2026"),
                "2026-04-10",
            )
            self.assertEqual(prd("10分钟前"), "2026-04-10")
            self.assertEqual(prd("3小时前"), "2026-04-10")
            self.assertEqual(prd("昨天"), "2026-04-09")
            self.assertEqual(prd("04-09"), "2026-04-09")
            self.assertIsNone(prd(""))
            self.assertIsNone(prd(None))


class TestGetCrawlerStatus(unittest.TestCase):
    def tearDown(self):
        _reset_playwright_cache()

    def test_get_crawler_status(self):
        with _temp_path() as cookie_dir:
            (cookie_dir / "weibo_cookies.json").write_text("[]", encoding="utf-8")
            with patch.object(crawler_bridge, "COOKIE_DIR", cookie_dir):
                with patch.dict(os.environ, {crawler_bridge.COOKIE_PERSIST_ENV: "1"}):
                    with patch.object(
                        crawler_bridge,
                        "is_playwright_available",
                        return_value=True,
                    ):
                        status = crawler_bridge.get_crawler_status()

            self.assertIsInstance(status, dict)
            self.assertIn("playwright_available", status)
            self.assertIn("cached_logins", status)
            self.assertIn("cookie_dir", status)
            self.assertIn("cookie_persistence_enabled", status)
            self.assertTrue(status["playwright_available"])
            self.assertTrue(status["cookie_persistence_enabled"])
            self.assertEqual(status["cookie_dir"], str(cookie_dir))
            self.assertIn("weibo", status["cached_logins"])

    def test_get_crawler_status_does_not_list_logins_when_disabled(self):
        with _temp_path() as cookie_dir:
            (cookie_dir / "weibo_cookies.json").write_text("[]", encoding="utf-8")
            with patch.object(crawler_bridge, "COOKIE_DIR", cookie_dir):
                with patch.dict(os.environ, {crawler_bridge.COOKIE_PERSIST_ENV: ""}):
                    with patch.object(
                        crawler_bridge,
                        "is_playwright_available",
                        return_value=True,
                    ):
                        status = crawler_bridge.get_crawler_status()

            self.assertIsInstance(status, dict)
            self.assertTrue(status["playwright_available"])
            self.assertFalse(status["cookie_persistence_enabled"])
            self.assertEqual(status["cookie_dir"], str(cookie_dir))
            self.assertEqual(status["cached_logins"], [])


class TestCleanHtml(unittest.TestCase):
    def test_clean_html(self):
        clean = crawler_bridge._clean_html
        self.assertEqual(clean(""), "")
        self.assertEqual(clean("a <b>b</b> c"), "a b c")
        self.assertEqual(clean("  foo   bar  "), "foo bar")


class TestLoadCookiesMissingFile(unittest.TestCase):
    def test_load_cookies_missing_file(self):
        with _temp_path() as d:
            with patch.object(crawler_bridge, "COOKIE_DIR", d):
                with patch.dict(os.environ, {crawler_bridge.COOKIE_PERSIST_ENV: "1"}):
                    self.assertIsNone(crawler_bridge.load_cookies("nonexistent_platform"))


class TestSaveAndLoadCookies(unittest.TestCase):
    def test_save_and_load_cookies_disabled_by_default(self):
        cookies = [{"name": "session", "value": "abc", "domain": ".example.com"}]
        with _temp_path() as td:
            d = Path(td) / "cookies"
            with patch.object(crawler_bridge, "COOKIE_DIR", d):
                with patch.dict(os.environ, {crawler_bridge.COOKIE_PERSIST_ENV: ""}):
                    crawler_bridge.save_cookies("weibo", cookies)
                    loaded = crawler_bridge.load_cookies("weibo")

            self.assertIsNone(loaded)
            self.assertFalse((d / "weibo_cookies.json").exists())
            self.assertFalse(d.exists())

    def test_save_and_load_cookies(self):
        cookies = [{"name": "session", "value": "abc", "domain": ".example.com"}]
        with _temp_path() as td:
            d = Path(td) / "cookies"
            with patch.object(crawler_bridge, "COOKIE_DIR", d):
                with patch.dict(os.environ, {crawler_bridge.COOKIE_PERSIST_ENV: "1"}):
                    crawler_bridge.save_cookies("weibo", cookies)
                    loaded = crawler_bridge.load_cookies("weibo")

            self.assertEqual(loaded, cookies)
            path = d / "weibo_cookies.json"
            self.assertTrue(path.exists())
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), cookies)
            if os.name == "posix":
                self.assertEqual(stat.S_IMODE(d.stat().st_mode), 0o700)
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)


if __name__ == "__main__":
    unittest.main()
