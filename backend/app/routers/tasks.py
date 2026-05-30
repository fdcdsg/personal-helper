"""Task APIs."""
from __future__ import annotations

from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.notion import import_notion_tasks
from app.schemas import (
    ApiResponse,
    NotionImportRequest,
    NotionImportResult,
    RemindLogOut,
    TaskCreate,
    TaskDetailOut,
    TaskOut,
    TaskParseCreate,
    TaskPostpone,
    TaskUpdate,
)

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("", response_model=ApiResponse[TaskOut])
def create_task(data: TaskCreate, db: Session = Depends(get_db)):
    task = crud.create_task(db, data)
    return ApiResponse(code=200, message="任务创建成功", data=TaskOut.model_validate(task))


@router.post("/parse-create", response_model=ApiResponse[TaskOut])
def parse_create_task(data: TaskParseCreate, db: Session = Depends(get_db)):
    try:
        task = crud.create_task_from_text(db, data.text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ApiResponse(code=200, message="任务创建成功", data=TaskOut.model_validate(task))


@router.post("/notion/import", response_model=ApiResponse[NotionImportResult])
def import_tasks_from_notion(data: NotionImportRequest, db: Session = Depends(get_db)):
    try:
        result = import_notion_tasks(db, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ApiResponse(code=200, message="Notion 同步完成", data=result)


@router.get("", response_model=ApiResponse[list[TaskOut]])
def list_tasks(
    status: str | None = Query(None),
    date: str | None = Query(None, description="Date in YYYY-MM-DD format"),
    db: Session = Depends(get_db),
):
    date_filter = None
    if date:
        try:
            date_filter = date_type.fromisoformat(date)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="日期格式应为 YYYY-MM-DD") from exc

    tasks = crud.list_tasks(db, status=status, date_filter=date_filter)
    return ApiResponse(code=200, message="success", data=[TaskOut.model_validate(t) for t in tasks])


@router.get("/{task_id}", response_model=ApiResponse[TaskDetailOut])
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    detail = TaskDetailOut.model_validate(task)
    detail.remind_logs = [RemindLogOut.model_validate(log) for log in task.remind_logs]
    return ApiResponse(code=200, message="success", data=detail)


@router.put("/{task_id}", response_model=ApiResponse[TaskOut])
def update_task(task_id: int, data: TaskUpdate, db: Session = Depends(get_db)):
    task = crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    task = crud.update_task(db, task, data)
    return ApiResponse(code=200, message="任务已更新", data=TaskOut.model_validate(task))


@router.post("/{task_id}/done", response_model=ApiResponse[TaskOut])
def done_task(task_id: int, db: Session = Depends(get_db)):
    task = crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    task = crud.mark_done(db, task)
    return ApiResponse(code=200, message="任务已完成", data=TaskOut.model_validate(task))


@router.post("/{task_id}/postpone", response_model=ApiResponse[TaskOut])
def postpone_task(task_id: int, data: TaskPostpone, db: Session = Depends(get_db)):
    task = crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    task = crud.postpone_task(db, task, data.minutes)
    return ApiResponse(code=200, message="任务已延后", data=TaskOut.model_validate(task))


@router.post("/{task_id}/cancel", response_model=ApiResponse[TaskOut])
def cancel_task(task_id: int, db: Session = Depends(get_db)):
    task = crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    task = crud.mark_cancelled(db, task)
    return ApiResponse(code=200, message="任务已取消", data=TaskOut.model_validate(task))
