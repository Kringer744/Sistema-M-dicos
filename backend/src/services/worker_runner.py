"""Orquestrador dos workers: stream + scheduler de lembretes + pós-venda diário."""
import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from src.core.config import get_settings
from src.services import lembrete_service, posvenda_service, stream_worker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("worker")
settings = get_settings()


async def main():
    scheduler = AsyncIOScheduler(timezone=settings.TZ)
    scheduler.add_job(
        lembrete_service.disparar_pendentes,
        IntervalTrigger(minutes=1),
        id="disparar_lembretes",
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        posvenda_service.rodar_diariamente,
        CronTrigger(hour=settings.POSVENDA_HORA_DIARIA, minute=0),
        id="posvenda_diario",
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    logger.info("scheduler iniciado")

    try:
        await stream_worker.run()
    finally:
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    asyncio.run(main())
