"""Загрузка и разбор расписания с timetable.spbu.ru.

Страница отдаётся сервером уже готовым HTML (без JS-рендеринга), поэтому
достаточно обычного requests.get + BeautifulSoup — headless-браузер не нужен.
"""
import re
from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup

from config import BASE_URL, GROUP_PATH

MONTHS_GENITIVE = {
    "января": 1, "февраля": 2, "марта": 3, "апреля": 4, "мая": 5, "июня": 6,
    "июля": 7, "августа": 8, "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
}

HEADER_RE = re.compile(r"(\d{1,2})\s+([а-яёА-ЯЁ]+)")

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; spbu-schedule-bot/1.0)"}


def _week_monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


def fetch_week_html(monday: date) -> str:
    url = f"{BASE_URL}{GROUP_PATH}/{monday.isoformat()}"
    resp = requests.get(url, timeout=15, headers=HEADERS)
    resp.raise_for_status()
    return resp.text


def _parse_event(li) -> dict | None:
    time_span = li.select_one("div.studyevent-datetime span.moreinfo")
    subject_div = li.select_one("div.studyevent-subject")
    if not time_span or not subject_div:
        return None

    subject_span = subject_div.select_one("span.moreinfo")
    if not subject_span:
        return None

    time_text = time_span.get_text(strip=True).replace("–", "-").replace("—", "-")
    subject_text = subject_span.get_text(strip=True)

    subgroup = None
    icon_divs = subject_div.select("div.with-icon")
    if len(icon_divs) > 1:
        sg_span = icon_divs[1].select_one("span")
        if sg_span:
            m = re.search(r"\d+", sg_span.get_text(strip=True))
            if m:
                subgroup = m.group(0)

    return {"time": time_text, "subject": subject_text, "subgroup": subgroup}


def parse_events_for_date(html: str, target: date) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")

    for panel in soup.select("div.panel.panel-default"):
        heading = panel.select_one("h4.panel-title")
        if not heading:
            continue
        m = HEADER_RE.search(heading.get_text(strip=True))
        if not m:
            continue
        day_num = int(m.group(1))
        month_num = MONTHS_GENITIVE.get(m.group(2).lower())
        if month_num is None:
            continue
        if day_num == target.day and month_num == target.month:
            return [
                ev for li in panel.select("li.common-list-item") if (ev := _parse_event(li))
            ]
    return []


def get_events_for_date(target: date) -> list[dict]:
    monday = _week_monday(target)
    html = fetch_week_html(monday)
    return parse_events_for_date(html, target)
