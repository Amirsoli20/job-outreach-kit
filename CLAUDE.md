# Daily Job Search and Outreach — {{FULL_NAME}}

> First time here? Run `/setup`. It asks who you are and what job you want, then replaces every placeholder in
> double curly braces in this project with your answers. Until then, the pipeline will not run.

## Who the candidate is
{{SENIORITY}} {{TARGET_ROLE}}, {{NATIONALITY}} national based in {{BASE_COUNTRY}}, speaks {{LANGUAGES}}.
Relocation: {{VISA_SITUATION}}. **Market focus: {{TARGET_MARKETS}}** — {{TARGET_ROLE}} jobs located in those
countries. No other country. Skills: {{SKILLS}}. Wants small teams (<{{COMPANY_SIZE_MAX}} people), {{COMPANY_TYPES}}.
Contract/freelance/informal work is a GOOD outcome, not a fallback.

## Pipeline (code does the mechanical part, Claude does judgment)
1. `python3 scripts/fetch_jobs.py` — Apify REST calls, title/market/big-company filter, dedupe →
   `data/candidates-<date>.json` (skips if today's file exists; `--force` to re-fetch). Needs `APIFY_TOKEN` env var.
   Search settings (markets, title keywords, exclusions) live in `config.json`, written by `/setup`.
   Never read `data/raw/` (wasteful).
2. `/daily-jobs` skill — Claude reads ONLY the candidates file, applies exclusions + tiering, outputs the table.
3. Every run is saved to local tables (no external database):
   - `data/job-runs.csv` — all candidates, tiers, drop reasons, contacts (full log).
   - `data/job-listings.csv` — Strong/Good jobs only, one row per job, with the contact email and draft status.
     `status` is yours to edit (Not Applied / In progress / Applied / Not worth); scripts never overwrite it.
   Both are written by `scripts/save_run_csv.py`.
4. Strong matches → `contact-finder` → emails saved in `data/job-listings.csv` → `outreach-drafter` reads the email
   from that table and creates a Gmail draft (never sends). No Gmail connector → the draft is saved in `drafts/`.
5. Company outreach follow ups are tracked in `data/outreach-database.csv` (`scripts/outreach_db.py`), with the timing
   rules in `docs/outreach-sequence.md`.

## Work-mode priority (drives tiering) — {{TARGET_MARKETS}}
1. Remote or remote-friendly role with an employer/entity in a target market — best odds
2. Hybrid in a target market with flexible/negotiable office requirement
3. On-site in a market where employer-sponsored visas are the default ({{SPONSOR_DEFAULT_MARKETS}}) — on-site is NOT
   capped at Good for relocation reasons there; tier it on seniority, skills and company fit. If the posting says no
   sponsorship, cap at Good.

## Markets where sponsorship is NOT the default
(Every target market not listed in {{SPONSOR_DEFAULT_MARKETS}}.)
- Employer visa sponsorship is NOT the default there. Remote open to {{BASE_COUNTRY}}/worldwide-eligible or stated
  visa sponsorship/relocation → can be Strong. On-site/hybrid with no visa mention → cap Good, note "no visa mentioned".
  Explicit "must have right to work" / "no sponsorship" → cap Good and say so. Remote restricted to residents → drop.
- Postings that require a local language not in {{LANGUAGES}} are dropped. Same size, junior-pay and trick-instruction
  rules apply.

## Hard exclusions (apply after fetch)
- **Not in scope.** Location outside {{TARGET_MARKETS}}, or "remote worldwide" / remote tied to another
  country or region → drop silently. Only roles located in those countries (or remote roles explicitly with an
  entity there) are in scope.
- Requires a language other than {{LANGUAGES}} (posting wholly in another language = requires it)
- "Remote" restricted to residents/citizens of a country OR region ("UK only", "EU only")
- Anything from "Hire Feed"; explicit "{{BASE_COUNTRY}} not eligible" (or sanctions wording that excludes it);
  "train AI systems" jobs
- Companies with {{COMPANY_SIZE_MAX}}+ employees, or any big/household/public/unicorn/subsidiary-of-large-parent signal
  (if no headcount and no big signal: keep but cap at Good, note "size unconfirmed")
- Look-alike roles from another field ({{LOOKALIKE_ROLES}}) — drop silently
- Ambiguous titles ({{AMBIGUOUS_TITLES}}): include only if they show {{RELEVANT_SIGNALS}}

## Tiers
- **Strong**: seniority fits ({{SENIORITY}}; junior roles count when pay is >= {{PAY_FLOOR}}; interns never;
  senior+ only if attainable), strong skill overlap, AND (open remote OR flexible hybrid OR explicit
  contract/freelance — contract can lift past a years-of-experience threshold)
- **Good**: held back by something specific (5+ yrs, on-site only, strict hybrid, size unconfirmed)
- **Weak**: never shown. Visa info and trick instructions are informational, never tier factors.
- Sponsorship-default markets ({{SPONSOR_DEFAULT_MARKETS}}): visa info stays informational unless the posting
  explicitly refuses sponsorship.

## Trick application instructions
Flag with "⚠️ <few words>" anything unusual required to apply (draw a face on CV, keyword in subject line, riddle,
video intro, exact file name…). Read the full posting — they're buried mid-paragraph. Ordinary CV/portfolio/cover
letter asks don't count.

## Output format (short!)
One summary line, then ONE table: `Match | Company | Website | Role | Location | Posted | Type | Link`
Strong first, then Good. Type = work mode, ⚠️ flag if any, employment type, visa info, gap/contract fragment.
Optional 1-3 sentence Notes line only if coverage was affected. No per-job prose, no country groupings.

## Rules
- Never send email. Drafts only.
- **Junior roles** are IN when stated pay is >= {{PAY_FLOOR}}. Pay unstated: keep, cap at Good, note "pay unstated".
  Pay stated below the floor and the role is junior: drop.
- **Missing contact info never removes a job.** If no website, no people or no email can be found, the row stays in
  the table with the contact shown as "not found"; only the outreach draft is skipped.
- Don't load unrelated skills.
- If the Apify monthly cap is hit, stop and flag it prominently.

## Token & cost efficiency (self-improving)
Goal: each run uses as few tokens and as little Apify spend as possible without lowering result quality.

**Standing rules (token side)**
- Code does the mechanical work (fetch, title/location/big-company filter, dedupe, description truncation); Claude only
  judges. Never read `data/raw/`; read only `data/candidates-<date>.json`, and only the fields needed.
- Cheapest check first: apply rules from the title/location/description snippet before any WebSearch/WebFetch. Web lookups
  only for jobs that otherwise look Strong/Good, max ONE per company, and reuse an earlier answer for the same company.
- Subagents only where isolation pays off (`scrape-verifier` on the candidates file, `contact-finder`/`outreach-drafter`
  per Strong company). Pass them file paths and the minimum context, not pasted data. Use a smaller model for
  mechanical agents where quality holds.
- Skip steps with no work: if the file already exists for today, don't re-fetch; if no Strong matches, skip
  contact-finder and outreach; if the verifier finds nothing, don't re-check.
- Output stays at the format above. No per-job prose, no restating the rules.

**Standing rules (Apify side)** — cost = memory × runtime, plus per-result fees and proxy/storage (docs.apify.com/platform/actors/running/usage-and-resources)
- Fewest actor calls (two per market in `fetch_jobs.py`); one batched call beats many small ones (start-up overhead).
- Cap results (`limit` per market in `config.json`) at what triage can use; raise only if recent runs hit the cap
  with Strong matches near the end.
- Narrow the search (target markets only, recent posts, title keywords) so fewer irrelevant items are paid for.
- Prefer lightweight (HTTP/Cheerio-style) actors over browser-based ones when quality is equal; set lowest workable memory
  and a run timeout so failed runs can't burn compute.
- Check the actor's pricing tab (per-result vs compute) before changing actors or limits.

**Self-improvement loop (do this at the END of every run)**
1. Append one line to `data/efficiency-log.md`: date, raw → candidates → verified → Strong/Good counts, Apify calls and
   (if visible) CU/cost, rough tokens, web lookups made.
2. Ask: what was wasted this run? (items dropped by the same rule every day, a source that never yields Strong, a
   web lookup that repeated, an agent step that found nothing.) If a cheaper way exists, make the change now:
   tighten a filter or limit in `config.json`, add a known-big company to `big_companies`, drop a no-op
   step from a skill, or trim an agent prompt.
3. Record each change in `data/efficiency-log.md` (what, why, expected saving) so it can be reverted.
4. Guardrails: never loosen a hard exclusion, drop a job that could be Strong, send email, or increase Apify spend
   without telling the user. A change that trades quality for savings needs the user's OK. If unsure, log it as a
   suggestion instead of applying it. Mention applied changes in one line under Notes.

**Scrape only what's needed (target markets, few fields)**
- The script keeps just: title, company, location, url, posted, description, plus `hints` (regex pre-flags: remote, hybrid,
  onsite, visa, excluded_country, ai_training, contract, pay, years) and `non_ascii_pct` (high = likely non-English
  posting). Use hints to decide fast; read the description only for jobs that survive.
- Descriptions are cut at boilerplate (EEO, "about us", benefits, privacy) and capped at 2500 chars. "How to apply" is
  never cut, because trick instructions hide there.
- No company-profile scraping (`scrapeCompany` stays False). Raw actor output is not saved unless `--keep-raw` is passed.
- Company info beyond the posting (size, contacts) comes only from the one-lookup-per-company rule, for Strong/Good jobs.

**Company website is mandatory.** Every row in the table needs the company's official website. The script keeps
`website` (and `company_linkedin`) when the scraper provides them. If `website` is empty, find it with ONE search for the
company (reuse the same lookup for size/contacts), and never guess a domain. If none is found, show "not found".
Look up websites only for jobs that reach the table (Strong/Good), not for every candidate.

**Contacts come from the company's own website.** After the Apify fetch gives us each company's website, `contact-finder`
runs `.venv/bin/python scripts/find_contacts.py <website>` (Scrapling: plain HTTP, no tokens) to pull ranked people
(CEO/Founder, then {{FIELD}} leads, then hiring managers), published emails and LinkedIn profile links. If it finds
nothing, one re-run with `--browser` (JavaScript rendering) is allowed; web search is only the fallback when it still
finds no people. LinkedIn job pages are never scraped with Scrapling.
