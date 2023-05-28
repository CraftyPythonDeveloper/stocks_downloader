from django.db import models
from datetime import datetime
import pytz

tz = pytz.timezone('Asia/kolkata')


class WebSocketData(models.Model):
    tick = models.IntegerField(null=False)
    unix_time = models.IntegerField(null=False)
    ltp = models.FloatField(null=True)
    volume = models.IntegerField(null=True)
    date_time = models.CharField(max_length=50, null=True)

    def save(self, *args, **kwargs):
        self.date_time = datetime.fromtimestamp(self.unix_time, tz=tz).strftime("%d-%m-%Y %H:%M:%S")
        return super(WebSocketData, self).save(*args, *kwargs)

    class Meta:
        db_table = "websocket_data"


class SubscribedData(models.Model):
    token = models.IntegerField(null=False)
    exchange = models.CharField(max_length=100, null=True)
    symbol = models.CharField(max_length=100, null=False)
    cname = models.CharField(max_length=100, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=False)

    class Meta:
        db_table = "subscribed_data"


class CandleOne(models.Model):
    Tick = models.IntegerField(null=False)
    Symbol = models.CharField(max_length=100, null=True)
    Open = models.FloatField(null=True)
    High = models.FloatField(null=True)
    Low = models.FloatField(null=True)
    Close = models.FloatField(null=True)
    Volume = models.IntegerField(null=True)
    unix_time = models.IntegerField(null=True)
    length = models.IntegerField(null=True)
    date_time = models.CharField(max_length=50, null=True)

    def save(self, *args, **kwargs):
        self.date_time = datetime.fromtimestamp(self.unix_time, tz=tz).strftime("%d-%m-%Y %H:%M")
        return super(CandleOne, self).save(*args, *kwargs)

    class Meta:
        db_table = "candle_one"


class CandleFive(models.Model):
    Tick = models.IntegerField(null=False)
    Symbol = models.CharField(max_length=100, null=True)
    Open = models.FloatField(null=True)
    High = models.FloatField(null=True)
    Low = models.FloatField(null=True)
    Close = models.FloatField(null=True)
    Volume = models.IntegerField(null=True)
    unix_time = models.IntegerField(null=True)
    length = models.IntegerField(null=True)
    date_time = models.CharField(max_length=50, null=True)

    def save(self, *args, **kwargs):
        self.date_time = datetime.fromtimestamp(self.unix_time, tz=tz).strftime("%d-%m-%Y %H:%M")
        return super(CandleFive, self).save(*args, *kwargs)

    class Meta:
        db_table = "candle_five"


class CandleFifteen(models.Model):
    Tick = models.IntegerField(null=False)
    Symbol = models.CharField(max_length=100, null=True)
    Open = models.FloatField(null=True)
    High = models.FloatField(null=True)
    Low = models.FloatField(null=True)
    Close = models.FloatField(null=True)
    Volume = models.IntegerField(null=True)
    unix_time = models.IntegerField(null=True)
    length = models.IntegerField(null=True)
    date_time = models.CharField(max_length=50, null=True)

    def save(self, *args, **kwargs):
        self.date_time = datetime.fromtimestamp(self.unix_time, tz=tz).strftime("%d-%m-%Y %H:%M")
        return super(CandleFifteen, self).save(*args, *kwargs)

    class Meta:
        db_table = "candle_fifteen"


class CandleThirty(models.Model):
    Tick = models.IntegerField(null=False)
    Symbol = models.CharField(max_length=100, null=True)
    Open = models.FloatField(null=True)
    High = models.FloatField(null=True)
    Low = models.FloatField(null=True)
    Close = models.FloatField(null=True)
    Volume = models.IntegerField(null=True)
    unix_time = models.IntegerField(null=True)
    length = models.IntegerField(null=True)
    date_time = models.CharField(max_length=50, null=True)

    def save(self, *args, **kwargs):
        self.date_time = datetime.fromtimestamp(self.unix_time, tz=tz).strftime("%d-%m-%Y %H:%M")
        return super(CandleThirty, self).save(*args, *kwargs)

    class Meta:
        db_table = "candle_thirty"


class CandleSixty(models.Model):
    Tick = models.IntegerField(null=False)
    Symbol = models.CharField(max_length=100, null=True)
    Open = models.FloatField(null=True)
    High = models.FloatField(null=True)
    Low = models.FloatField(null=True)
    Close = models.FloatField(null=True)
    Volume = models.IntegerField(null=True)
    unix_time = models.IntegerField(null=True)
    length = models.IntegerField(null=True)
    date_time = models.CharField(max_length=50, null=True)

    def save(self, *args, **kwargs):
        self.date_time = datetime.fromtimestamp(self.unix_time, tz=tz).strftime("%d-%m-%Y %H:%M")
        return super(CandleSixty, self).save(*args, *kwargs)

    class Meta:
        db_table = "candle_sixty"


class DailySubscribe(models.Model):
    unix_time = models.IntegerField()
    subscribe = models.BooleanField(default=False)
    unsubscribe = models.BooleanField(default=False)

    class Meta:
        db_table = "daily_subscribe"


class SchedularTable(models.Model):
    function_name = models.CharField(max_length=500)
    readable_function = models.TextField(null=True)
    serialized_function = models.BinaryField(null=True)
    last_run = models.IntegerField(null=True)
    next_run = models.IntegerField(null=True)
    is_enabled = models.BooleanField(null=True)
    run_counts = models.IntegerField(null=True)
    successful = models.IntegerField(null=True)
    failed = models.IntegerField(null=True)

    class Meta:
        db_table = "schedular_table"
