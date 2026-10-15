from __future__ import annotations
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class DayPlanCreate(BaseModel):
    date: date
    topic: str


class WeeklyPlanCreate(BaseModel):
    days: List[DayPlanCreate]
    delete_dates: List[date] = Field(default_factory=list)


class DayPlanOut(BaseModel):
    date: date
    topic: str

    class Config:
        from_attributes = True


class LogCreate(BaseModel):
    date: Optional[date] = None  # defaults to today if not provided
    note: Optional[str] = None


class LogOut(BaseModel):
    date: date
    topic: str
    note: Optional[str]
    logged_at: datetime

    class Config:
        from_attributes = True


class TodayStatus(BaseModel):
    date: date
    topic: Optional[str]
    logged: bool
    log: Optional[LogOut] = None


class HistoryDay(BaseModel):
    date: date
    planned_topic: Optional[str]
    logged: bool
    note: Optional[str] = None


class StreakOut(BaseModel):
    current_streak: int
    longest_streak: int
    total_logged: int