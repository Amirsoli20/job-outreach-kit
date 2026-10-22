# Outreach sequence rules

The source of truth for when to contact a company again. `inbox-classifier`, `pipeline-reader` and
`db-updater` all read this file. Rows live in `data/outreach-database.csv` (edit only through `scripts/outreach_db.py`).

## Timing

Day 0 is the day the company is added to the database.

| Day | Touch | sequence_step after it |
| --- | --- | --- |
| 14 | Email 1 | Email 1 sent |
| 17 | LinkedIn message or connection | LinkedIn sent |
| 20 | Follow up 1 (must add something new, never a bump) | Follow-up 1 sent |
| 34 | Close out (short, friendly, door left open) | Close-out sent |
| then quarterly | One light touch every 3 months | Quarterly |

- Max 4 touches per 90 days.
- Never pitch capacity ("I have time free", "I can take on work"). Every touch offers something useful instead.
- After each touch: set `last_touched` to today, `next_action` and `next_action_date` to the next step above, and
  append one line to `what_i_said` (`YYYY-MM-DD: <angle>`) so the next touch never repeats it.

## Replies

| Reply | Action |
| --- | --- |
| Interested / wants a call / not now | Respond; set stage to "In conversation"; stop the sequence |
| Referred me to someone else | Short note to the new contact; do not send them Email 1 |
| No / no budget / has a team / hostile / unsubscribe | No further touches; stage "Dead" (or "Removed - do not contact" for unsubscribe/hostile, with the user's OK) |
| Bounce | Find the right address; never resend to the same one |
| Out of office | Wait; move next_action_date to after they return |

## Allowed values

Run `python3 scripts/outreach_db.py options` for the exact list the script accepts.
