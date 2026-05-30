"""Database CRUD helpers."""
from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.models import RemindLog, Task, UserSettings
from app.schemas import SettingsUpdate, TaskCreate, TaskUpdate
from app.time_parser import extract_title, parse_remind_time


def get_settings(db: Session) -> UserSettings:
    settings = db.query(UserSettings).filter(UserSettings.user_name == "default").first()
    if not settings:
        settings = UserSettings(user_name="default", default_remind_interval_minutes=10)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def update_settings(db: Session, data: SettingsUpdate) -> UserSettings:
    settings = get_settings(db)
    if data.dingding_webhook is not None:
        settings.dingding_webhook = data.dingding_webhook.strip()
    if data.dingding_secret is not None:
        settings.dingding_secret = data.dingding_secret.strip()
    if data.notion_token is not None:
        settings.notion_token = data.notion_token.strip()
    if data.notion_data_source_id is not None:
        settings.notion_data_source_id = data.notion_data_source_id.strip()
    if data.notion_title_property is not None:
        settings.notion_title_property = data.notion_title_property.strip() or "Name"
    if data.notion_remind_time_property is not None:
        settings.notion_remind_time_property = data.notion_remind_time_property.strip() or "提醒时间"
    if data.notion_content_property is not None:
        settings.notion_content_property = data.notion_content_property.strip() or "内容"
    if data.notion_category_property is not None:
        settings.notion_category_property = data.notion_category_property.strip() or "分类"
    if data.notion_interval_property is not None:
        settings.notion_interval_property = data.notion_interval_property.strip() or "提醒间隔"
    if data.notion_status_property is not None:
        settings.notion_status_property = data.notion_status_property.strip() or "状态"
    if data.notion_created_time_property is not None:
        settings.notion_created_time_property = data.notion_created_time_property.strip() or "创建时间"
    if data.enable_notion_sync is not None:
        settings.enable_notion_sync = 1 if data.enable_notion_sync else 0
    if data.notion_sync_interval_minutes is not None:
        settings.notion_sync_interval_minutes = data.notion_sync_interval_minutes
    if data.default_remind_interval_minutes is not None:
        settings.default_remind_interval_minutes = data.default_remind_interval_minutes
    if data.enable_dingding is not None:
        settings.enable_dingding = 1 if data.enable_dingding else 0
    if data.enable_app_notify is not None:
        settings.enable_app_notify = 1 if data.enable_app_notify else 0
    if data.enable_calendar is not None:
        settings.enable_calendar = 1 if data.enable_calendar else 0
    db.commit()
    db.refresh(settings)
    return settings


def create_task(db: Session, data: TaskCreate) -> Task:
    task = Task(
        title=data.title.strip(),
        content=data.content,
        raw_input=data.raw_input,
        category=(data.category or "默认").strip() or "默认",
        remind_time=data.remind_time,
        next_remind_time=data.remind_time,
        status="pending",
        remind_interval_minutes=data.remind_interval_minutes,
        dingding_enabled=1 if data.dingding_enabled else 0,
        app_notify_enabled=1 if data.app_notify_enabled else 0,
        calendar_enabled=1 if data.calendar_enabled else 0,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def create_task_from_text(db: Session, text: str) -> Task:
    settings = get_settings(db)
    remind_time = parse_remind_time(text)
    if remind_time is None:
        raise ValueError("无法解析提醒时间，请输入类似：10分钟后提醒我打电话、明天下午三点提醒我联系客户")

    return create_task(
        db,
        TaskCreate(
            title=extract_title(text),
            content=text,
            raw_input=text,
            remind_time=remind_time,
            remind_interval_minutes=settings.default_remind_interval_minutes,
        ),
    )


def get_task(db: Session, task_id: int) -> Task | None:
    return db.query(Task).filter(Task.id == task_id).first()


def get_task_by_raw_input(db: Session, raw_input: str) -> Task | None:
    return db.query(Task).filter(Task.raw_input == raw_input).first()


def update_task(db: Session, task: Task, data: TaskUpdate) -> Task:
    if data.title is not None:
        task.title = data.title.strip()
    if data.content is not None:
        task.content = data.content
    if data.category is not None:
        task.category = data.category.strip() or "默认"
    if data.remind_time is not None:
        task.remind_time = data.remind_time
        if task.status not in ("done", "cancelled"):
            task.next_remind_time = data.remind_time
            task.status = "pending"
    if data.remind_interval_minutes is not None:
        task.remind_interval_minutes = data.remind_interval_minutes
    if data.dingding_enabled is not None:
        task.dingding_enabled = 1 if data.dingding_enabled else 0
    if data.app_notify_enabled is not None:
        task.app_notify_enabled = 1 if data.app_notify_enabled else 0
    if data.calendar_enabled is not None:
        task.calendar_enabled = 1 if data.calendar_enabled else 0
    db.commit()
    db.refresh(task)
    return task


def list_tasks(
    db: Session,
    status: str | None = None,
    date_filter: date | None = None,
) -> list[Task]:
    query = db.query(Task).order_by(Task.next_remind_time.asc(), Task.id.desc())
    if status:
        query = query.filter(Task.status == status)
    if date_filter:
        start = datetime.combine(date_filter, datetime.min.time())
        end = start + timedelta(days=1)
        query = query.filter(Task.remind_time >= start, Task.remind_time < end)
    return query.all()


def mark_done(db: Session, task: Task) -> Task:
    now = datetime.now()
    task.status = "done"
    task.completed_at = now
    db.commit()
    db.refresh(task)
    return task


def mark_cancelled(db: Session, task: Task) -> Task:
    now = datetime.now()
    task.status = "cancelled"
    task.cancelled_at = now
    db.commit()
    db.refresh(task)
    return task


def mark_pending(db: Session, task: Task) -> Task:
    task.status = "pending"
    task.completed_at = None
    task.cancelled_at = None
    task.next_remind_time = task.remind_time
    db.commit()
    db.refresh(task)
    return task


def postpone_task(db: Session, task: Task, minutes: int) -> Task:
    now = datetime.now()
    task.next_remind_time = now + timedelta(minutes=minutes)
    task.status = "postponed"
    db.commit()
    db.refresh(task)
    return task


def add_remind_log(
    db: Session,
    task_id: int,
    channel: str,
    message: str,
    result: str = "success",
    error_message: str | None = None,
) -> RemindLog:
    log = RemindLog(
        task_id=task_id,
        channel=channel,
        message=message,
        result=result,
        error_message=error_message,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_due_tasks(db: Session, now: datetime | None = None) -> list[Task]:
    now = now or datetime.now()
    return (
        db.query(Task)
        .filter(
            Task.status.notin_(["done", "cancelled"]),
            Task.next_remind_time <= now,
        )
        .order_by(Task.next_remind_time.asc())
        .all()
    )


def apply_reminder_sent(db: Session, task: Task, now: datetime | None = None) -> Task:
    now = now or datetime.now()
    task.remind_count += 1
    task.status = "reminding"
    task.next_remind_time = now + timedelta(minutes=task.remind_interval_minutes)
    db.commit()
    db.refresh(task)
    return task
