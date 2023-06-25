import logging
import time
from datetime import datetime, timedelta
import inspect
import textwrap
import pickle
import requests

from decouple import config
from django.conf import settings
from pymongo import DESCENDING

from stocks_data_downloader.models import SchedularTable, SchedularHistory, SubscribedData
from utils.shoonya_api import sapi

from utils.mongo_conn import db

logger = logging.getLogger(__name__)
tz = settings.INDIAN_TIMEZONE


def is_working_hr():
    time_now = datetime.now()
    market_start_time = time_now.replace(hour=9, minute=14, second=0, microsecond=0)
    market_end_time = time_now.replace(hour=15, minute=31, second=0, microsecond=0)
    if time_now.weekday() < 5:
        return market_start_time <= time_now <= market_end_time
    return False


def convert_function_to_text(func):
    source, _ = inspect.getsourcelines(func)
    return textwrap.dedent(''.join(source))


def pickle_func(func):
    return pickle.dumps(func)


def unpickle_func(func):
    return pickle.loads(func)


def get_timedelta_minutes(tdelta):
    minutes = tdelta.seconds / 60
    if minutes < 1:
        return 1
    return int(minutes)


def update_status(model, status):
    model.status = status
    model.save()
    return True


def get_timedelta(str_time):
    interval = int(str_time[:-1])
    if str_time.endswith("s"):
        return timedelta(seconds=interval)
    elif str_time.endswith("m"):
        return timedelta(minutes=interval)
    elif str_time.endswith("h"):
        return timedelta(hours=interval)
    elif str_time.endswith("d"):
        return timedelta(days=interval)
    else:
        return timedelta(minutes=1)


def get_last_status(metadata):
    try:
        return metadata.history.last().status
    except AttributeError:
        return None


def upload_to_gofile_bucket(filepath, filename):
    try:
        best_server = requests.get("https://api.gofile.io/getServer", timeout=30).json()["data"]["server"]
        upload_api = f"https://{best_server}.gofile.io/uploadFile"
        data = {"token": config("GOFILE_TOKEN"), "folderId": config("GOFILE_FOLDER")}
        response = requests.post(upload_api, files={filename: filepath}, data=data)
        if response.ok:
            logger.info(f"Log {filename} uploaded to GoFiles bucket successfully.. \n"
                        f"Response body {response.json()}")
            return
        logger.info(f"Log {filename} uploading returned {response.status_code} status code on GoFile.. \n"
                    f"Response body {response.json()}")
    except Exception:
        logger.exception(f"Something went wrong while uploading {filename} to GoFiles")
    return


def register_function(func, interval):
    function_name = func.__name__
    function_src = convert_function_to_text(func)
    old_schedular_task = SchedularTable.objects.filter(function_name=function_name, interval=interval).first()
    interval_timedelta = get_timedelta(interval)
    start_time = datetime.now(tz=settings.INDIAN_TIMEZONE).replace(second=0, microsecond=0)

    last_run = start_time.replace(minute=start_time.minute - start_time.minute %
                                  get_timedelta_minutes(interval_timedelta))
    next_run = last_run + interval_timedelta
    if old_schedular_task:
        old_schedular_task.last_run = last_run.timestamp()
        old_schedular_task.next_run = next_run.timestamp()
        if old_schedular_task.readable_function != function_src:
            old_schedular_task.serializer_function = pickle_func(func)
            old_schedular_task.readable_function = function_src
            old_schedular_task.save()
            logger.info(f"source code seems to be changed.. Updating {function_name} function in schedular.")
            return
        old_schedular_task.save()
        logger.info(f"Function with {function_name} already exists.")
        return
    logger.info(f"Registering new function with the name {function_name} and interval of {interval}")
    serialized_function = pickle_func(func)
    schedular = SchedularTable(function_name=function_name, serialized_function=serialized_function,
                               readable_function=function_src, next_run=next_run.timestamp(), interval=interval,
                               last_run=last_run.timestamp())
    schedular.save()
    logger.info(f"Registered {function_name} function to schedular with time interval of every {interval} interval")
    return


