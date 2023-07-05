from threading import Thread
from utils.scheduler import run_schedular
from utils.scheduler_functions import stock_watcher
import logging
from .scheduler_functions import draw_candle


logger = logging.getLogger(__name__)


class CustomThread:
    main_schedular = Thread(target=run_schedular, daemon=True, name="Main Schedular")
    stock_watcher_thread = Thread(target=stock_watcher, daemon=True, name="Stock Watcher")
    one_minutes_candle = Thread(target=draw_candle, args=(1,), daemon=True, name="One Minutes Candle Thread")
    five_minutes_candle = Thread(target=draw_candle, args=(5,), daemon=True, name="Five Minutes Candle Thread")
    fifteen_minutes_candle = Thread(target=draw_candle, args=(15,), daemon=True, name="Fifteen Minutes Candle Thread")
    thirty_minutes_candle = Thread(target=draw_candle, args=(30,), daemon=True, name="Thirty Minutes Candle Thread")
    sixty_minutes_candle = Thread(target=draw_candle, args=(60,), daemon=True, name="Sixty Minutes Candle Thread")


LIST_OF_THREADS = [v for k, v in CustomThread.__dict__.items() if not k.startswith("_")]


def run_thread(thread):
    try:
        thread.start()
        logger.info(f"Started running thread {thread.name} in background..")
        return thread
    except RuntimeError:
        logger.error(f"Thread {thread.name} is already running..")
        return thread
