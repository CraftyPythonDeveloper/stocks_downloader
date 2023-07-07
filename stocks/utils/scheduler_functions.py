import logging
import os
import shutil
import time
from datetime import datetime, timedelta
from django.conf import settings
import requests
from pymongo.errors import BulkWriteError

from django.apps import apps
from django.db.models import Q
from utils.misc import (is_working_hr, upload_to_gofile_bucket, get_ohlvc, mongo_convert_to_dict, \
    mongo_get_latest_id, send_telegram_msg, is_candle_ended)
from stocks_data_downloader.models import (SubscribedData, WebSocketData, DailySubscribe, CandleOne, CandleFive,
                                                  CandleFifteen, CandleThirty, CandleSixty)
from utils.mongo_conn import db
from utils.shoonya_api import sapi, shoonya_refresh

from stocks_data_downloader.models import WatcherHistory, StockWatcher

logger = logging.getLogger(__name__)
CANDLE_TIMEFRAMES = {1: CandleOne, 5: CandleFive, 15: CandleFifteen, 30: CandleThirty, 60: CandleSixty}
tables_to_migrate = settings.TABLES_TO_MIGRATE
models = {model._meta.db_table: model for model in apps.get_models()}
valid_tables = [table for table in tables_to_migrate if table in models.keys()]
tz = settings.INDIAN_TIMEZONE

def draw_candle_v2(**kwargs):
    if not is_working_hr():
        return
    task_instance = kwargs["task_instance"]
    timeframe = int(task_instance.interval[:-1])
    active_ticks = SubscribedData.objects.filter(is_active=True).all()
    time_from = datetime.fromtimestamp(task_instance.last_run, tz=settings.INDIAN_TIMEZONE).strftime("%d-%m-%Y %H:%M:%S")
    time_to = datetime.fromtimestamp(task_instance.next_run, tz=settings.INDIAN_TIMEZONE).strftime('%d-%m-%Y %H:%M:%S')
    logger.info(f"Making candle of {timeframe} minutes from {time_from} to {time_to}")
    for tick in active_ticks:
        # queryset = WebSocketData.objects.filter(tick=tick.token, unix_time__gte=task_instance.last_run,
        #                                         unix_time__lt=task_instance.next_run).order_by("unix_time")
        queryset = tick.data.filter(unix_time__gte=task_instance.last_run,
                                    unix_time__lt=task_instance.next_run).order_by("id")
        if queryset:
            logger.info(f"using {len(queryset)} rows to calculate {timeframe} minute candle {time_from} to {time_to}")
            candle = get_ohlvc(queryset=queryset, meta=tick, close_at=task_instance.last_run)
            candle_obj = CANDLE_TIMEFRAMES[timeframe](**candle)
            candle_obj.save()
        else:
            logger.info(f"No data for tick {tick.token} timeframe {timeframe} from {time_from} to"
                        f" {time_to} to make candle")
    logger.info(f"Inserted {timeframe} minutes candle")


def self_ping(**kwargs):
    try:
        response = requests.get("https://stock-data-downloader.onrender.com/ping", timeout=30)
        if response.ok:
            logger.info("Server is alive..")
            return True
        logger.error(f"server seems not accessible. Status code: {response.status_code}")
        return False
    except requests.exceptions.ConnectTimeout:
        logger.error(f"Ping timed out.. Server seems offline..")
        return False


def upload_logs(**kwargs):
    # copy/clear/send
    log_name = datetime.now().strftime("backend_%d-%m-%Y_%H-%M.log")
    src = os.path.join(settings.LOGFILE_FOLDER, "backend.log")
    dest = os.path.join(settings.LOGFILE_FOLDER, log_name)
    file_loc = shutil.copy(src, dest)
    with open(file_loc, 'rb') as fp:
        data = fp.read()
    upload_to_gofile_bucket(filepath=data, filename=log_name)
    logger.info("Log file uploaded successfully")
    open(src, 'w').close()
    os.remove(dest)
    return True


def subscribe_unsubscribe_market(**kwargs):
    if not is_working_hr():
        return
    if datetime.now().replace(hour=9, minute=14, second=0) <= datetime.now() <=\
            datetime.now().replace(hour=9, minute=16, second=0):
        logger.info("Market is open...")
        unix_time = datetime.now().replace(hour=9, minute=14, second=0).timestamp()
        sub = DailySubscribe.objects.filter(unix_time=unix_time).last()
        if not sub:
            shoonya_refresh()
            logger.info("Opened websocket..")
            ticks = SubscribedData.objects.filter(is_active=True)
            for t in ticks:
                sapi.subscribe_wsticks(t.token)
            update_status = DailySubscribe(unix_time=unix_time, subscribe=True)
            update_status.save()
            logger.info(f"Market is open auto-subscribed to all {len(ticks)} active ticks")
            return
        logger.info("Already auto-subscribed ticks. Skipping...")
        return
    elif datetime.now().replace(hour=15, minute=30, second=0) <= datetime.now() <=\
            datetime.now().replace(hour=15, minute=32, second=0):
        logger.info("Market is closed...")
        unix_time = datetime.now().replace(hour=9, minute=14, second=0).timestamp()
        sub = DailySubscribe.objects.filter(unix_time=unix_time, unsubscribe=True).last()
        if not sub:
            ticks = SubscribedData.objects.filter(is_active=True)
            for t in ticks:
                sapi.unsubscribe_wsticks(t.token)
            shoonya_refresh("logout")
            logger.info("Closed websocket..")
            latest_record = DailySubscribe.objects.filter(unix_time=unix_time).last()
            if latest_record:
                latest_record.unsubscribe = True
                latest_record.save()
            else:
                latest_record = DailySubscribe(unix_time=unix_time, unsubscribe=True)
                latest_record.save()
            logger.info(f"Market is closed auto-unsubscribed to all {len(ticks)} active ticks")
            return
        logger.info("Already auto-unsubscribed ticks. Skipping...")
        return


