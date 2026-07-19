#!/usr/bin/env python3
"""
Pull Dayflow activity data straight from its local SQLite DB — READ-ONLY.

Why this exists: Dayflow's own per-card durations DOUBLE-COUNT overlapping
cards and occasionally emit corrupted timestamps (a card ~59 days long), so a
naive SUM(end-start) inflates hours. This computes real wall-clock time by
MERGING overlapping intervals, and flags the glitchy cards instead of trusting
them — the point is to read the structured data, not Dayflow's LLM summary at
face value.

Usage:
  pull.py                         # last 8 days, per-day merged hours + work cards
  pull.py --from 2026-07-08 --to 2026-07-14
  pull.py --day 2026-07-13        # one day, card by card
  pull.py --cards                 # include every card's title/summary (default on for a single --day)
  pull.py --obs                   # also dump the rawer `observations` layer (below the LLM cards)
  pull.py --category Work|Personal|Distraction|Idle|System|all   (default Work)
"""
import argparse
import os
import sqlite3
import sys
from collections import defaultdict
from datetime import date, timedelta

DB = os.path.expanduser("~/Library/Application Support/Dayflow/chunks.sqlite")
MAX_CARD_S = 3 * 3600  # a single "activity" card longer than this is treated as a glitch


def connect():
    if not os.path.exists(DB):
        sys.exit(f"Dayflow DB not found at {DB}")
    # mode=ro is mandatory: the DB is live; never open it writable.
    return sqlite3.connect(f"file:{DB}?mode=ro", uri=True)


def merge_hours(intervals):
    """Union of [start,end) intervals, in hours — the real wall-clock time."""
    if not intervals:
        return 0.0
    intervals = sorted(intervals)
    total = 0
    cs, ce = intervals[0]
    for s, e in intervals[1:]:
        if s <= ce:
            ce = max(ce, e)
        else:
            total += ce - cs
            cs, ce = s, e
    total += ce - cs
    return total / 3600


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="frm")
    ap.add_argument("--to", dest="to")
    ap.add_argument("--day")
    ap.add_argument("--category", default="Work")
    ap.add_argument("--cards", action="store_true")
    ap.add_argument("--obs", action="store_true")
    a = ap.parse_args()

    if a.day:
        a.frm = a.to = a.day
        a.cards = True
    if not a.frm:
        a.frm = str(date.today() - timedelta(days=8))
    if not a.to:
        a.to = str(date.today())

    con = connect()
    cat_clause = "" if a.category == "all" else "AND category = ?"
    params = [a.frm, a.to] + ([] if a.category == "all" else [a.category])
    rows = con.execute(
        f"""SELECT day, start_ts, end_ts, title, summary, category
            FROM timeline_cards
            WHERE is_deleted=0 AND day BETWEEN ? AND ? {cat_clause}
            ORDER BY day, start_ts""",
        params,
    ).fetchall()

    byday = defaultdict(list)
    cards_byday = defaultdict(list)
    flagged = []
    for day, s, e, title, summary, cat in rows:
        if s is None or e is None or e <= s:
            continue
        if (e - s) > MAX_CARD_S:
            flagged.append((day, round((e - s) / 3600, 1), cat, (title or "")[:60]))
            continue
        byday[day].append((s, e))
        cards_byday[day].append((s, e, title, summary, cat))

    print(f"Dayflow — {a.category} — {a.frm} … {a.to}  (overlap-merged, read-only)\n")
    grand = 0.0
    for day in sorted(byday):
        hrs = merge_hours(byday[day])
        grand += hrs
        print(f"── {day}   {hrs:.1f} h   ({len(cards_byday[day])} cards)")
        if a.cards:
            for s, e, title, summary, cat in cards_byday[day]:
                from datetime import datetime
                t0 = datetime.fromtimestamp(s).strftime("%H:%M")
                t1 = datetime.fromtimestamp(e).strftime("%H:%M")
                print(f"   {t0}-{t1}  {title}")
            print()
    print(f"\nTOTAL {a.category} (merged): {grand:.1f} h")

    if flagged:
        print("\n⚠ excluded glitch cards (single card >3h — sleep/wake or corrupt timestamp):")
        for d, h, cat, t in flagged:
            print(f"   {d}  {h}h  [{cat}]  {t}")

    if a.obs:
        print("\n=== raw observations (the layer beneath the LLM cards) ===")
        obs = con.execute(
            """SELECT o.start_ts, o.observation, o.llm_model
               FROM observations o
               JOIN timeline_cards c ON c.batch_id=o.batch_id
               WHERE c.day BETWEEN ? AND ?
               GROUP BY o.id ORDER BY o.start_ts LIMIT 40""",
            [a.frm, a.to],
        ).fetchall()
        from datetime import datetime
        for ts, text, model in obs:
            t = datetime.fromtimestamp(ts).strftime("%m-%d %H:%M")
            print(f"   [{t}] ({model}) {text[:140]}")


if __name__ == "__main__":
    main()
