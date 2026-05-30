"""Lightweight MVP checks for local development."""
from __future__ import annotations

from datetime import datetime, timedelta

from app import crud
from app.database import Base, SessionLocal, engine, init_db
from app.models import Task
from app.scheduler import scan_and_remind
from app.time_parser import extract_title, parse_remind_time


def assert_time_parser() -> None:
    now = datetime(2026, 5, 27, 10, 0)
    cases = [
        ("10分钟后提醒我打电话", datetime(2026, 5, 27, 10, 10), "打电话"),
        ("明天下午三点提醒我联系客户", datetime(2026, 5, 28, 15, 0), "联系客户"),
        ("每天晚上9点提醒我学英语", datetime(2026, 5, 27, 21, 0), "学英语"),
    ]
    for text, expected_time, expected_title in cases:
        assert parse_remind_time(text, now) == expected_time
        assert extract_title(text) == expected_title


def assert_reminder_loop() -> None:
    Base.metadata.create_all(bind=engine)
    init_db()
    db = SessionLocal()
    try:
        task = Task(
            title="测试提醒",
            remind_time=datetime.now() - timedelta(minutes=1),
            next_remind_time=datetime.now() - timedelta(seconds=1),
            status="pending",
            remind_interval_minutes=10,
            dingding_enabled=0,
            app_notify_enabled=1,
            calendar_enabled=0,
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        task_id = task.id
    finally:
        db.close()

    scan_and_remind()

    db = SessionLocal()
    try:
        task = crud.get_task(db, task_id)
        assert task is not None
        assert task.status == "reminding"
        assert task.remind_count == 1
        assert task.next_remind_time > datetime.now()
        assert len(task.remind_logs) == 1

        crud.mark_done(db, task)
        task.next_remind_time = datetime.now() - timedelta(seconds=1)
        db.commit()
    finally:
        db.close()

    scan_and_remind()

    db = SessionLocal()
    try:
        task = crud.get_task(db, task_id)
        assert task is not None
        assert task.status == "done"
        assert task.remind_count == 1
        assert len(task.remind_logs) == 1
    finally:
        db.close()


if __name__ == "__main__":
    assert_time_parser()
    assert_reminder_loop()
    print("MVP checks passed")
