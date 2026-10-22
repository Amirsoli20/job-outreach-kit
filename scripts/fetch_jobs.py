#!/usr/bin/env python3
"""Fetch, filter and dedupe jobs from Apify. Stdlib only.

Usage: APIFY_TOKEN=... python3 scripts/fetch_jobs.py [--dry-run]
Scope and filters (markets, title keywords, big companies) come from config.json, written by /setup.

Writes data/candidates-<date>.json (title/location/big-company-filtered, deduped survivors with a
truncated description). Claude only reads the candidates file. Raw actor output is saved to
data/raw/<date>/ only with --keep-raw. Skips the fetch if today's file exists (use --force).
"""
import argparse, json, os, re, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINKEDIN = "curious_coder~linkedin-jobs-scraper"
INDEED = "borderline~indeed-scraper"

LEGAL_RE = re.compile(r"[,.]?\s*\b(llc|l\.l\.c|fz[- ]?llc|fze|fzco|dmcc|inc|ltd|limited|plc|corp(oration)?|co|gmbh|"
                      r"pjsc|group|holding|uae|middle east|mena|bv|b\.v|nv|sa|ag)\.?$", re.I)
# Boilerplate that carries no decision signal; description is cut at the first match.
BOILER_RE = re.compile(r"equal (opportunity|employment)|we are an equal|about (us|the company)\b|what we offer|our benefits|"
                       r"benefits:|perks|privacy (policy|notice)|data protection", re.I)
HINTS = {  # cheap regex pre-flags so Claude doesn't have to hunt for them
    "remote": r"\bremote\b", "hybrid": r"\bhybrid\b", "onsite": r"on[- ]?site|in[- ]office",
    "visa": r"visa|sponsor", "ai_training": r"train(ing)? (ai|ml|llm)|rlhf|annotat",
    "contract": r"contract|freelance|part[- ]time",
    "pay": r"[$€£]\s?[\d,]{4,}|\b(aed|usd|eur|gbp)\s?[\d,]{4,}|salary|per (month|year|annum)",
    "years": r"\d\+?\s*(\+|-|to)?\s*\d*\s*years",
}
# "How to apply" is never cut (trick instructions hide there); re-appended if the boilerplate cut removed it.
APPLY_RE = re.compile(r"how to apply|to apply,|application process|apply (by|via|with)|in (the|your) subject line", re.I)


def load_config():
    path = ROOT / "config.json"
    if not path.exists():
        sys.exit("config.json missing. Run /setup in Claude Code first.")
    cfg = json.loads(path.read_text())
    if not cfg.get("markets") or not cfg.get("title_regex"):
        sys.exit("config.json has no markets or title_regex yet. Run /setup in Claude Code first.")
    cfg["_title"] = re.compile(cfg["title_regex"], re.I)
    cfg["_exclude"] = re.compile(cfg["exclude_title_regex"], re.I) if cfg.get("exclude_title_regex") else None
    cfg["_banned"] = {n.lower().strip() for n in cfg.get("banned_companies", [])}
    cfg["_big"] = {n.lower().strip() for n in cfg.get("big_companies", [])}
    cfg["_big_phrases"] = [p.lower() for p in cfg.get("big_company_phrases", [])]
    cfg["_loc"], cfg["_lang"] = {}, {}
    for m in cfg["markets"]:
        terms = "|".join(re.escape(t.lower()).replace(r"\ ", r"[- ]") for t in m.get("location_terms", []))
        cfg["_loc"][m["label"]] = re.compile(rf"\b({terms})\b", re.I) if terms else None
        words = "|".join(re.escape(w.lower()) for w in m.get("local_language_words", []))
        cfg["_lang"][m["label"]] = re.compile(rf"\b({words})\b", re.I) if words else None
    if cfg.get("excluded_country_regex"):
        HINTS["excluded_country"] = cfg["excluded_country_regex"]
    return cfg


def pick(item, *keys):
    for k in keys:
        v = item.get(k)
        if v:
            return v if not isinstance(v, dict) else (v.get("name") or v.get("formattedAddressLong") or v.get("city")
                                                       or json.dumps(v))
    return ""


def _api(method, url, payload=None, timeout=60):
    req = urllib.request.Request(url, data=json.dumps(payload).encode() if payload is not None else None, method=method,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def run_actor(actor, payload, token):
    """Async run + poll + dataset fetch. The sync endpoint drops long connections (paid results get lost)."""
    base = "https://api.apify.com/v2"
    try:
        run = _api("POST", f"{base}/acts/{actor}/runs?token={token}&timeout=240", payload)["data"]
        deadline = time.time() + 270
        while run["status"] in ("READY", "RUNNING") and time.time() < deadline:
            time.sleep(6)
            run = _api("GET", f"{base}/actor-runs/{run['id']}?token={token}")["data"]
        if run["status"] != "SUCCEEDED":
            return {"error": f"run {run['id']} ended {run['status']}"}
        return _api("GET", f"{base}/datasets/{run['defaultDatasetId']}/items?token={token}&clean=true", timeout=120)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:300]
        if "usage" in body.lower() and "limit" in body.lower():
            sys.exit(f"APIFY MONTHLY USAGE CAP HIT — stopping. {body}")
        return {"error": f"HTTP {e.code}: {body}"}
    except Exception as e:  # network/timeout
        return {"error": str(e)}


def build_jobs(cfg, days=None):
    jobs = []
    for m in cfg["markets"]:
        jobs.append((m["label"], "linkedin", LINKEDIN, {"keywords": cfg["linkedin_keywords"], "location": m["linkedin_location"],
                     "datePosted": "pastMonth" if days and days > 7 else "past24Hours" if days == 1 else "pastWeek",
                     "limitPerSource": m.get("limit", 40), "scrapeCompany": False}))
        if m.get("indeed_country") and cfg.get("indeed_query"):
            jobs.append((m["label"], "indeed", INDEED, {"country": m["indeed_country"], "query": cfg["indeed_query"],
                         "fromDays": str(days or 3), "sort": "date", "maxRows": 20,
                         "enableUniqueJobs": True, "includeSimilarJobs": False}))
    return jobs


