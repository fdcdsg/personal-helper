"""Rule-based Chinese natural-language reminder time parser."""
from __future__ import annotations

import re
from datetime import datetime, timedelta


_CN_DIGITS = {
    "零": 0,
    "〇": 0,
    "一": 1,
    "二": 2,
    "两": 2,
    "俩": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}

_RELATIVE_MINUTES = re.compile(r"(\d+|[零〇一二两俩三四五六七八九十百]+)\s*(?:分钟|分)\s*(?:后|以后|之后|内)?")
_RELATIVE_HOURS = re.compile(r"(\d+|[零〇一二两俩三四五六七八九十百]+)\s*(?:小时|个小时)\s*(?:后|以后|之后|内)?")
_RELATIVE_DAYS = re.compile(r"(\d+|[零〇一二两俩三四五六七八九十百]+)\s*天\s*(?:后|以后|之后|内)?")

_TODAY = re.compile(r"今天|今日")
_TOMORROW = re.compile(r"明天|明日")
_DAY_AFTER_TOMORROW = re.compile(r"后天")
_DAILY = re.compile(r"每天|每日|天天")

_MORNING = re.compile(r"上午|早上|早晨|清晨")
_NOON = re.compile(r"中午|午间")
_AFTERNOON = re.compile(r"下午|午后")
_EVENING = re.compile(r"晚上|傍晚|夜里|夜间")
_MIDNIGHT = re.compile(r"凌晨|半夜")

_HALF_HOUR = re.compile(r"(\d{1,2})\s*点\s*半")
_HOUR_MINUTE = re.compile(r"(\d{1,2})\s*点(?:钟)?(?:\s*(\d{1,2})\s*分?)?")
_COLON_TIME = re.compile(r"(\d{1,2})[:：](\d{1,2})")

_REMIND_WORDS = re.compile(r"提醒我|记得提醒我|提醒|通知我|叫我|别忘了|不要忘了|帮我")


def _cn_to_int(value: str) -> int | None:
    value = value.strip()
    if not value:
        return None
    if value.isdigit():
        return int(value)
    if value in _CN_DIGITS:
        return _CN_DIGITS[value]
    if value == "十":
        return 10
    if value.startswith("十"):
        tail = value[1:]
        return 10 + _CN_DIGITS.get(tail, 0)
    if value.endswith("十"):
        head = value[:-1]
        if head in _CN_DIGITS:
            return _CN_DIGITS[head] * 10
    if "十" in value:
        head, tail = value.split("十", 1)
        if head in _CN_DIGITS:
            return _CN_DIGITS[head] * 10 + _CN_DIGITS.get(tail, 0)
    return None


def _replace_cn_numbers(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        number = _cn_to_int(match.group(1))
        suffix = match.group(2)
        return f"{number}{suffix}" if number is not None else match.group(0)

    return re.sub(r"([零〇一二两俩三四五六七八九十百]+)(点|分钟|分|小时|个小时|天)", repl, text)


def _apply_period(hour: int, text: str) -> int:
    if (_AFTERNOON.search(text) or _EVENING.search(text)) and 1 <= hour <= 11:
        return hour + 12
    if _NOON.search(text) and hour < 11:
        return 12
    if (_MORNING.search(text) or _MIDNIGHT.search(text)) and hour == 12:
        return 0
    return hour


def parse_remind_time(text: str, now: datetime | None = None) -> datetime | None:
    """Extract the next reminder datetime from common Chinese reminder phrases."""
    now = now or datetime.now()
    normalized = _replace_cn_numbers(text.strip())

    match = _RELATIVE_MINUTES.search(normalized)
    if match:
        minutes = _cn_to_int(match.group(1))
        return now + timedelta(minutes=minutes) if minutes is not None else None

    match = _RELATIVE_HOURS.search(normalized)
    if match:
        hours = _cn_to_int(match.group(1))
        return now + timedelta(hours=hours) if hours is not None else None

    match = _RELATIVE_DAYS.search(normalized)
    if match:
        days = _cn_to_int(match.group(1))
        return now + timedelta(days=days) if days is not None else None

    base_date = now.date()
    explicit_future_day = False
    if _DAY_AFTER_TOMORROW.search(normalized):
        base_date = (now + timedelta(days=2)).date()
        explicit_future_day = True
    elif _TOMORROW.search(normalized):
        base_date = (now + timedelta(days=1)).date()
        explicit_future_day = True
    elif _TODAY.search(normalized):
        base_date = now.date()

    hour: int | None = None
    minute = 0

    match = _COLON_TIME.search(normalized)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
    else:
        match = _HALF_HOUR.search(normalized)
        if match:
            hour = int(match.group(1))
            minute = 30
        else:
            match = _HOUR_MINUTE.search(normalized)
            if match:
                hour = int(match.group(1))
                if match.group(2):
                    minute = int(match.group(2))

    if hour is None:
        return None
    if hour > 23 or minute > 59:
        return None

    hour = _apply_period(hour, normalized)
    result = datetime(base_date.year, base_date.month, base_date.day, hour, minute)

    if result <= now and not explicit_future_day and not _TODAY.search(normalized):
        result += timedelta(days=1)

    return result


def extract_title(text: str) -> str:
    """Remove common reminder/time words and keep a compact task title."""
    normalized = _replace_cn_numbers(text.strip())
    patterns = [
        _RELATIVE_MINUTES,
        _RELATIVE_HOURS,
        _RELATIVE_DAYS,
        _TODAY,
        _TOMORROW,
        _DAY_AFTER_TOMORROW,
        _DAILY,
        _MORNING,
        _NOON,
        _AFTERNOON,
        _EVENING,
        _MIDNIGHT,
        _COLON_TIME,
        _HALF_HOUR,
        _HOUR_MINUTE,
        _REMIND_WORDS,
        re.compile(r"到时候|的时候|请|一下"),
    ]
    title = normalized
    for pattern in patterns:
        title = pattern.sub("", title)
    title = re.sub(r"\s+", "", title)
    title = title.strip("，。,.；;：:、")
    return (title or normalized)[:255]
