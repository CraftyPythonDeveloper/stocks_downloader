# this will migrate data from sqlite to mongodb
from django.apps import apps
from django.conf import settings
from decouple import config
from pymongo import MongoClient, DESCENDING
import time
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)

mongo_conn = MongoClient(config('MONGODB_HOST'))
db = mongo_conn[settings.MONGO_DATABASE]


def mongo_get_latest_id(collection_name):
    record = db[collection_name].find_one(sort=[("_id", DESCENDING)])
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


def migrate_table():
    for table in valid_tables:
        latest_id, unix_time = mongo_get_latest_id(table)
        data = models[table].objects.filter(Q(id__gt=latest_id) | Q(unix_time__gt=unix_time)).order_by("id")
        if not data:
            continue
        data_dict = mongo_convert_to_dict(data, latest_id)
        db[table].insert_many(data_dict)


def migrate_tables(interval):
    while True:
        try:
            migrate_table()
            time.sleep(interval)
        except Exception:
            logger.exception("Exception in db_migrations..")
            time.sleep(interval)