def normalize(item, market, source):
    return {
        "market": market,
        "source": source,
        "title": pick(item, "title", "jobTitle", "positionName"),
        "company": pick(item, "companyName", "company", "employer"),
        "location": pick(item, "location", "jobLocation", "city"),
        "website": re.sub(r"^https?://([a-z]+\.)?(indeed|linkedin)\.com/.*", "",
                          pick(item, "companyWebsite", "companyWebsiteUrl", "companyUrl", "website", "employerWebsite")),
        "company_linkedin": pick(item, "companyLinkedinUrl", "companyLink", "companyProfileUrl"),
        "url": pick(item, "link", "url", "jobUrl", "applyUrl"),
        "posted": pick(item, "postedAt", "datePosted", "postedDate", "date"),
        "description": pick(item, "descriptionText", "description", "descriptionHtml", "snippet"),
    }


def keep(j, cfg):
    t, c = j["title"], j["company"].lower().strip()
    base = c
    while (s := LEGAL_RE.sub("", base).strip()) != base:
        base = s
    if not cfg["_title"].search(t) or (cfg["_exclude"] and cfg["_exclude"].search(t)):
        return False
    loc_re = cfg["_loc"].get(j["market"])
    if j["location"] and loc_re and not loc_re.search(j["location"]):
        return False  # location must match the market searched (empty location kept; scrape-verifier checks it)
    lang_re = cfg["_lang"].get(j["market"])
    if lang_re and len(lang_re.findall(j["description"][:1500])) >= 3:
        return False  # posting in a local language the user doesn't work in
    if c in cfg["_banned"] or base in cfg["_big"] or any(p in c for p in cfg["_big_phrases"]):
        return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="list planned calls, make none")
    ap.add_argument("--keep-raw", action="store_true", help="also save full raw actor output (off by default)")
    ap.add_argument("--only", default="", help="comma list of market labels/codes to run (substring match)")
    ap.add_argument("--force", action="store_true", help="re-fetch even if today's candidates file exists")
    ap.add_argument("--days", type=int, default=None, help="widen the window (e.g. 14): Indeed fromDays=N, LinkedIn pastMonth if N>7")
    a = ap.parse_args()
    cfg = load_config()
    jobs = build_jobs(cfg, a.days)
    if a.only:
        wanted = [w.strip().lower() for w in a.only.split(",")]
        jobs = [j for j in jobs if any(w in j[0].lower() or w == j[3].get("country", "") for w in wanted)]
    today = date.today().isoformat()
    path = ROOT / "data" / f"candidates-{today}.json"
    if path.exists() and not a.force and not a.dry_run:
        print(f"{path.name} already exists, skipping fetch (no Apify spend). Use --force to re-fetch.")
        return
    print(f"{len(jobs)} actor calls planned ({', '.join(m['label'] for m in cfg['markets'])})")
    if a.dry_run:
        for m, s, _, p in jobs:
            print(f"  {s:8} {m}")
        return
    token = os.environ.get("APIFY_TOKEN") or sys.exit("Set APIFY_TOKEN env var.")
    (ROOT / "data").mkdir(exist_ok=True)
    raw_dir = ROOT / "data" / "raw" / today
    if a.keep_raw:
        raw_dir.mkdir(parents=True, exist_ok=True)

    results = []
    with ThreadPoolExecutor(max_workers=4) as pool:  # free Apify accounts cap concurrent runs
        futs = [(m, s, pool.submit(run_actor, actor, p, token)) for m, s, actor, p in jobs]
        for m, s, f in futs:
            data = f.result()
            if a.keep_raw:
                (raw_dir / f"{s}-{m}.json").write_text(json.dumps(data, indent=1))
            if isinstance(data, dict) and "error" in data:
                print(f"  ! {s} {m}: {data['error'][:120]}")
                continue
            if data and isinstance(data, list) and set(data[0].keys()) == {"error"}:
                print(f"  ! {s} {m}: bare error item, skipped")
                continue
            results += [normalize(i, m, s) for i in data]
            print(f"  ok {s:8} {m}: {len(data)} raw")

    seen_file = ROOT / "data" / "seen.json"  # jobs already shown on earlier runs: skipped so the wider window adds only new ones
    old = set(json.loads(seen_file.read_text())) if seen_file.exists() else set()
    seen, out = set(old), []
    for j in results:
        if not keep(j, cfg):
            continue
        # same job often appears on LinkedIn and Indeed with different URLs, so dedupe on company+title too
        keys = {j["url"], f'{j["company"]}|{j["title"]}'.lower()} - {"", "|"}
        if keys & seen:
            continue
        seen |= keys
        d = re.sub(r"<[^>]+>", " ", j["description"])
        d = re.sub(r"\s+", " ", d)
        cut = BOILER_RE.search(d, 400)  # keep at least the first 400 chars
        if cut:
            m = APPLY_RE.search(d, cut.start())
            d = d[:cut.start()] + (" … " + d[m.start():m.start() + 600] if m else "")
        j["description"] = d[:2500]
        j["hints"] = [k for k, rx in HINTS.items() if re.search(rx, d, re.I)]
        j["non_ascii_pct"] = round(100 * sum(ord(c) > 127 for c in d) / max(len(d), 1))
        out.append(j)
    seen_file.write_text(json.dumps(sorted(seen)))
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(f"\n{len(results)} raw -> {len(out)} candidates after title/big-company/dedupe filters")
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
