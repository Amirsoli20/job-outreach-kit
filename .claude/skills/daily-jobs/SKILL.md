---
name: daily-jobs
description: Run the daily {{TARGET_ROLE}} job search - fetch candidates via the Apify script, triage into Strong/Good matches, output the table, save it to the local job tables, and create Gmail outreach drafts for Strong matches using the emails in that table. Use when asked to run the daily job search or /daily-jobs.
---

# Daily jobs routine

Scope: {{TARGET_ROLE}} jobs in {{TARGET_MARKETS}} (see CLAUDE.md).

If CLAUDE.md still contains `{{` placeholders or `config.json` has no markets, stop and tell the user to run `/setup` first.

Follow the rules in CLAUDE.md (profile, exclusions, tiers, output format). Steps:

1. **Fetch.** Run `python3 scripts/fetch_jobs.py` (needs `APIFY_TOKEN`). It skips the fetch by itself when today's
   `data/candidates-<date>.json` exists; pass `--force` only if the user asks to refresh. If it exits with a usage-cap
   or auth error, report that in one line and stop. If the file has 0 candidates, report that and skip steps 2-7.
2. **Verify.** Delegate to the `scrape-verifier` subagent with the candidates file path. Drop its `DROP` rows;
   resolve `CHECK` rows during triage (or note them).
3. **Triage.** Read only `data/candidates-<date>.json`. For each candidate apply the hard exclusions from CLAUDE.md
   using the description text. If a company's size is unclear and it matters, do ONE quick WebSearch/WebFetch on
   its About/LinkedIn page — only for jobs that otherwise look Strong or Good.
   Extract: work mode, company website (from `website`; if empty, one search, never guess), employment type, visa info, contractor signal, trick instruction, headcount.
   Reuse the verifier's evidence instead of re-reading descriptions it already judged, and reuse one lookup per company.
4. **Report.** Summary line + the single table, per CLAUDE.md. No Weak matches.
5. **Contacts (Strong only).** For each Strong match, run the `contact-finder` subagent (one per distinct company).
   Copy its `SAVE:` line into that job's triage entry (`contact_name`, `contact_role`, `contact_email`,
   `company_email`, `contact_linkedin`). If it returns SKIPPED, keep the job with contact "not found" and the reason.
6. **Save the tables.** Write a triage JSON to the scratchpad: a list of objects keyed by `url` for EVERY candidate
   (Strong, Good and dropped), with fields `tier` (Strong/Good/Dropped), `drop_reason`, `work_mode`,
   `employment_type`, `visa`, `trick_flag`, `headcount`, `pay`, `website` (if you found one), `contact_name`,
   `contact_role`, `contact_email`, `company_email`, `contact_linkedin`, `outreach_draft` ("pending" for Strong jobs
   with an email, otherwise "no: <reason>"), `notes`. Then run `python3 scripts/save_run_csv.py --triage <that file>`.
   It writes `data/job-runs.csv` (all candidates; replaces same-date rows) and adds/updates Strong and Good jobs in
   `data/job-listings.csv` (one row per job link; the user's `status` column is never overwritten).
   Use only data already gathered; no extra lookups for this step.
7. **Drafts (Strong with an email).** For each Strong job whose row in `data/job-listings.csv` has a `contact_email`
   or `company_email`, delegate to `outreach-drafter` with the job link (one call per distinct company). It reads the
   address from the table and creates the Gmail draft (or saves it to `drafts/` if Gmail is not connected).
   Then set each job's `outreach_draft` in the triage JSON to the result ("gmail", "local file" or "no: <reason>"),
   add any address the drafter found, and re-run `python3 scripts/save_run_csv.py --triage <that file>`.
   Then add the one-line reporting summary:
   "Drafted N outreach emails for M strong matches (K skipped — reason)."
   A company with no findable contacts STAYS in the table (contact "not found"); only its draft is skipped. Name skip
   reasons explicitly (anonymized / existing history / identity unverified / duplicate company / no contact).
8. **Log.** Do the self-improvement loop from CLAUDE.md: one line in `data/efficiency-log.md`, plus any change made.

Final reply = summary line + table + outreach line + optional Notes. Nothing else.