def run_n_update_task(metadata):
    c_time = datetime.now(tz=settings.INDIAN_TIMEZONE).strftime("%d-%m-%Y %H:%M:%S")
    logger.info(f"Running {metadata.function_name} function at {c_time}, time interval of {metadata.interval}")
    update_status(metadata, "running")
    history = SchedularHistory(run_at=datetime.now(tz=settings.INDIAN_TIMEZONE).timestamp(), scheduler_details=metadata)
    next_run = datetime.fromtimestamp(metadata.next_run, tz=settings.INDIAN_TIMEZONE) + get_timedelta(metadata.interval)
    metadata.last_status = get_last_status(metadata)
    metadata.last_run = metadata.next_run
    metadata.next_run = next_run.timestamp()
    metadata.run_counts += 1

    try:
        serialized_function = unpickle_func(metadata.serialized_function)
        serialized_function(task_instance=metadata)
        metadata.successful += 1
        update_status(metadata, "scheduled")
        update_status(history, "success")
        c_time = datetime.now(tz=settings.INDIAN_TIMEZONE).strftime("%d-%m-%Y %H:%M:%S")
        logger.info(f'Success running {metadata.function_name} function at {c_time}, time interval of'
                    f' {metadata.interval}')
    except Exception as e:
        history.exception = e
        metadata.failed += 1
        update_status(metadata, "scheduled")
        update_status(history, "failed")
        c_time = datetime.now(tz=settings.INDIAN_TIMEZONE).strftime("%d-%m-%Y %H:%M:%S")
        logger.exception(f'Failed {metadata.function_name} function at {c_time}, time interval of {metadata.interval}')


def get_ohlvc(queryset, meta, close_at):
    candle = {"Tick": meta.token, "Symbol": meta.symbol, "Open": None, "High": None, "Low": None,
              "Close": None, "Volume": 0, "unix_time": close_at, "length": None}
    temp_volume = 0
    length = set()
    for record in queryset:
        if record.ltp:
            if not candle["Open"]:
                candle["Open"] = record.ltp
                candle["High"] = record.ltp
                candle["Low"] = record.ltp
            elif record.ltp < candle["Low"]:
                candle["Low"] = record.ltp
            elif record.ltp > candle["High"]:
                candle["High"] = record.ltp
            candle["Close"] = record.ltp
        if record.volume:
            if temp_volume < 1:
                temp_volume = record.volume
            else:
                candle["Volume"] += record.volume - temp_volume
                temp_volume = record.volume
        length.add(record.unix_time)
    candle["length"] = len(length)
    return candle


def mongo_get_latest_id(collection_name):
    record = db[collection_name].find_one(sort=[("id", DESCENDING)])
    if record:
        return record["id"], record["unix_time"]
    return 0, 0


def mongo_convert_to_dict(queryset, last_id):
    def _convert(query, id_):
        doc_dict = query.__dict__
        doc_dict.pop("_state")
        doc_dict["id"] = id_
        return doc_dict

    ids = [i for i in range(last_id+1, last_id+len(queryset)+1)]
    return list(map(_convert, queryset, ids))


def subscribe_all_tokens():
    subscribed_tokens = SubscribedData.objects.filter(is_active=True)
    logger.info(f"Subscribing all {len(subscribed_tokens)} tokens")
    if sapi.is_feed_opened:
        for t in subscribed_tokens:
            sapi.subscribe_wsticks(t.token)
        logger.info(f"Subscribed all {len(subscribed_tokens)} tokens")
    else:
        logger.info("Websocket feed is not open.. Skipping subscribe token..")


def send_telegram_msg(msg):
    for i in range(5):
        response = requests.get(settings.TELEGRAM_MSG_API + msg)
        if response.ok:
            return True
        time.sleep(1)
    return False
