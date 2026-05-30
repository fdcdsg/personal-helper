"""Database engine and session setup."""
from __future__ import annotations

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

_connect_args = {}
if settings.database_type.lower() == "sqlite":
    _connect_args["check_same_thread"] = False

engine = create_engine(settings.database_url, connect_args=_connect_args, pool_pre_ping=True)

if settings.database_type.lower() == "sqlite":

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app import models  # noqa: F401
    from app.models import UserSettings

    Base.metadata.create_all(bind=engine)
    _ensure_columns()
    db = SessionLocal()
    try:
        if not db.query(UserSettings).filter(UserSettings.user_name == "default").first():
            db.add(UserSettings(user_name="default", default_remind_interval_minutes=10))
            db.commit()
    finally:
        db.close()


def _ensure_columns() -> None:
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    if "tasks" in table_names:
        task_columns = {column["name"] for column in inspector.get_columns("tasks")}
        if "category" not in task_columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE tasks ADD COLUMN category VARCHAR(60) NOT NULL DEFAULT '默认'"))
    if "user_settings" in table_names:
        settings_columns = {column["name"] for column in inspector.get_columns("user_settings")}
        with engine.begin() as conn:
            if "dingding_secret" not in settings_columns:
                conn.execute(text("ALTER TABLE user_settings ADD COLUMN dingding_secret TEXT"))
            if "notion_token" not in settings_columns:
                conn.execute(text("ALTER TABLE user_settings ADD COLUMN notion_token TEXT"))
            if "notion_data_source_id" not in settings_columns:
                conn.execute(text("ALTER TABLE user_settings ADD COLUMN notion_data_source_id TEXT"))
            if "notion_title_property" not in settings_columns:
                conn.execute(text("ALTER TABLE user_settings ADD COLUMN notion_title_property VARCHAR(100)"))
            if "notion_remind_time_property" not in settings_columns:
                conn.execute(text("ALTER TABLE user_settings ADD COLUMN notion_remind_time_property VARCHAR(100)"))
            if "notion_content_property" not in settings_columns:
                conn.execute(text("ALTER TABLE user_settings ADD COLUMN notion_content_property VARCHAR(100)"))
            if "notion_category_property" not in settings_columns:
                conn.execute(text("ALTER TABLE user_settings ADD COLUMN notion_category_property VARCHAR(100)"))
            if "notion_interval_property" not in settings_columns:
                conn.execute(text("ALTER TABLE user_settings ADD COLUMN notion_interval_property VARCHAR(100)"))
            if "notion_status_property" not in settings_columns:
                conn.execute(text("ALTER TABLE user_settings ADD COLUMN notion_status_property VARCHAR(100)"))
            if "notion_created_time_property" not in settings_columns:
                conn.execute(text("ALTER TABLE user_settings ADD COLUMN notion_created_time_property VARCHAR(100)"))
            if "enable_notion_sync" not in settings_columns:
                conn.execute(text("ALTER TABLE user_settings ADD COLUMN enable_notion_sync SMALLINT NOT NULL DEFAULT 0"))
            if "notion_sync_interval_minutes" not in settings_columns:
                conn.execute(text("ALTER TABLE user_settings ADD COLUMN notion_sync_interval_minutes INTEGER NOT NULL DEFAULT 5"))
            if "notion_last_synced_at" not in settings_columns:
                conn.execute(text("ALTER TABLE user_settings ADD COLUMN notion_last_synced_at DATETIME"))
