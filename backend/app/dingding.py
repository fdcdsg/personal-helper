"""DingTalk group robot webhook notifications."""
from __future__ import annotations

import httpx
import base64
import hashlib
import hmac
import time
from urllib.parse import quote_plus


def build_remind_message(
    title: str,
    remind_time_str: str,
    remind_count: int,
    status: str = "未完成",
) -> str:
    return (
        "任务提醒\n\n"
        f"事项：{title}\n"
        f"原定时间：{remind_time_str}\n"
        f"状态：{status}\n"
        f"提醒次数：第 {remind_count} 次\n\n"
        "请在 App 中选择：完成 / 延后10分钟 / 延后30分钟 / 延后1小时 / 取消。"
    )


def _signed_webhook(webhook: str, secret: str | None = None) -> str:
    if not secret or not secret.strip():
        return webhook.strip()
    timestamp = str(round(time.time() * 1000))
    string_to_sign = f"{timestamp}\n{secret.strip()}".encode("utf-8")
    secret_bytes = secret.strip().encode("utf-8")
    sign = quote_plus(base64.b64encode(hmac.new(secret_bytes, string_to_sign, hashlib.sha256).digest()))
    separator = "&" if "?" in webhook else "?"
    return f"{webhook.strip()}{separator}timestamp={timestamp}&sign={sign}"


async def send_dingding_text(webhook: str, content: str, secret: str | None = None) -> tuple[bool, str | None]:
    """Send a DingTalk text message and return (success, error_message)."""
    if not webhook or not webhook.strip():
        return False, "未配置钉钉 Webhook"

    payload = {"msgtype": "text", "text": {"content": content}}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(_signed_webhook(webhook, secret), json=payload)
            try:
                data = response.json()
            except ValueError:
                data = {}
            if response.status_code == 200 and data.get("errcode") == 0:
                return True, None
            return False, data.get("errmsg") or response.text
    except Exception as exc:
        return False, str(exc)
