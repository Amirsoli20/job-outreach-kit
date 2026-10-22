#!/usr/bin/env python3
"""Pull hiring-relevant people from a company's own website with Scrapling. Prints compact JSON.

Usage: .venv/bin/python scripts/find_contacts.py https://company.com [--max-pages 4] [--browser]
Fetches the homepage, follows links to team/about/leadership/contact/careers pages, and returns only:
  people   - lines containing a hiring-relevant title, with the name-like line next to them, ranked by tier
  emails   - published emails (mailto: and visible text)
  linkedin - linkedin.com/in/ profile links
No LLM tokens are spent here; Claude reads the small JSON instead of whole pages.
Tiers: 1 = CEO/Founder, 2 = leaders in the user's field (contact_tier2_regex in config.json),
3 = hiring managers for the role (contact_tier3_regex) plus HR/talent/recruiters.
"""
import argparse, json, re
from pathlib import Path
from urllib.parse import urljoin, urlparse
from scrapling.fetchers import Fetcher, StealthyFetcher

USE_BROWSER = False
CONFIG = Path(__file__).resolve().parent.parent / "config.json"
_cfg = json.loads(CONFIG.read_text()) if CONFIG.exists() else {}
NEVER = r"(?!x)x"  # matches nothing; used until /setup fills config.json
TIER2 = _cfg.get("contact_tier2_regex") or NEVER
TIER3 = _cfg.get("contact_tier3_regex") or NEVER

PAGE_RE = re.compile(r"team|about|people|leadership|management|founder|who-we-are|our-story|contact|careers|jobs|join", re.I)
SKIP_PATH = re.compile(r"service|solution|capabilit|industr|blog|news|press|work/|case|product|insight|event", re.I)
PRIORITY = re.compile(r"team|leadership|people|management|founder|about|who-we-are|our-story", re.I)
TIERS = [
    (1, re.compile(r"\b(co-?founder|founder|ceo|chief executive|managing director|owner|managing partner|\bmd\b)\b", re.I)),
    (2, re.compile(TIER2, re.I)),
    (3, re.compile(rf"(?:{TIER3})|\b(head of (people|talent|hr)|hr manager|talent (acquisition|partner)|"
                   r"recruit(er|ment)|people (ops|operations|partner))\b", re.I)),
]
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
NAME_RE = re.compile(r"^[A-Z][\w'’.-]+(?:\s+[A-Z][\w'’.-]+){1,3}$")
NOT_NAME = re.compile(r"director|designer|manager|lead|head|chief|officer|founder|ceo|states|kingdom|emirates|london|dubai|"
                      r"new york|team|about|contact|careers|read more|learn more|apply", re.I)
JOB_PAGE = re.compile(r"career|jobs?\b|join|vacanc|openings", re.I)
JUNK_EMAIL = re.compile(r"\.(png|jpg|jpeg|gif|svg|webp)$|sentry|wixpress|example\.", re.I)


def fetch(url):
    try:
        p = StealthyFetcher.fetch(url, headless=True) if USE_BROWSER else Fetcher.get(url, timeout=15)
        return p if p.status == 200 else None
    except Exception:
        return None


def lines_of(page):
    out = []
    for t in page.css("body *::text").getall():
        t = re.sub(r"\s+", " ", str(t)).strip()
        if t and len(t) < 120:
            out.append(t)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("website")
    ap.add_argument("--max-pages", type=int, default=4)
    ap.add_argument("--browser", action="store_true", help="render JavaScript (slower; for sites the plain fetch returns nothing on)")
    a = ap.parse_args()
    global USE_BROWSER
    USE_BROWSER = a.browser
    base = a.website if a.website.startswith("http") else "https://" + a.website
    host = urlparse(base).netloc.replace("www.", "")
    home = fetch(base)
    res = {"website": base, "pages": [], "people": [], "emails": [], "linkedin": []}
    if not home:
        res["error"] = "homepage not reachable"
        print(json.dumps(res)); return
    links = []
    for h in home.css("a::attr(href)").getall():
        u = urljoin(base, str(h).split("#")[0])
        if urlparse(u).netloc.replace("www.", "") == host and PAGE_RE.search(urlparse(u).path) and not SKIP_PATH.search(urlparse(u).path) and u not in links:
            links.append(u)
    links.sort(key=lambda u: 0 if PRIORITY.search(urlparse(u).path) else 1)
    pages = [(base, home)] + [(u, p) for u in links[:a.max_pages] if (p := fetch(u))]
    seen_people, emails, lin = set(), set(), set()
    for url, page in pages:
        res["pages"].append(url)
        for h in page.css("a::attr(href)").getall():
            h = str(h)
            if h.startswith("mailto:"):
                emails.add(h[7:].split("?")[0].replace("%20", "").strip().lower())
            elif "linkedin.com/in/" in h:
                lin.add(h.split("?")[0])
        ls = lines_of(page)
        emails.update(e.lower() for l in ls for e in EMAIL_RE.findall(l))
        if JOB_PAGE.search(urlparse(url).path):
            continue  # job-listing pages hold job titles, not people; keep their emails only
        for i, l in enumerate(ls):
            for tier, rx in TIERS:
                if rx.search(l) and len(l) < 80:
                    # name is usually the line just before or after the title
                    cand = [x for x in (ls[i-1] if i else "", ls[i+1] if i+1 < len(ls) else "", l.split(",")[0].split(" - ")[0]) if NAME_RE.match(x) and not NOT_NAME.search(x)]
                    key = (cand[0] if cand else "", l)
                    if key not in seen_people:
                        seen_people.add(key)
                        res["people"].append({"tier": tier, "name": cand[0] if cand else "", "title": l, "page": url})
                    break
    res["people"].sort(key=lambda x: (x["tier"], x["name"] == ""))
    res["people"] = res["people"][:8]
    res["emails"] = sorted(e for e in emails if not JUNK_EMAIL.search(e))[:8]
    res["linkedin"] = sorted(lin)[:8]
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
