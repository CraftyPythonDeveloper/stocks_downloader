from django.db import models
from django.utils import timezone
from datetime import datetime
import pytz

tz = pytz.timezone('Asia/kolkata')


# Create your models here.

class TestModelMongo(models.Model):
    name = models.CharField(max_length=200, default=None)
    age = models.IntegerField(default=None)
    created_at = models.DateTimeField(editable=True)
    modified = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.id:
            self.created_at = timezone.now()
        self.modified = timezone.now()
        return super(TestModelMongo, self).save(*args, **kwargs)


class WebSocketData(models.Model):
    tick = models.IntegerField()
    unix_time = models.IntegerField()
    ltp = models.FloatField(null=True)
    volume = models.IntegerField(null=True)
    date_time = models.CharField(max_length=50, null=True)

    def save(self, *args, **kwargs):
        self.date_time = datetime.fromtimestamp(self.unix_time, tz=tz).strftime("%d-%m-%Y %H:%M:%S")
        return super(WebSocketData, self).save(*args, *kwargs)


class SubscribedData(models.Model):
    token = models.IntegerField()
    exchange = models.CharField(max_length=100)
    symbol = models.CharField(max_length=100)
    cname = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
