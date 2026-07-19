---
name: dayflow-pull
description: Pull Henry's Dayflow activity data (what he actually worked on, day by day, card by card, with accurate hours) straight from Dayflow's local SQLite DB — read-only. Use whenever Henry asks to check his Dayflow, compute real work hours, build a weekly/daily report of what he did, verify time spent on a project, or audit his activity. Computes overlap-merged wall-clock hours (Dayflow's own sums double-count) and flags corrupt cards instead of trusting the LLM summaries at face value.
---

# dayflow-pull

Read Henry's Dayflow data directly from its structured store — **do not** eyeball
the app or trust Dayflow's own hour totals. Dayflow is a screen-recording time
tracker whose cards are LLM/OCR-generated, so two things must be handled:

1. **Overlapping cards** — Dayflow sometimes emits duplicate/overlapping cards
   for the same span (esp. after re-analysis). `SUM(end_ts - start_ts)`
   double-counts them. Always **interval-merge** for real wall-clock hours.
2. **Corrupt timestamps** — occasional cards span days (a "System" card of
   1400+ hours was observed). Exclude any single card longer than ~3h and flag it.

## How to use

Run the helper (read-only; safe while Dayflow is running):

```bash
python3 ~/.claude/skills/dayflow-pull/pull.py                    # last 8 days, Work, per-day merged hours + cards
python3 ~/.claude/skills/dayflow-pull/pull.py --from 2026-07-08 --to 2026-07-14
python3 ~/.claude/skills/dayflow-pull/pull.py --day 2026-07-13   # one day, card by card
python3 ~/.claude/skills/dayflow-pull/pull.py --category all     # every category, not just Work
python3 ~/.claude/skills/dayflow-pull/pull.py --obs              # also dump the rawer `observations` layer
```

Categories: `Work` (default), `Personal`, `Distraction`, `Idle`, `System`, `all`.

## Data model (for ad-hoc queries)

DB: `~/Library/Application Support/Dayflow/chunks.sqlite` — **open `mode=ro` only.**

- `timeline_cards` — the summary cards: `day`, `start_ts`/`end_ts` (unix),
  `title`, `summary`, `detailed_summary`, `category`, `subcategory`, `metadata`
  (JSON incl. `appSites`), `is_deleted` (filter `=0`).
- `observations` — the finer, rawer layer beneath the cards (per-batch),
  joined via `batch_id`; use to sanity-check what a card claims vs. the
  underlying evidence (`llm_model` records which model produced it).
- `llm_calls` — Dayflow's own LLM invocations, if you need to audit how a card
  was derived (the "OCR-LLM might be wrong" check).
- `journal_entries`, `day_goals`, `daily_standup_entries` — journal/goals.

## Rules

- **Read-only, always.** `sqlite3 -readonly` / `?mode=ro`. Never write; the DB is live.
- **Report merged hours, not summed.** State when you excluded glitch cards.
- **Read the cards, don't hand-wave.** Cite actual card titles/times, and drop to
  `observations` when a card's claim looks off — that's the point of reading the
  structured data instead of guessing from a summary.
