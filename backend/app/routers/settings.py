"""Settings APIs."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.dingding import send_dingding_text
from app.schemas import ApiResponse, DingdingTestRequest, SettingsOut, SettingsUpdate

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=ApiResponse[SettingsOut])
def get_settings(db: Session = Depends(get_db)):
    settings = crud.get_settings(db)
    return ApiResponse(code=200, message="success", data=SettingsOut.model_validate(settings))


@router.post("", response_model=ApiResponse[SettingsOut])
def update_settings(data: SettingsUpdate, db: Session = Depends(get_db)):
    settings = crud.update_settings(db, data)
    return ApiResponse(code=200, message="设置已保存", data=SettingsOut.model_validate(settings))


@router.post("/test-dingding", response_model=ApiResponse[dict[str, bool]])
async def test_dingding(data: DingdingTestRequest, db: Session = Depends(get_db)):
    settings = crud.get_settings(db)
    webhook = (data.dingding_webhook or settings.dingding_webhook or "").strip()
    secret = (data.dingding_secret or settings.dingding_secret or "").strip()
    ok, err = await send_dingding_text(
        webhook,
        "任务提醒\n\n这是一条来自 Personal Helper 的钉钉测试消息。如果你收到了，说明机器人配置可用。",
        secret,
    )
    if ok:
        return ApiResponse(code=200, message="钉钉测试消息发送成功", data={"ok": True})
    return ApiResponse(code=400, message=err or "钉钉测试消息发送失败", data={"ok": False})
