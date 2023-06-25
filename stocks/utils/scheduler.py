import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import logging
from django.conf import settings

from stocks_data_downloader.models import SchedularTable, StockWatcher, WebSocketData, WatcherHistory
from utils.misc import run_n_update_task


logger = logging.getLogger(__name__)


def run_schedular():
    while True:
        try:
            st = time.time()
            unix_now = datetime.now(tz=settings.INDIAN_TIMEZONE).timestamp()
            tasks_to_run = SchedularTable.objects.filter(is_enabled=True, next_run__lte=unix_now)
            if tasks_to_run:
                logger.info(f"Number of tasks to run {len(tasks_to_run)}")
            with ThreadPoolExecutor(max_workers=50) as executor:
                for task in tasks_to_run:
                    executor.submit(run_n_update_task, task)
            finish_time = time.time() - st
            if tasks_to_run:
                logger.info(f"Took {finish_time} seconds to run {len(tasks_to_run)} tasks.")
            if finish_time > 1 <= (settings.SCHEDULAR_INTERVAL - finish_time):
                time.sleep(settings.SCHEDULAR_INTERVAL - finish_time)
            else:
                time.sleep(2)
        except Exception:
            logger.exception("Exception in main schedular")
            time.sleep(2)
