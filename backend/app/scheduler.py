"""APScheduler reminder scanner."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app import crud
from app.config import settings
from app.database import SessionLocal
from app.dingding import build_remind_message, send_dingding_text
from app.notion import import_notion_tasks
from app.schemas import NotionImportRequest

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()


def _get_webhook(db: Session) -> tuple[str, str | None]:
    user_settings = crud.get_settings(db)
    if user_settings.dingding_webhook:
        return user_settings.dingding_webhook.strip(), user_settings.dingding_secret
    return (settings.dingding_webhook or "").strip(), None


async def _send_reminder_for_task(db: Session, task) -> None:
    now = datetime.now()
    remind_time_str = task.remind_time.strftime("%Y-%m-%d %H:%M")
    next_count = task.remind_count + 1
    message = build_remind_message(
        title=task.title,
        remind_time_str=remind_time_str,
        remind_count=next_count,
    )

    user_settings = crud.get_settings(db)

    if task.dingding_enabled and user_settings.enable_dingding:
        webhook, secret = _get_webhook(db)
        ok, err = await send_dingding_text(webhook, message, secret)
        crud.add_remind_log(
            db,
            task_id=task.id,
            channel="dingding",
            message=message,
            result="success" if ok else "failed",
            error_message=err,
        )

    if task.app_notify_enabled and user_settings.enable_app_notify:
        crud.add_remind_log(
            db,
            task_id=task.id,
            channel="app",
            message=message,
            result="success",
        )

    if task.calendar_enabled and user_settings.enable_calendar:
        crud.add_remind_log(
            db,
            task_id=task.id,
            channel="calendar",
            message=message,
            result="failed",
            error_message="日历写入功能将在后续版本实现",
        )

    crud.apply_reminder_sent(db, task, now)


def scan_and_remind() -> None:
    """Send reminders for every due task that is not done or cancelled."""
    db = SessionLocal()
    try:
        now = datetime.now()
        for task in crud.get_due_tasks(db, now):
            if task.status in ("done", "cancelled") or task.next_remind_time > now:
                continue
            try:
                asyncio.run(_send_reminder_for_task(db, task))
            except Exception as exc:
                logger.exception("提醒任务 %s 失败: %s", task.id, exc)
    finally:
        db.close()


def sync_notion_if_due() -> None:
    db = SessionLocal()
    try:
        user_settings = crud.get_settings(db)
        if not user_settings.enable_notion_sync:
            return
        if not user_settings.notion_token or not user_settings.notion_data_source_id:
            return

        now = datetime.now()
        last_synced_at = user_settings.notion_last_synced_at
        interval_seconds = max(1, user_settings.notion_sync_interval_minutes) * 60
        if last_synced_at and (now - last_synced_at).total_seconds() < interval_seconds:
            return

        result = import_notion_tasks(
            db,
            NotionImportRequest(
                notion_token=user_settings.notion_token,
                data_source_id=user_settings.notion_data_source_id,
                title_property=user_settings.notion_title_property or "Name",
                remind_time_property=user_settings.notion_remind_time_property or "提醒时间",
                content_property=user_settings.notion_content_property or "内容",
                category_property=user_settings.notion_category_property or "分类",
                interval_property=user_settings.notion_interval_property or "提醒间隔",
                status_property=user_settings.notion_status_property or "状态",
                created_time_property=user_settings.notion_created_time_property or "创建时间",
                default_interval_minutes=user_settings.default_remind_interval_minutes,
            ),
        )
        user_settings.notion_last_synced_at = now
        db.commit()
        logger.info(
            "Notion 自动同步完成：新增 %s，更新 %s，跳过 %s，失败 %s",
            result.created,
            result.updated,
            result.skipped,
            result.failed,
        )
    except Exception as exc:
        logger.exception("Notion 自动同步失败: %s", exc)
    finally:
        db.close()


def start_scheduler() -> None:
    if scheduler.running:
        return
    scheduler.add_job(
        scan_and_remind,
        "interval",
        seconds=settings.scheduler_interval_seconds,
        id="task_reminder_scan",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.add_job(
        sync_notion_if_due,
        "interval",
        seconds=60,
        id="notion_auto_sync",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.start()
    logger.info("任务提醒调度器已启动，扫描间隔 %s 秒", settings.scheduler_interval_seconds)


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
