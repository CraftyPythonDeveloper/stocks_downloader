import logging
import os
import shutil
from datetime import datetime, timedelta
from django.conf import settings
import requests
from pymongo.errors import BulkWriteError

from django.apps import apps
from django.db.models import Q
from utils.misc import is_working_hr, upload_to_gofile_bucket, get_ohlvc, mongo_convert_to_dict, \
    mongo_get_latest_id
from stocks_data_downloader.models import (SubscribedData, WebSocketData, DailySubscribe, CandleOne, CandleFive,
                                                  CandleFifteen, CandleThirty, CandleSixty)
from utils.mongo_conn import db
from utils.shoonya_api import sapi, shoonya_refresh

logger = logging.getLogger(__name__)
CANDLE_TIMEFRAMES = {1: CandleOne, 5: CandleFive, 15: CandleFifteen, 30: CandleThirty, 60: CandleSixty}
tables_to_migrate = settings.TABLES_TO_MIGRATE
models = {model._meta.db_table: model for model in apps.get_models()}
valid_tables = [table for table in tables_to_migrate if table in models.keys()]


def draw_candle_v2(**kwargs):
    task_instance = kwargs.get("task_instance")
    if not is_working_hr():
        return
    timeframe = int(task_instance.interval[:-1])
    active_ticks = SubscribedData.objects.filter(is_active=True).all()
    time_from = datetime.fromtimestamp(task_instance.last_run, tz=settings.INDIAN_TIMEZONE).strftime("%d-%m-%Y %H:%M:%S")
    time_to = datetime.fromtimestamp(task_instance.next_run, tz=settings.INDIAN_TIMEZONE).strftime('%d-%m-%Y %H:%M:%S')
    logger.info(f"Making candle of {timeframe} minutes from {time_from} to {time_to}")
    for tick in active_ticks:
        queryset = WebSocketData.objects.filter(tick=tick.token, unix_time__gte=task_instance.last_run,
                                                unix_time__lt=task_instance.next_run).order_by("unix_time")
        if queryset:
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
    old_dt = datetime.now(tz=settings.INDIAN_TIMEZONE) - timedelta(days=7)
    for table_name in valid_tables:
        models[table_name].objects.filter(unix_time__lt=old_dt.timestamp()).delete()
        results = db[table_name].remove({"unix_time": {"$lt": old_dt.timestamp()}})
        logger.info(f"Deleted old data from {table_name} table. Data older than {old_dt.strftime('%d-%m-%Y')}. "
                    f"Total number of rows deleted {results['n']}")
