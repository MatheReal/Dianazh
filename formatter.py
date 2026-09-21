from datetime import date

from config import RULES

WEEKDAY_NAMES = [
    "понедельник", "вторник", "среда", "четверг",
    "пятница", "суббота", "воскресенье",
]

MONTHS_RU = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля", 5: "мая", 6: "июня",
    7: "июля", 8: "августа", 9: "сентября", 10: "октября", 11: "ноября", 12: "декабря",
}


def apply_rules(subject: str, subgroup: str | None) -> str | None:
    """Возвращает сокращённое название, None (если предмет нужно скрыть)
    или исходное название, если ни одно правило не подошло."""
    for rule in RULES:
        if not subject.startswith(rule["match"]):
            continue
        if rule.get("subgroup") is not None and rule["subgroup"] != subgroup:
            continue
        if rule.get("exclude"):
            return None
        return rule.get("short", subject)
    return subject


def format_day(target: date, events: list[dict]) -> str:
    header = f"{WEEKDAY_NAMES[target.weekday()]}, {target.day} {MONTHS_RU[target.month]}"
    lines = [header]
    has_events = False
    for ev in events:
        name = apply_rules(ev["subject"], ev["subgroup"])
        if name is None:
            continue
        lines.append(f"{ev['time']} {name}")
        has_events = True
    if not has_events:
        lines.append("Занятий нет")
    return "\n".join(lines)
