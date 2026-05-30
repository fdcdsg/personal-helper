"""Pydantic request and response schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field, field_validator

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: T | None = None


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str | None = None
    category: str | None = Field("默认", max_length=60)
    remind_time: datetime
    remind_interval_minutes: int = Field(10, gt=0, le=24 * 60)
    dingding_enabled: bool = True
    app_notify_enabled: bool = True
    calendar_enabled: bool = False
    raw_input: str | None = None

    @field_validator("remind_time", mode="before")
    @classmethod
    def parse_remind_time(cls, value):
        if isinstance(value, str):
            return value.replace(" ", "T", 1)
        return value


class TaskParseCreate(BaseModel):
    text: str = Field(..., min_length=1)


class TaskPostpone(BaseModel):
    minutes: int = Field(..., gt=0, le=30 * 24 * 60, description="Postpone minutes")


class TaskUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    content: str | None = None
    category: str | None = Field(None, max_length=60)
    remind_time: datetime | None = None
    remind_interval_minutes: int | None = Field(None, gt=0, le=24 * 60)
    dingding_enabled: bool | None = None
    app_notify_enabled: bool | None = None
    calendar_enabled: bool | None = None

    @field_validator("remind_time", mode="before")
    @classmethod
    def parse_remind_time(cls, value):
        if isinstance(value, str):
            return value.replace(" ", "T", 1)
        return value


class TaskOut(BaseModel):
    id: int
    title: str
    content: str | None = None
    raw_input: str | None = None
    category: str
    remind_time: datetime
    next_remind_time: datetime
    status: str
    remind_interval_minutes: int
    remind_count: int
    dingding_enabled: int
    app_notify_enabled: int
    calendar_enabled: int
    priority: str
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class RemindLogOut(BaseModel):
    id: int
    task_id: int
    channel: str
    message: str
    result: str
    error_message: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class TaskDetailOut(TaskOut):
    remind_logs: list[RemindLogOut] = Field(default_factory=list)


class NotionImportRequest(BaseModel):
    notion_token: str = Field(..., min_length=1)
    data_source_id: str = Field(..., min_length=1)
    title_property: str = Field("Name", min_length=1)
    remind_time_property: str = Field("提醒时间", min_length=1)
    content_property: str | None = "内容"
    category_property: str | None = "分类"
    interval_property: str | None = "提醒间隔"
    status_property: str | None = "状态"
    created_time_property: str | None = "创建时间"
    completed_property: str | None = None
    default_category: str = Field("Notion", max_length=60)
    default_interval_minutes: int = Field(10, gt=0, le=24 * 60)
    default_hour_for_date_only: int = Field(9, ge=0, le=23)
    dry_run: bool = False


class NotionImportError(BaseModel):
    page_id: str | None = None
    title: str | None = None
    message: str


class NotionImportResult(BaseModel):
    created: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0
    tasks: list[TaskOut] = Field(default_factory=list)
    errors: list[NotionImportError] = Field(default_factory=list)


class SettingsUpdate(BaseModel):
    dingding_webhook: str | None = None
    dingding_secret: str | None = None
    notion_token: str | None = None
    notion_data_source_id: str | None = None
    notion_title_property: str | None = Field(None, max_length=100)
    notion_remind_time_property: str | None = Field(None, max_length=100)
    notion_content_property: str | None = Field(None, max_length=100)
    notion_category_property: str | None = Field(None, max_length=100)
    notion_interval_property: str | None = Field(None, max_length=100)
    notion_status_property: str | None = Field(None, max_length=100)
    notion_created_time_property: str | None = Field(None, max_length=100)
    enable_notion_sync: bool | None = None
    notion_sync_interval_minutes: int | None = Field(None, gt=0, le=24 * 60)
    default_remind_interval_minutes: int | None = Field(None, gt=0, le=24 * 60)
    enable_dingding: bool | None = None
    enable_app_notify: bool | None = None
    enable_calendar: bool | None = None


class DingdingTestRequest(BaseModel):
    dingding_webhook: str | None = None
    dingding_secret: str | None = None


class SettingsOut(BaseModel):
    id: int
    user_name: str
    dingding_webhook: str | None = None
    dingding_secret: str | None = None
    notion_token: str | None = None
    notion_data_source_id: str | None = None
    notion_title_property: str | None = None
    notion_remind_time_property: str | None = None
    notion_content_property: str | None = None
    notion_category_property: str | None = None
    notion_interval_property: str | None = None
    notion_status_property: str | None = None
    notion_created_time_property: str | None = None
    enable_notion_sync: int
    notion_sync_interval_minutes: int
    notion_last_synced_at: datetime | None = None
    default_remind_interval_minutes: int
    enable_dingding: int
    enable_app_notify: int
    enable_calendar: int

    model_config = {"from_attributes": True}