def migrate_table(**kwargs):
    if not is_working_hr():
        return
    for table in valid_tables:
        latest_id, unix_time = mongo_get_latest_id(table)
        data = models[table].objects.filter(Q(id__gt=latest_id) | Q(unix_time__gt=unix_time)).order_by("id")
        if not data:
            continue
        data_dict = mongo_convert_to_dict(data, latest_id)
        try:
            db[table].insert_many(data_dict)
        except BulkWriteError as e:
            for dup_record in e.details['writeErrors']:
                if dup_record["code"] == 11000:
                    db[table].delete_many(dup_record["keyValue"])
                    logger.info(f'Found duplicate {dup_record["keyValue"]}. deleting from db')
                else:
                    logger.exception(e)
        except Exception:
            logger.exception("Exception occurred while inserting data into mongo db")


def purge_old_data(**kwargs):
    old_dt = datetime.now(tz=settings.INDIAN_TIMEZONE) - timedelta(days=3)
    for table_name in valid_tables:
        if table_name != "websocket_data":
            old_dt += timedelta(days=7)
        models[table_name].objects.filter(unix_time__lt=old_dt.timestamp()).delete()
        results = db[table_name].remove({"unix_time": {"$lt": old_dt.timestamp()}})
        logger.info(f"Deleted old data from {table_name} table. Data older than {old_dt.strftime('%d-%m-%Y')}. "
                    f"Total number of rows deleted {results['n']}")


def stock_watcher():
    while True:
        if not is_working_hr():
            time.sleep(30)
            return
        try:
            stocks_to_watch = StockWatcher.objects.filter(is_active=True)
            for stock in stocks_to_watch:
                if not stock.tick.is_active:
                    stock.is_active = False
                    stock.save()
                    continue
                data = stock.tick.data.exclude(ltp=None).last()
                # data = WebSocketData.objects.filter(tick=stock.tick.token).exclude(ltp=None).last()
                if stock.price_low < data.ltp < stock.price_high:
                    # send telegram alert
                    msg = f"Your stock {stock.tick.symbol} is in range of your watchlist. \n CURRENT PRICE ==> " \
                          f"{data.ltp} \n \n PRICE RANGE ==> {stock.price_low} TO {stock.price_high}. \n"
                    result = send_telegram_msg(msg)
                    if not result:
                        logger.error("unable to send msg to telegram group..")
                        time.sleep(1)
                        continue
                    logger.info(f"Target price for {data.tick} with price {data.ltp} is in range of {stock.price_low} "
                                f"to {stock.price_high}")
                    history = WatcherHistory(stock=stock, ltp=data.ltp,
                                             unix_time=datetime.now(tz=settings.INDIAN_TIMEZONE).timestamp())
                    stock.is_active = False
                    history.save()
                    stock.save()
                time.sleep(1)
        except Exception:
            logger.exception("Exception in stock watcher thread..")
            time.sleep(1)


def draw_candle(timeframe):
    if timeframe not in CANDLE_TIMEFRAMES.keys():
        logger.error("Not a valid timeframe.. use (1, 5, 15, 30 ,60)")
        return
    start_time = datetime.now().replace(second=0, microsecond=0)
    start_time = start_time.replace(minute=start_time.minute - start_time.minute % timeframe)
    while True:
        if not is_working_hr():
            time.sleep(30)
            continue
        if is_candle_ended(start_time, timeframe):
            start = int(start_time.timestamp())
            end = int(datetime.now().timestamp())
            start_time = datetime.now().replace(second=0, microsecond=0)
            logger.info(f"Getting data from {start} to {end} for {timeframe} timeframe to make candle.")
            try:
                active_ticks = SubscribedData.objects.filter(is_active=True).all()
                time_from = datetime.fromtimestamp(start, tz=tz).strftime("%d-%m-%Y %H:%M:%S")
                time_to = datetime.fromtimestamp(end, tz=tz).strftime('%d-%m-%Y %H:%M:%S')
                for tick in active_ticks:
                    queryset = tick.data.filter(unix_time__gte=start, unix_time__lt=end).order_by("unix_time")
                    if queryset:
                        candle = get_ohlvc(queryset=queryset, meta=tick, close_at=start)
                        # CANDLE_TIMEFRAMES[timeframe].objects.create(**candle)
                        candle_obj = CANDLE_TIMEFRAMES[timeframe](**candle)
                        try:
                            candle_obj.save()
                        except Exception:
                            logger.exception(f"Exception while inserting data for tick {tick.token}, candle {candle}")
                    else:
                        logger.info(f"No data for tick {tick.token} timeframe {timeframe} from {time_from} to"
                                    f" {time_to} to make candle")
                logger.info(f"Inserted {timeframe} minutes candle")
            except Exception:
                logger.exception(f"Exception occurred while generating {timeframe} minutes candle..")
            continue
        time.sleep(1)
