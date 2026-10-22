---
name: setup
description: First-run setup. Asks the user who they are and what job they are looking for, fills profile.md, replaces every {{PLACEHOLDER}} in the project with their answers, writes config.json for the job search, and tailors the email examples to their field. Use when the user runs /setup, says they are new, or when another skill finds leftover placeholders.
---

# Setup

The project ships with placeholders (`{{FULL_NAME}}`, `{{TARGET_ROLE}}`, ...) instead of one person's details.
This skill turns it into the user's own copy. The rules, tone of voice, shape of an email and pipeline stay
exactly as they are; only the personal and job-specific parts change.

## 1. Check the state

Run `python3 scripts/apply_profile.py --check`. If it reports 0 placeholders left, setup was already done:
ask what the user wants to change and edit those files directly instead of re-running everything.

## 2. Start with the job

Nothing in this project assumes a field. The job the user names drives everything: search keywords, title filters,
look-alike roles to drop, who to contact, what free work to offer and the email examples.

Ask one open question: "What job are you looking for, and where? Then tell me a little about yourself."
If the job is vague ("something in tech"), ask them to name one or two exact job titles before going on.
Fill as much of `profile.md` as you can from the answer, then ask only for what is still missing (group the
remaining questions; use AskUserQuestion for choices like company size or sign off). Every key in `profile.md` needs
a value; "none" is a valid value where the file says so. Never invent personal facts.

Suggest sensible defaults from the examples in `profile.md` when the user has no preference (for example
COMPANY_SIZE_MAX 50, SIGN_OFF "Hug"), and say they are defaults.

## 3. Fill in and apply

1. Write the answers into `profile.md` (one value after each `=`).
2. Run `python3 scripts/apply_profile.py`. It replaces every placeholder in CLAUDE.md, `.claude/` and `docs/` and
   lists anything still missing. Fix and re-run until it reports 0 left.

## 4. Write config.json (the job search)

Fill `config.json` from the profile. Keep the existing `banned_companies`, `big_companies` and `big_company_phrases`
lists and add 20-40 well-known large employers in the user's field and markets (lowercase company names).
- `linkedin_keywords`: 3-5 words covering the role titles (for example "Backend Developer Engineer").
- `indeed_query`: the role titles and close variants OR-ed in quotes (for example `"Backend Developer" OR "Backend Engineer"`).
- `title_regex`: a case-insensitive regex that matches real titles for the role and its close variants.
- `exclude_title_regex`: words that mark look-alike roles from another field (from LOOKALIKE_ROLES), or "".
- `contact_tier2_regex`: the field's leadership titles (from FIELD_LEADERSHIP_TITLES), as a regex.
- `contact_tier3_regex`: the hiring manager titles (from HIRING_MANAGER_TITLES), as a regex.
- `excluded_country_regex`: words that flag the user's eligibility issue, for example `\b<country>\b|sanction`, or "".
- `markets`: one object per target country: `label`, `linkedin_location` (country name as LinkedIn writes it),
  `indeed_country` (Indeed country code such as "uk", "nl", "ae", "us", "de", or "" if Indeed has no site there),
  `limit` (40), `location_terms` (country name, common short names and the 10-15 biggest cities, lowercase),
  `local_language_words` (8-12 common words of the local language if it is not one the user speaks, else []).

Then run `python3 scripts/fetch_jobs.py --dry-run`. It must list the planned calls with no error.

## 5. Tailor the email examples to their field

Read `.claude/skills/email-tone-of-voice/SKILL.md`. The tables of examples (ad vs person, weak vs strong opening,
worry vs convincing reason, sentence fixes) are general patterns filled with the user's placeholders. Rewrite
every example cell so it sounds like someone in the user's field talking about real moments from that work,
keeping the same pattern, length and emotional pull. Also check the subject line and question examples in "The
shape of an email". Do NOT change the voice, the five traits, the hard rules, the shape of an email, the notes on making
an email resonate, or the checklist.

## 6. Connections

- **Apify:** the user needs an Apify account and `export APIFY_TOKEN=...` in their shell. Never write the token into a file.
- **Gmail:** drafts go to whichever Gmail account the user connected in Claude (claude.ai → Settings → Connectors →
  Gmail). If no Gmail connector is available, drafts are saved as files in `drafts/` instead. Nothing is ever sent.
- **Scrapling (contact finder):** `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`, plus
  `.venv/bin/scrapling install` for the optional `--browser` mode.

## 7. Finish

Tell the user in a few lines: what was filled in, any default you chose, what is left for them (token, Gmail, venv),
and that `/daily-jobs` is ready. Remind them that after setup the files contain their personal details, so their
own copy should stay a private repo.
