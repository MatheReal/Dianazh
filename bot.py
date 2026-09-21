import asyncio
import logging
from datetime import date, timedelta

from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import BOT_TOKEN, CHAT_ID, SEND_HOUR, SEND_MINUTE, TIMEZONE
from formatter import format_day
from scraper import get_events_for_date

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def build_schedule_text(target: date) -> str:
    try:
        events = get_events_for_date(target)
    except Exception:
        logger.exception("Failed to fetch/parse schedule for %s", target)
        return f"Не получилось загрузить расписание на {target.isoformat()}. Попробуй ещё раз чуть позже."
    return format_day(target, events)


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я присылаю расписание СПбГУ.\n\n"
        "/today — расписание на сегодня\n"
        "/tomorrow — расписание на завтра\n\n"
        f"Твой chat_id: {message.chat.id}\n"
        "Чтобы расписание на завтра приходило само каждый вечер, впиши этот "
        "chat_id в переменную окружения CHAT_ID и перезапусти бота."
    )


@dp.message(Command("today"))
async def cmd_today(message: Message):
    await message.answer(build_schedule_text(date.today()))


@dp.message(Command("tomorrow"))
async def cmd_tomorrow(message: Message):
    await message.answer(build_schedule_text(date.today() + timedelta(days=1)))


async def send_tomorrow_schedule():
    if not CHAT_ID:
        logger.warning("CHAT_ID не задан — автоматическая отправка пропущена")
        return
    text = build_schedule_text(date.today() + timedelta(days=1))
    await bot.send_message(CHAT_ID, f"Расписание на завтра:\n\n{text}")


async def main():
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    scheduler.add_job(
        send_tomorrow_schedule,
        CronTrigger(hour=SEND_HOUR, minute=SEND_MINUTE, timezone=TIMEZONE),
    )
    scheduler.start()
    logger.info(
        "Бот запущен. Автоотправка расписания на завтра: %02d:%02d %s",
        SEND_HOUR, SEND_MINUTE, TIMEZONE,
    )
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
