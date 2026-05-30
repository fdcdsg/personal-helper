"""Helpers for importing reminder tasks from Notion."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
import re
from enum import Enum
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app import crud
from app.schemas import (
    NotionImportError,
    NotionImportRequest,
    NotionImportResult,
    TaskCreate,
    TaskOut,
    TaskUpdate,
)


NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_CURRENT_VERSION = "2025-09-03"
NOTION_LEGACY_VERSION = "2022-06-28"


@dataclass
class ParsedNotionTask:
    page_id: str
    title: str
    created_time: datetime
    remind_time: datetime
    content: str | None
    category: str
    interval_minutes: int
    sync_status: "NotionSyncStatus"


class NotionSyncStatus(str, Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    done = "done"


def import_notion_tasks(db: Session, data: NotionImportRequest) -> NotionImportResult:
    pages = _query_notion_pages(data)
    result = NotionImportResult()

    for page in pages:
        page_id = page.get("id")
        try:
            parsed = _parse_page(page, data)
            raw_input = _raw_input_for_task(parsed)
            if data.dry_run:
                result.skipped += 1
                continue

            existing = crud.get_task_by_raw_input(db, raw_input)
            if parsed.sync_status == NotionSyncStatus.not_started:
                if existing and existing.status not in ("done", "cancelled"):
                    crud.mark_cancelled(db, existing)
                    result.updated += 1
                else:
                    result.skipped += 1
                continue

            if existing:
                task = crud.update_task(
                    db,
                    existing,
                    TaskUpdate(
                        title=parsed.title,
                        content=parsed.content,
                        category=parsed.category,
                        remind_time=parsed.remind_time,
                        remind_interval_minutes=parsed.interval_minutes,
                    ),
                )
                if parsed.sync_status == NotionSyncStatus.done and task.status != "done":
                    task = crud.mark_done(db, task)
                elif parsed.sync_status == NotionSyncStatus.in_progress and task.status in (
                    "done",
                    "cancelled",
                ):
                    task = crud.mark_pending(db, task)
                result.updated += 1
            else:
                if parsed.sync_status == NotionSyncStatus.done:
                    result.skipped += 1
                    continue
                task = crud.create_task(
                    db,
                    TaskCreate(
                        title=parsed.title,
                        content=parsed.content,
                        category=parsed.category,
                        remind_time=parsed.remind_time,
                        remind_interval_minutes=parsed.interval_minutes,
                        raw_input=raw_input,
                    ),
                )
                result.created += 1
            result.tasks.append(TaskOut.model_validate(task))
        except ValueError as exc:
            result.failed += 1
            result.errors.append(
                NotionImportError(
                    page_id=page_id,
                    title=_best_effort_title(page),
                    message=str(exc),
                )
            )

    return result


def _query_notion_pages(data: NotionImportRequest) -> list[dict[str, Any]]:
    clean_id = _clean_notion_id(data.data_source_id)
    try:
        return _query_pages(
            token=data.notion_token,
            path=f"/data_sources/{clean_id}/query",
            notion_version=NOTION_CURRENT_VERSION,
            remind_time_property=data.remind_time_property,
        )
    except httpx.HTTPStatusError as first_error:
        try:
            return _query_pages(
                token=data.notion_token,
                path=f"/databases/{clean_id}/query",
                notion_version=NOTION_LEGACY_VERSION,
                remind_time_property=data.remind_time_property,
            )
        except httpx.HTTPStatusError as second_error:
            first_message = _notion_error_message(first_error)
            second_message = _notion_error_message(second_error)
            raise ValueError(
                f"Notion 查询失败：{first_message}；兼容数据库接口也失败：{second_message}"
            ) from second_error
        except httpx.RequestError as exc:
            raise ValueError(f"后端无法连接 Notion API，请检查网络、代理或 VPN：{exc}") from exc
    except httpx.RequestError as exc:
        raise ValueError(f"后端无法连接 Notion API，请检查网络、代理或 VPN：{exc}") from exc


def _query_pages(
    *,
    token: str,
    path: str,
    notion_version: str,
    remind_time_property: str,
) -> list[dict[str, Any]]:
    headers = {
        "Authorization": f"Bearer {token.strip()}",
        "Content-Type": "application/json",
        "Notion-Version": notion_version,
    }
    pages: list[dict[str, Any]] = []
    body: dict[str, Any] = {
        "page_size": 100,
        "filter": {
            "property": remind_time_property,
            "date": {"is_not_empty": True},
        },
    }
    with httpx.Client(base_url=NOTION_API_BASE, timeout=20.0) as client:
        while True:
            response = client.post(path, headers=headers, json=body)
            response.raise_for_status()
            payload = response.json()
            pages.extend(payload.get("results", []))
            if not payload.get("has_more"):
                break
            body["start_cursor"] = payload.get("next_cursor")
    return pages


def _parse_page(page: dict[str, Any], data: NotionImportRequest) -> ParsedNotionTask:
    properties = page.get("properties") or {}
    page_id = str(page.get("id") or "")
    if not page_id:
        raise ValueError("Notion 页面缺少 id")

    if data.completed_property:
        completed_value = properties.get(data.completed_property)
        if _property_is_completed(completed_value):
            sync_status = NotionSyncStatus.done
        else:
            sync_status = _parse_status(properties.get(data.status_property or ""))
    else:
        sync_status = _parse_status(properties.get(data.status_property or ""))

    title = _property_to_text(properties.get(data.title_property)).strip()
    if not title:
        title = _best_effort_title(page).strip()
    if not title:
        raise ValueError(f"找不到标题属性：{data.title_property}")

    created_time = _property_to_datetime(
        properties.get(data.created_time_property or ""),
        data.default_hour_for_date_only,
    )
    if created_time is None:
        created_time = _page_created_time(page)
    if created_time is None:
        raise ValueError(f"找不到创建时间属性：{data.created_time_property}")

    remind_time = _property_to_datetime(
        properties.get(data.remind_time_property),
        data.default_hour_for_date_only,
    )
    if remind_time is None:
        raise ValueError(f"找不到提醒时间属性：{data.remind_time_property}")

    content = None
    if data.content_property:
        content = _property_to_text(properties.get(data.content_property)).strip() or None

    category = data.default_category.strip() or "Notion"
    if data.category_property:
        category = _property_to_text(properties.get(data.category_property)).strip() or category

    interval = data.default_interval_minutes
    if data.interval_property:
        maybe_interval = _property_to_number(properties.get(data.interval_property))
        if maybe_interval is not None:
            interval = max(1, min(24 * 60, int(maybe_interval)))

    return ParsedNotionTask(
        page_id=page_id,
        title=title,
        created_time=created_time,
        remind_time=remind_time,
        content=content,
        category=category,
        interval_minutes=interval,
        sync_status=sync_status,
    )


def _property_to_text(prop: dict[str, Any] | None) -> str:
    if not prop:
        return ""
    prop_type = prop.get("type")
    value = prop.get(prop_type) if prop_type else None
    if prop_type in {"title", "rich_text"} and isinstance(value, list):
        return "".join(item.get("plain_text", "") for item in value)
    if prop_type == "select" and isinstance(value, dict):
        return value.get("name") or ""
    if prop_type == "multi_select" and isinstance(value, list):
        return "、".join(item.get("name", "") for item in value if item.get("name"))
    if prop_type == "status" and isinstance(value, dict):
        return value.get("name") or ""
    if prop_type in {"email", "phone_number", "url"}:
        return str(value or "")
    if prop_type == "number" and value is not None:
        return str(value)
    if prop_type == "formula" and isinstance(value, dict):
        return _formula_to_text(value)
    return ""


def _property_to_datetime(prop: dict[str, Any] | None, default_hour: int) -> datetime | None:
    if not prop:
        return None
    prop_type = prop.get("type")
    if prop_type == "date":
        date_value = prop.get("date") or {}
        start = date_value.get("start")
    elif prop_type == "created_time":
        start = prop.get("created_time")
    else:
        return None
    if not start:
        return None
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", start):
        return datetime.combine(datetime.fromisoformat(start).date(), time(default_hour, 0))
    parsed = datetime.fromisoformat(start.replace("Z", "+00:00"))
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone().replace(tzinfo=None)
    return parsed


def _property_to_number(prop: dict[str, Any] | None) -> float | None:
    if not prop:
        return None
    prop_type = prop.get("type")
    if prop_type == "number":
        return prop.get("number")
    text = _property_to_text(prop)
    if not text:
        return None
    match = re.search(r"\d+", text)
    return float(match.group()) if match else None


def _property_is_completed(prop: dict[str, Any] | None) -> bool:
    if not prop:
        return False
    prop_type = prop.get("type")
    value = prop.get(prop_type) if prop_type else None
    if prop_type == "checkbox":
        return bool(value)
    text = _property_to_text(prop).strip().lower()
    return text in {"done", "complete", "completed", "已完成", "完成"}


def _parse_status(prop: dict[str, Any] | None) -> NotionSyncStatus:
    text = _property_to_text(prop).strip().lower()
    if text in {"完成", "已完成", "done", "complete", "completed"}:
        return NotionSyncStatus.done
    if text in {"未开始", "待办", "todo", "not started", "not_started"}:
        return NotionSyncStatus.not_started
    if text in {"进行中", "in progress", "in_progress", "doing", "active"}:
        return NotionSyncStatus.in_progress
    return NotionSyncStatus.in_progress


def _page_created_time(page: dict[str, Any]) -> datetime | None:
    value = page.get("created_time")
    if not value:
        return None
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone().replace(tzinfo=None)
    return parsed


def _formula_to_text(value: dict[str, Any]) -> str:
    formula_type = value.get("type")
    raw = value.get(formula_type) if formula_type else None
    if raw is None:
        return ""
    return str(raw)


def _best_effort_title(page: dict[str, Any]) -> str:
    properties = page.get("properties") or {}
    for prop in properties.values():
        if isinstance(prop, dict) and prop.get("type") == "title":
            return _property_to_text(prop)
    return ""


def _raw_input_for_task(task: ParsedNotionTask) -> str:
    created_key = task.created_time.isoformat(timespec="seconds")
    title_key = re.sub(r"\s+", " ", task.title.strip())
    return f"notion-task:{created_key}:{title_key}"


def _clean_notion_id(value: str) -> str:
    value = value.strip()
    match = re.search(r"([0-9a-fA-F]{32})", value.replace("-", ""))
    if match:
        raw = match.group(1)
        return f"{raw[0:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:32]}"
    return value


def _notion_error_message(exc: httpx.HTTPStatusError) -> str:
    try:
        payload = exc.response.json()
    except ValueError:
        return exc.response.text
    return str(payload.get("message") or payload)
