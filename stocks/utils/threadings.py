from threading import Thread
from utils.scheduler import run_schedular
from utils.scheduler_functions import stock_watcher
import logging

logger = logging.getLogger(__name__)


class CustomThread:
    main_schedular = Thread(target=run_schedular, daemon=True, name="Main Schedular")
    stock_watcher_thread = Thread(target=stock_watcher, daemon=True, name="Stock Watcher")


LIST_OF_THREADS = [v for k, v in CustomThread.__dict__.items() if not k.startswith("_")]


def run_thread(thread):
    try:
        thread.start()
        logger.info(f"Started running thread {thread.name} in background..")
        return thread
    except RuntimeError:
        logger.error(f"Thread {thread.name} is already running..")
        return thread
