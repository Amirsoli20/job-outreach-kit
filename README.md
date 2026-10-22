# Job Search and Outreach Kit for Claude Code

A daily job search that runs inside [Claude Code](https://claude.com/claude-code). Each day it:

1. pulls new job posts from LinkedIn and Indeed through Apify, in the countries you choose,
2. filters out the noise (wrong field, big companies, other languages, remote jobs you can't take),
3. sorts what's left into **Strong** and **Good** matches and saves them to a table in the project,
4. finds the right person to email at each Strong match, from the company's own website,
5. writes a short, personal email to them in a warm, honest voice and saves it as a **Gmail draft**.

It never sends email. You read every draft and decide.

It works for any job. Nothing about the role is built in: the job title, the field, who to contact, what to offer
in emails and where to search are all placeholders. Run `/setup` first and tell it what job you want. It then builds
the whole system around that job: search keywords, filters, contact titles, email examples and your profile.

## What you need

- Claude Code
- Python 3.10+
- An [Apify](https://apify.com) account. The free plan works for a small daily search.
- Optional: the Gmail connector in Claude (claude.ai → Settings → Connectors → Gmail). Drafts go to your own Gmail.
  Without it, drafts are saved as files in `drafts/`.

## Get started

```bash
git clone <this repo> && cd <repo>
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/scrapling install          # optional: lets the contact finder read JavaScript-heavy sites
export APIFY_TOKEN=your_token_here   # put this in your shell profile; never commit it
claude
```

Then, in Claude Code:

```
/setup        # once: tell it who you are and what job you want
/daily-jobs   # every day
```

## How it works

| Piece | What it does |
| --- | --- |
| `CLAUDE.md` | Your profile and the rules for which jobs count: markets, exclusions, Strong vs Good |
| `profile.md` | Your answers to `/setup`. `scripts/apply_profile.py` copies them into every placeholder |
| `config.json` | Search settings: markets, title keywords, look-alike roles to drop, big companies to skip |
| `scripts/fetch_jobs.py` | Calls Apify and does the cheap filtering in code, so Claude spends fewer tokens |
| `scripts/find_contacts.py` | Reads a company's team and contact pages for names, titles and emails (no tokens) |
| `scripts/save_run_csv.py` | Writes the tables below |
| `scripts/outreach_db.py` | Reads and updates the outreach database with checks (allowed values, append-only notes) |
| `.claude/skills/daily-jobs` | The daily routine |
| `.claude/skills/email-tone-of-voice` | How every email is written: voice, hard rules, shape, opening question, checklist |
| `.claude/skills/presend-inbox-check` | Checks the last 24h of your inbox before outreach and suggests what to do |
| `.claude/skills/setup` | First-run interview |
| `.claude/agents/*` | Small helpers: verify the scrape, find contacts, draft emails, read and update the database |
| `docs/outreach-sequence.md` | When to follow up (Day 14, 17, 20, 34, then quarterly) and how to handle replies |

## Your data stays in the project

There is no external database. Everything is saved as CSV files in `data/`, which open in Excel, Numbers or Google
Sheets:

- `data/job-listings.csv`: one row per Strong or Good job, with the contact email and draft status. Track your
  progress in the `status` column (Not Applied / In progress / Applied / Not worth). Scripts never overwrite it.
- `data/job-runs.csv`: the full log of every job checked, including the ones that were dropped and why.
- `data/outreach-database.csv`: companies you contact directly, with your follow up timing.

`data/` and `drafts/` are in `.gitignore`, so they are never committed.

## The emails

No two emails are the same. There are no templates, only rules. An email opens with a question about the reader's
situation, names one problem in plain words, offers one small free piece of work they keep either way, and ends with
one easy question. It has no dashes, no sales phrases and no list of credentials, and it stays under 100 words. See
`.claude/skills/email-tone-of-voice/SKILL.md`.

## Privacy

After `/setup`, `CLAUDE.md`, `profile.md` and the skills contain your personal details. Keep your own copy in a
**private** repo, or don't push it after setup.
