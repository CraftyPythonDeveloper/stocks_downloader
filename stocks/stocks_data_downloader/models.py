from django.db import models
from datetime import datetime
from django.conf import settings

tz = settings.INDIAN_TIMEZONE


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
    interval = models.CharField(max_length=10, null=True)
    last_run = models.IntegerField(null=True)
    next_run = models.IntegerField(null=True)
    is_enabled = models.BooleanField(default=True)
    status = models.CharField(max_length=50, default="scheduled")  # (scheduled, running, stopped)
    last_status = models.CharField(max_length=50, null=True)
    run_counts = models.IntegerField(default=0)
    successful = models.IntegerField(default=0)
    failed = models.IntegerField(default=0)
    last_run_datetime = models.CharField(max_length=50, null=True)
    next_run_datetime = models.CharField(max_length=50, null=True)
    function_hash = models.CharField(max_length=250, null=True)

    def save(self, *args, **kwargs):
        self.next_run_datetime = datetime.fromtimestamp(self.next_run, tz=tz).strftime("%d-%m-%Y %H:%M:%S")
        self.last_run_datetime = datetime.fromtimestamp(self.last_run, tz=tz).strftime("%d-%m-%Y %H:%M:%S")
        return super(SchedularTable, self).save(*args, *kwargs)

    class Meta:
        db_table = "schedular_table"


class SchedularHistory(models.Model):
    run_at = models.IntegerField(null=True)
    status = models.CharField(max_length=50, null=True)
    exception = models.TextField(null=True)
    scheduler_details = models.ForeignKey(SchedularTable, on_delete=models.DO_NOTHING, null=True, blank=True,
                                          related_name='history')

    class Meta:
        db_table = "schedular_history"


class StockWatcher(models.Model):
    symbol = models.ForeignKey(SubscribedData, on_delete=models.DO_NOTHING)
    price_low = models.FloatField()
    price_high = models.FloatField()
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "stock_watcher"


class WatcherHistory(models.Model):
    stock = models.ForeignKey(StockWatcher, on_delete=models.DO_NOTHING)
    ltp = models.FloatField()
    unix_time = models.IntegerField()
    date_time = models.CharField(max_length=50, null=True)

    def save(self, *args, **kwargs):
        self.date_time = datetime.fromtimestamp(self.unix_time, tz=tz).strftime("%d-%m-%Y %H:%M:%S")
        return super(WatcherHistory, self).save(*args, **kwargs)

    class Meta:
        db_table = "watcher_history"
