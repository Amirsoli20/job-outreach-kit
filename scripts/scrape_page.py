#!/usr/bin/env python3
"""Fetch one web page with Scrapling and print trimmed text (token-friendly).

Usage: .venv/bin/python scripts/scrape_page.py URL [--css SELECTOR] [--browser]
--css      print only text matching this selector (e.g. "h1::text", "footer a::attr(href)")
--browser  use StealthyFetcher for JavaScript pages (needs `scrapling install` browsers first)
"""
import argparse
from scrapling.fetchers import Fetcher, StealthyFetcher


def scrape_page(url: str, css: str = "", use_browser: bool = False) -> str:
    """Fetch a web page. If css is given, return only matching text.
    Set use_browser=True for pages that need JavaScript."""
    page = StealthyFetcher.fetch(url, headless=True) if use_browser else Fetcher.get(url)
    if css:
        return "\n".join(str(x).strip() for x in page.css(css).getall())
    return " ".join(str(t).strip() for t in page.css("body *::text").getall())[:8000]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--css", default="")
    ap.add_argument("--browser", action="store_true")
    a = ap.parse_args()
    print(scrape_page(a.url, a.css, a.browser))
