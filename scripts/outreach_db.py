#!/usr/bin/env python3
"""The local Outreach Database: data/outreach-database.csv. Stdlib only. Prints JSON.

Usage:
  python3 scripts/outreach_db.py due [--date YYYY-MM-DD]       rows due for a touch (read)
  python3 scripts/outreach_db.py find "<text>"                  match company / contact_email / company_email (read)
  python3 scripts/outreach_db.py show <id>                      one row (read)
  python3 scripts/outreach_db.py options                        allowed values for select-style columns (read)
  python3 scripts/outreach_db.py update <id> <field> "<new>" --expect "<current>"   change one field (write)
  python3 scripts/outreach_db.py append <id> what_i_said "YYYY-MM-DD: <angle>"      append a line (write)
  python3 scripts/outreach_db.py add --company "X" [--field value ...]              new row, for the user (write)

Timing rules for next_action / next_action_date: docs/outreach-sequence.md.
"""
import argparse, csv, datetime, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "outreach-database.csv"
FIELDS = ["id", "company", "website", "contact_name", "contact_email", "company_email", "email_status",
          "sequence_step", "stage", "next_action", "next_action_date", "last_touched", "what_i_said", "notes"]
OPTIONS = {
    "stage": ["Prospect", "In sequence", "In conversation", "Cold pool", "Dead", "Removed - do not contact"],
    "email_status": ["Not sent", "Sent", "Bounced", "Out of office", "Replied - interested", "Replied - wants call",
                     "Replied - not now", "Replied - no", "Unsubscribed"],
    "sequence_step": ["Not started", "Email 1 sent", "LinkedIn sent", "Follow-up 1 sent", "Close-out sent", "Quarterly"],
}
INACTIVE = {"Removed - do not contact", "Dead", "Cold pool"}
APPEND_ONLY = {"what_i_said"}
DATES = {"next_action_date", "last_touched"}


def load():
    if not DB.exists():
        return []
    with DB.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def save(rows):
    DB.parent.mkdir(exist_ok=True)
    with DB.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def out(x):
    print(json.dumps(x, ensure_ascii=False, indent=1))


def row_of(rows, rid):
    for r in rows:
        if r["id"] == rid:
            return r
    sys.exit(f"ERROR: id {rid} not found")


def check_value(field, value):
    if field not in FIELDS or field == "id":
        sys.exit(f"ERROR: unknown field {field}")
    if field in OPTIONS and value not in OPTIONS[field]:
        sys.exit(f"ERROR: {value!r} is not an allowed {field}: {OPTIONS[field]}")
    if field in DATES and value:
        try:
            datetime.date.fromisoformat(value)
        except ValueError:
            sys.exit(f"ERROR: {field} must be YYYY-MM-DD")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("due"); s.add_argument("--date", default=datetime.date.today().isoformat())
    s = sub.add_parser("find"); s.add_argument("text")
    s = sub.add_parser("show"); s.add_argument("id")
    sub.add_parser("options")
    s = sub.add_parser("update"); s.add_argument("id"); s.add_argument("field"); s.add_argument("value")
    s.add_argument("--expect", required=True, help="current value; the update is refused if it differs")
    s = sub.add_parser("append"); s.add_argument("id"); s.add_argument("field"); s.add_argument("line")
    s = sub.add_parser("add"); s.add_argument("--company", required=True)
    for f in FIELDS[2:]:
        s.add_argument(f"--{f}", default="")
    a = ap.parse_args()
    rows = load()

    if a.cmd == "options":
        return out(OPTIONS)
    if a.cmd == "due":
        return out([r for r in rows if r["next_action_date"] and r["next_action_date"] <= a.date
                    and r["stage"] not in INACTIVE])
    if a.cmd == "find":
        t = a.text.lower().strip()
        return out([r for r in rows if t and (t in r["company"].lower() or t == r["contact_email"].lower()
                                              or t == r["company_email"].lower())])
    if a.cmd == "show":
        return out(row_of(rows, a.id))
    if a.cmd == "update":
        r = row_of(rows, a.id)
        if a.field in APPEND_ONLY:
            sys.exit(f"ERROR: {a.field} is append-only; use append")
        check_value(a.field, a.value)
        if r[a.field] != a.expect:
            sys.exit(f"MISMATCH: {a.field} is {r[a.field]!r}, expected {a.expect!r}; nothing changed")
        old, r[a.field] = r[a.field], a.value
        save(rows)
        return out({"id": a.id, "company": r["company"], "field": a.field, "old": old, "new": a.value})
    if a.cmd == "append":
        if a.field not in APPEND_ONLY:
            sys.exit(f"ERROR: append only works on {sorted(APPEND_ONLY)}")
        r = row_of(rows, a.id)
        r[a.field] = (r[a.field] + "\n" if r[a.field] else "") + a.line
        save(rows)
        return out({"id": a.id, "company": r["company"], "field": a.field, "added": a.line})
    if a.cmd == "add":
        new = {f: getattr(a, f, "") for f in FIELDS[1:]}
        for f, v in new.items():
            if v:
                check_value(f, v)
        new["id"] = str(max((int(r["id"]) for r in rows if r["id"].isdigit()), default=0) + 1)
        new["stage"] = new["stage"] or "Prospect"
        new["email_status"] = new["email_status"] or "Not sent"
        new["sequence_step"] = new["sequence_step"] or "Not started"
        rows.append(new)
        save(rows)
        return out(new)


if __name__ == "__main__":
    main()
