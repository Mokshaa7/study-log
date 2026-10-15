from datetime import date, datetime, timedelta, timezone
from typing import List

from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import desc

import models
import schemas
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Study Tracker MVP")


def ist_today() -> date:
    ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist).date()


# ---------- Weekly Plan ----------

@app.post("/weekly-plan", response_model=List[schemas.DayPlanOut])
def create_weekly_plan(plan: schemas.WeeklyPlanCreate, db: Session = Depends(get_db)):
    """
    Upsert a batch of day->topic plans, e.g. at the start of the week.
    If a plan already exists for a date, it's overwritten (lets you edit).
    """
    result = []
    for cleared_date in plan.delete_dates:
        existing = db.query(models.DayPlan).filter(models.DayPlan.date == cleared_date).first()
        if existing:
            db.delete(existing)

    for day in plan.days:
        existing = db.query(models.DayPlan).filter(models.DayPlan.date == day.date).first()
        if existing:
            existing.topic = day.topic
            db.add(existing)
            result.append(existing)
        else:
            new_plan = models.DayPlan(date=day.date, topic=day.topic)
            db.add(new_plan)
            result.append(new_plan)
    db.commit()
    for r in result:
        db.refresh(r)
    return result


@app.get("/weekly-plan", response_model=List[schemas.DayPlanOut])
def get_weekly_plan(start: date, end: date, db: Session = Depends(get_db)):
    """Get planned topics for a date range (inclusive)."""
    plans = (
        db.query(models.DayPlan)
        .filter(models.DayPlan.date >= start, models.DayPlan.date <= end)
        .order_by(models.DayPlan.date)
        .all()
    )
    return plans


# ---------- Logging ----------

@app.post("/log", response_model=schemas.LogOut)
def log_day(entry: schemas.LogCreate, db: Session = Depends(get_db)):
    """
    Log today's (or a given date's) topic as studied.
    Pulls the topic from the day's plan; fails if no plan exists for that date.
    """
    target_date = entry.date or ist_today()

    plan = db.query(models.DayPlan).filter(models.DayPlan.date == target_date).first()
    if not plan:
        raise HTTPException(
            status_code=404,
            detail=f"No planned topic found for {target_date}. Set a weekly plan first.",
        )

    existing_log = db.query(models.LogEntry).filter(models.LogEntry.date == target_date).first()
    if existing_log:
        raise HTTPException(status_code=400, detail=f"{target_date} is already logged.")

    log = models.LogEntry(date=target_date, topic=plan.topic, note=entry.note)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


# ---------- Today status ----------

@app.get("/today", response_model=schemas.TodayStatus)
def today_status(db: Session = Depends(get_db)):
    today = ist_today()
    plan = db.query(models.DayPlan).filter(models.DayPlan.date == today).first()
    log = db.query(models.LogEntry).filter(models.LogEntry.date == today).first()

    return schemas.TodayStatus(
        date=today,
        topic=plan.topic if plan else None,
        logged=log is not None,
        log=log,
    )


# ---------- History ----------

@app.get("/history", response_model=List[schemas.HistoryDay])
def get_history(days: int = 30, db: Session = Depends(get_db)):
    """Last N days, showing planned topic + whether it was logged."""
    end = ist_today()
    start = end - timedelta(days=days - 1)

    plans = {
        p.date: p
        for p in db.query(models.DayPlan)
        .filter(models.DayPlan.date >= start, models.DayPlan.date <= end)
        .all()
    }
    logs = {
        l.date: l
        for l in db.query(models.LogEntry)
        .filter(models.LogEntry.date >= start, models.LogEntry.date <= end)
        .all()
    }

    result = []
    for i in range(days):
        d = start + timedelta(days=i)
        plan = plans.get(d)
        log = logs.get(d)
        result.append(
            schemas.HistoryDay(
                date=d,
                planned_topic=plan.topic if plan else None,
                logged=log is not None,
                note=log.note if log else None,
            )
        )
    return list(reversed(result))  # most recent first


# ---------- Streak ----------

@app.get("/streak", response_model=schemas.StreakOut)
def get_streak(db: Session = Depends(get_db)):
    logs = db.query(models.LogEntry).order_by(desc(models.LogEntry.date)).all()
    logged_dates = set(l.date for l in logs)

    if not logged_dates:
        return schemas.StreakOut(current_streak=0, longest_streak=0, total_logged=0)

    # Current streak: walk backward from today (or yesterday, so a not-yet-logged
    # today doesn't zero out an otherwise intact streak)
    current_streak = 0
    cursor = ist_today()
    if cursor not in logged_dates:
        cursor -= timedelta(days=1)
    while cursor in logged_dates:
        current_streak += 1
        cursor -= timedelta(days=1)

    # Longest streak: scan all logged dates sorted ascending
    sorted_dates = sorted(logged_dates)
    longest_streak = 1
    running = 1
    for i in range(1, len(sorted_dates)):
        if sorted_dates[i] - sorted_dates[i - 1] == timedelta(days=1):
            running += 1
        else:
            running = 1
        longest_streak = max(longest_streak, running)

    return schemas.StreakOut(
        current_streak=current_streak,
        longest_streak=longest_streak,
        total_logged=len(logged_dates),
    )


# ---------- Frontend ----------
# Mounted last and at "/" so it acts as a catch-all for the UI page,
# without shadowing any of the API routes defined above.
app.mount("/", StaticFiles(directory="static", html=True), name="frontend")