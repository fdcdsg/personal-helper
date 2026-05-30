"""SQLAlchemy 模型"""
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, ForeignKey, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_input: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(60), nullable=False, default="默认")

    remind_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    next_remind_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    remind_interval_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    remind_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    dingding_enabled: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    app_notify_enabled: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    calendar_enabled: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)

    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="normal")

    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )

    remind_logs: Mapped[list["RemindLog"]] = relationship(
        "RemindLog", back_populates="task", cascade="all, delete-orphan"
    )


class RemindLog(Base):
    __tablename__ = "remind_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"))
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    result: Mapped[str] = mapped_column(String(30), nullable=False, default="success")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    task: Mapped["Task"] = relationship("Task", back_populates="remind_logs")


class UserSettings(Base):
    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_name: Mapped[str] = mapped_column(String(100), default="default")
    dingding_webhook: Mapped[str | None] = mapped_column(Text, nullable=True)
    dingding_secret: Mapped[str | None] = mapped_column(Text, nullable=True)
    notion_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    notion_data_source_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    notion_title_property: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notion_remind_time_property: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notion_content_property: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notion_category_property: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notion_interval_property: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notion_status_property: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notion_created_time_property: Mapped[str | None] = mapped_column(String(100), nullable=True)
    enable_notion_sync: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    notion_sync_interval_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    notion_last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    default_remind_interval_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=10)

    enable_dingding: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    enable_app_notify: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    enable_calendar: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )
