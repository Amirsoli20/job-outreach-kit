---
name: presend-inbox-check
description: Before any outreach email is drafted or sent, check the user's connected Gmail inbox for the last 24 hours, classify each thread, and recommend an action (reply, follow up, close out, ignore) with the reason. Use when asked to check the inbox before sending, "what action should I take", or before running company outreach.
---

# Pre-send inbox check

Purpose: educational and decision support. Recommend and explain; the user decides. Never send email, never modify Gmail (no labels, trash, or spam marks).

This skill orchestrates three subagents in `.claude/agents/`. It does the merging and talking to the user; the agents do the reading and the one allowed write.

| Agent | Job | Writes? |
|---|---|---|
| `inbox-classifier` | Classifies the last 24h of Gmail with an action and the rule behind it | No |
| `pipeline-reader` | Lists who is due today, matches replies to Outreach Database rows, proposes updates | No |
| `db-updater` | Applies approved Outreach Database updates | Yes, only after the user says yes |

## Local sources (no external database)

- Rules: `docs/outreach-sequence.md` (sequence timing: Day 14 Email 1, Day 17 LinkedIn, Day 20 Follow up, Day 34 Close out, then quarterly; max 4 touches per 90 days; never pitch capacity). The file is the source of truth; don't hardcode it here.
- Outreach Database: `data/outreach-database.csv`, read and written only through `scripts/outreach_db.py`.
- Job Listings: `data/job-listings.csv`. Columns include role, company, status (Not Applied / In progress / Applied / Not worth), match, work_mode, employment_type, link, posted, date_added, contact_email, outreach_draft, notes. Read-only in this skill.

## Steps

1. **Run `inbox-classifier` and `pipeline-reader` in parallel** (one message, two Agent calls).
   - `inbox-classifier`: it reads `docs/outreach-sequence.md`, searches `in:inbox newer_than:1d` and returns a classified list.
   - `pipeline-reader`: it returns companies due today. Once the classifier finishes, send its company replies to `pipeline-reader` (via SendMessage) so it can match them to rows and propose updates.
2. **Match job-related threads to Job Listings.** For each recruiter, application or interview thread, search `data/job-listings.csv` for the company (and role if clear). Report the row's current status and suggest the next one (for example Not Applied → Applied after a confirmation email, or flag an interview). If no row matches, say so; do not create rows.
3. **Merge** into the output below. Recommendations per class:
   - Positive or neutral company reply: respond, set the company's stage to "In conversation".
   - Referral to someone else: draft a short note to the new contact; do not cold-pitch them with Email 1.
   - Negative reply: no further touches; note it.
   - Bounce: find the correct address; do not resend to the same one.
   - Out-of-office: wait; re-time the next touch for after they return.
   - Job-related: flag first, ahead of outreach.
   - Noise: ignore.
4. **Ask the user to approve** the proposed Outreach Database updates. Only after an explicit yes, call `db-updater` with the approved list and say it is approved by the user. Setting `stage` to "Removed - do not contact" needs a separate yes per row.
5. Job Listings status changes are proposals only unless the user asks; then edit only that row's `status` cell.

## Output (short)

One summary line (counts: replies, bounces, job-related, noise, outreach due today), then ONE table:

`Thread | What it means | Recommended action | Why`

The "Why" column names the rule behind the call (for example, "no reply by Day 20, so the follow up must add something new, not a bump"). Keep it to one sentence; this column is the learning part.

Then: "Due today" (from the database), "Proposed Outreach Database updates" (row → fields → new values, or "none"), "Job Listings matches" (or "none"), and a one-line verdict: safe to proceed with today's outreach, or what to handle first.

## Rules

- Never send. Drafts only, and only if the user asks.
- Only `db-updater` writes to the Outreach Database, and only after approval.
- Don't load the `daily-jobs` skill; this skill runs before it, separately.
- If nothing needs action, say so plainly instead of padding.
