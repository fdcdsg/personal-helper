"""FastAPI entrypoint."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routers import settings, tasks
from app.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="智能任务提醒系统",
    description="TaskReminder API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router)
app.include_router(settings.router)

_web_dir = Path(__file__).resolve().parents[2] / "web"
if _web_dir.is_dir():
    app.mount("/web", StaticFiles(directory=str(_web_dir), html=True), name="web")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "message": exc.detail, "data": None},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": str(exc), "data": None},
    )


@app.get("/")
def root():
    if _web_dir.is_dir():
        return RedirectResponse(url="/web/")
    return {"code": 200, "message": "TaskReminder API 正在运行", "data": None}


@app.get("/health")
def health():
    return {"code": 200, "message": "ok", "data": None}
