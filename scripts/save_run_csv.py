#!/usr/bin/env python3
"""Save one run to the local tables (no external database).

Usage: python3 scripts/save_run_csv.py [--date YYYY-MM-DD] [--triage triage.json]

1. data/job-runs.csv     - master log, one row per candidate per run. Re-running a date replaces that date's rows.
2. data/job-listings.csv - Strong/Good jobs only, one row per job link. New jobs are added; known jobs get their
                           fields refreshed, except the user's own columns (status, date_added), which are kept.
                           The drafter reads contact_email / company_email from here.

Reads data/candidates-<date>.json. Optional triage JSON is a list of objects keyed by "url" with any of the
TRIAGE fields below (Claude's judgment: tier, drop_reason, contacts...). Candidates without a triage entry are
saved as "Unreviewed".
"""
import argparse, csv, json, datetime, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "job-runs.csv"
LISTINGS = ROOT / "data" / "job-listings.csv"
TRIAGE = ["tier", "drop_reason", "work_mode", "employment_type", "visa", "trick_flag", "headcount", "pay", "website",
          "contact_name", "contact_role", "contact_email", "company_email", "contact_linkedin", "outreach_draft", "notes"]
FIELDS = ["run_date", "tier", "company", "website", "title", "location", "posted", "work_mode", "employment_type",
          "visa", "trick_flag", "headcount", "pay", "contact_name", "contact_role", "contact_email", "company_email",
          "contact_linkedin", "outreach_draft", "drop_reason", "notes", "url", "source", "company_linkedin",
          "hints", "non_ascii_pct"]
LISTING_FIELDS = ["date_added", "match", "status", "role", "company", "website", "location", "work_mode",
                  "employment_type", "posted", "salary", "visa", "trick_flag", "contact_name", "contact_role",
                  "contact_email", "company_email", "contact_linkedin", "outreach_draft", "notes", "link"]
USER_OWNED = {"status", "date_added"}


def read_csv(path):
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path, fields, rows):
    path.parent.mkdir(exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:  # BOM so Excel/Numbers read UTF-8
        w = csv.DictWriter(f, fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--triage")
    a = ap.parse_args()

    cands = json.loads((ROOT / "data" / f"candidates-{a.date}.json").read_text())
    triage = {}
    if a.triage:
        triage = {t["url"]: t for t in json.loads(pathlib.Path(a.triage).read_text())}

    rows = []
    for c in cands:
        t = triage.get(c["url"], {})
        row = {k: c.get(k, "") for k in FIELDS}
        row["run_date"] = a.date
        row["hints"] = json.dumps(c.get("hints", {}), ensure_ascii=False)
        for k in TRIAGE:
            row[k] = t.get(k, "") or (row.get(k, "") if k == "website" else "")
        row["tier"] = row["tier"] or "Unreviewed"
        rows.append(row)

    old = [r for r in read_csv(OUT) if r["run_date"] != a.date]
    write_csv(OUT, FIELDS, old + rows)
    print(f"{OUT}: {len(rows)} rows for {a.date}, {len(old) + len(rows)} total")

    listings = read_csv(LISTINGS)
    by_link = {r["link"]: r for r in listings}
    added = updated = 0
    for r in rows:
        if r["tier"] not in ("Strong", "Good") or not r["url"]:
            continue
        new = {"date_added": a.date, "match": r["tier"], "status": "Not Applied", "role": r["title"],
               "salary": r["pay"], "link": r["url"],
               **{k: r[k] for k in LISTING_FIELDS if k in r}}
        if r["url"] in by_link:
            cur = by_link[r["url"]]
            cur.update({k: v for k, v in new.items() if k not in USER_OWNED and v})
            updated += 1
        else:
            listings.append(new)
            by_link[r["url"]] = new
            added += 1
    write_csv(LISTINGS, LISTING_FIELDS, listings)
    print(f"{LISTINGS}: {added} added, {updated} updated, {len(listings)} total")


if __name__ == "__main__":
    main()
