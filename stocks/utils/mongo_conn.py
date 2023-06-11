from decouple import config
from django.conf import settings
from pymongo import MongoClient


mongo_conn = MongoClient(config('MONGODB_HOST'))
db = mongo_conn[settings.MONGO_DATABASE]
