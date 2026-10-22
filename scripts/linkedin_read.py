#!/usr/bin/env python3
"""Read a PUBLIC LinkedIn company/profile page via Jina Reader (no login, no account automation).

Usage: python3 scripts/linkedin_read.py <linkedin url> [--max-chars 1800]
Prints trimmed text only. Login-walled pages return little; that is expected, don't retry.
"""
import argparse, re, sys, urllib.request

ap = argparse.ArgumentParser()
ap.add_argument("url")
ap.add_argument("--max-chars", type=int, default=1800)
a = ap.parse_args()
if "linkedin.com/" not in a.url:
    sys.exit("only linkedin.com URLs")
req = urllib.request.Request("https://r.jina.ai/" + a.url, headers={"User-Agent": "Mozilla/5.0", "Accept": "text/plain"})
try:
    txt = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
except Exception as e:
    sys.exit(f"fetch failed: {e}")
txt = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", txt)          # drop images
txt = re.sub(r"\(https?://[^)]*\)", "", txt)             # drop link targets
txt = re.sub(r"\n{3,}", "\n\n", txt).strip()
print(txt[: a.max_chars] if len(txt) > 200 else "WALLED/EMPTY: " + txt)
