# this will migrate data from sqlite to mongodb
import shutil

import requests
from django.apps import apps
from django.conf import settings
from decouple import config
from pymongo import MongoClient, DESCENDING
from pymongo.errors import BulkWriteError
import time
from django.db.models import Q
import logging
from datetime import datetime, timedelta
from urllib import error, request
from stocks_data_downloader.models import DailySubscribe, SubscribedData
from utils.shoonya_api import sapi, shoonya_refresh
from utils.make_candles import is_working_hr
import os

logger = logging.getLogger(__name__)

mongo_conn = MongoClient(config('MONGODB_HOST'))
db = mongo_conn[settings.MONGO_DATABASE]


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


tables_to_migrate = settings.TABLES_TO_MIGRATE
models = {model._meta.db_table: model for model in apps.get_models()}
valid_tables = [table for table in tables_to_migrate if table in models.keys()]


def self_ping():
    try:
        response = request.urlopen("https://stock-data-downloader.onrender.com/ping", timeout=30)
        if response.status == 200:
            logger.info("Server is alive..")
            return True
        logger.error(f"server seems not accessible. Status code: {response.status}")
        return False
    except error.HTTPError:
        logger.error(f"Ping timed out.. Server seems offline..")
        return False


def subscribe_unsubscribe_market():
    if not is_working_hr():
        return
    try:
        if datetime.now().replace(hour=9, minute=14, second=0) <= datetime.now() <=\
                datetime.now().replace(hour=9, minute=16, second=0):
        # if datetime.now().replace(hour=23, minute=55, second=0) <= datetime.now() <= \
        #         datetime.now().replace(hour=23, minute=56, second=0):
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
        # elif datetime.now().replace(hour=23, minute=58, second=0) <= datetime.now() <= \
        #      datetime.now().replace(hour=23, minute=59, second=0):
            # unsubscribe all ticks
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
    except Exception:
        logger.exception(f"Exception occurred in subscribe_unsubscribe_market()..")


def migrate_table():
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
        logger.exception(f"Something went wrong while uploading {filename} to gofiles")
    return


def upload_logs(previous_time, timeframe):
    if not previous_time + timedelta(hours=timeframe) <= datetime.now().replace(minute=0, second=0, microsecond=0):
        return previous_time
    # copy/clear/send
    try:
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
        return previous_time + timedelta(hours=timeframe)
    except Exception:
        logger.exception("Exception occured in upload_logs().. ")
        return previous_time


def migrate_tables(interval):
    go_file_start_time = datetime.now().replace(minute=0, second=0, microsecond=0)
    while True:
        try:
            subscribe_unsubscribe_market()
            go_file_start_time = upload_logs(go_file_start_time, timeframe=3)
            migrate_table()
            self_ping()
        except Exception:
            logger.exception("Exception in db_migrations..")
        time.sleep(interval)
