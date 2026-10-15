from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean
from sqlalchemy.sql import func
from database import Base


class DayPlan(Base):
    """A single day's planned topic, set at the start of the week."""
    __tablename__ = "day_plans"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, index=True, nullable=False)  # one plan per calendar day
    topic = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class LogEntry(Base):
    """A completed log for a given day. One-to-one with DayPlan.date."""
    __tablename__ = "log_entries"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, index=True, nullable=False)
    topic = Column(String, nullable=False)  # snapshot of what was studied, in case plan changes later
    note = Column(String, nullable=True)    # optional reflection/summary
    logged_at = Column(DateTime(timezone=True), server_default=func.now())