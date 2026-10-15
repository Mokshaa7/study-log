# Study Tracker — MVP (Phase 1)

A backend-only MVP: set a week's topics, log each day, see your streak.
No blocking, no quiz yet — this phase is just to prove the daily logging
habit works before building the Android app around it.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python -m uvicorn main:app --reload
```

Then open **http://localhost:8000/** — this is the actual app: Today / Plan week / History.

The raw API still exists underneath and its interactive docs are at
http://localhost:8000/docs if you ever want to call endpoints directly
or debug something.

## Data model

- **DayPlan**: one row per calendar date, holds the topic you planned to
  study that day. Created/updated via `/weekly-plan`.
- **LogEntry**: one row per calendar date, created when you actually log
  that day. Snapshots the topic at time of logging + an optional note.

## Endpoints

| Method | Path            | Purpose                                              |
|--------|-----------------|-------------------------------------------------------|
| POST   | `/weekly-plan`  | Set/overwrite topics for a batch of dates             |
| GET    | `/weekly-plan`  | View planned topics for a date range (`?start=&end=`) |
| POST   | `/log`          | Log a day as studied (defaults to today), optional note |
| GET    | `/today`        | Today's planned topic + whether it's logged           |
| GET    | `/history`      | Last N days: plan vs. logged status (`?days=30`)      |
| GET    | `/streak`       | Current streak, longest streak, total days logged     |

## Example: set up your week (Sunday night)

```bash
curl -X POST http://localhost:8000/weekly-plan \
  -H "Content-Type: application/json" \
  -d '{
    "days": [
      {"date": "2026-07-20", "topic": "Linked Lists"},
      {"date": "2026-07-21", "topic": "Binary Trees"},
      {"date": "2026-07-22", "topic": "Dynamic Programming Basics"},
      {"date": "2026-07-23", "topic": "Graph Traversal (BFS/DFS)"},
      {"date": "2026-07-24", "topic": "Sorting Algorithms"},
      {"date": "2026-07-25", "topic": "Hashing & Hash Maps"},
      {"date": "2026-07-26", "topic": "Review + weak-topic revision"}
    ]
  }'
```

## Example: log today

```bash
curl -X POST http://localhost:8000/log \
  -H "Content-Type: application/json" \
  -d '{"note": "Covered separate chaining vs open addressing"}'
```

`note` is optional — you can also just send `{}`.

## Design notes / known v1 limitations (intentional, for now)

- **No auth** — single-user, local use only. Fine for personal MVP;
  revisit before this touches the internet or has multiple users.
- **No blocking or quiz yet** — this phase only tests whether you
  actually keep up the daily logging habit. Phase 2 wires in the
  Android blocking + quiz-gated unlock once this loop feels right.
- **One log per date, no edits** — you can't re-log or edit a day
  once logged. Deliberate for now (mirrors "you can't undo having
  studied or not") but flag if this gets annoying in practice.
- **`/log` requires a plan to exist for that date first** — by design,
  so you can't log something you never actually planned to study.
- **SQLite** — trivially fine for one user; swap to Postgres only if
  this ever needs concurrent/multi-device access.

## Next steps (not built yet)

1. Use this for a week or two as-is (via `/docs` or curl) — does the
   logging habit actually stick?
2. Phase 2: minimal Android app (Kotlin + Compose) hitting these same
   endpoints — log from your phone instead of curl.
3. Phase 3: Accessibility Service + UsageStatsManager blocking layer.
4. Phase 4: LLM-generated quiz gate before `/log` counts as complete.