from django.db import models
from datetime import datetime
from django.conf import settings

tz = settings.INDIAN_TIMEZONE


class SubscribedData(models.Model):
    token = models.IntegerField(null=False, unique=True)
    exchange = models.CharField(max_length=100, null=True, blank=True)
    symbol = models.CharField(max_length=100, null=False)
    cname = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=False)
    # data = related websocket data
    # candle_one = get candle one related data
    # candle_five = get candle five related data
    # candle_fifteen = get candle fifteen related data
    # candle_thirty = get candle thirty related data
    # candle_sixty = get candle sixty related data
    # watcher = get watch list
    # active_strategies = get active strategies

    class Meta:
        db_table = "subscribed_data"


class WebSocketData(models.Model):
    tick = models.ForeignKey(SubscribedData, on_delete=models.DO_NOTHING, to_field="token", db_column="tick",
                             related_name="data")
    unix_time = models.IntegerField(null=False)
    ltp = models.FloatField(null=True, blank=True)
    volume = models.IntegerField(null=True, blank=True)
    date_time = models.CharField(max_length=50, null=True, blank=True)

    def save(self, *args, **kwargs):
        self.date_time = datetime.fromtimestamp(self.unix_time, tz=tz).strftime("%d-%m-%Y %H:%M:%S")
        return super(WebSocketData, self).save(*args, *kwargs)

    class Meta:
        db_table = "websocket_data"


class CandleOne(models.Model):
    tick = models.ForeignKey(SubscribedData, on_delete=models.DO_NOTHING, to_field="token", db_column="tick",
                             related_name="candle_one")
    Open = models.FloatField(null=True, blank=True)
    High = models.FloatField(null=True, blank=True)
    Low = models.FloatField(null=True, blank=True)
    Close = models.FloatField(null=True, blank=True)
    Volume = models.IntegerField(null=True, blank=True)
    unix_time = models.IntegerField(null=True, blank=True)
    length = models.IntegerField(null=True, blank=True)
    date_time = models.CharField(max_length=50, null=True, blank=True)

    def save(self, *args, **kwargs):
        self.date_time = datetime.fromtimestamp(self.unix_time, tz=tz).strftime("%d-%m-%Y %H:%M")
        return super(CandleOne, self).save(*args, *kwargs)

    class Meta:
        db_table = "candle_one"


class CandleFive(models.Model):
    tick = models.ForeignKey(SubscribedData, on_delete=models.DO_NOTHING, to_field="token", db_column="tick",
                             related_name="candle_five")
    Open = models.FloatField(null=True, blank=True)
    High = models.FloatField(null=True, blank=True)
    Low = models.FloatField(null=True, blank=True)
    Close = models.FloatField(null=True, blank=True)
    Volume = models.IntegerField(null=True, blank=True)
    unix_time = models.IntegerField(null=True, blank=True)
    length = models.IntegerField(null=True, blank=True)
    date_time = models.CharField(max_length=50, null=True, blank=True)

    def save(self, *args, **kwargs):
        self.date_time = datetime.fromtimestamp(self.unix_time, tz=tz).strftime("%d-%m-%Y %H:%M")
        return super(CandleFive, self).save(*args, *kwargs)

    class Meta:
        db_table = "candle_five"


class CandleFifteen(models.Model):
    tick = models.ForeignKey(SubscribedData, on_delete=models.DO_NOTHING, to_field="token", db_column="tick",
                             related_name="candle_fifteen")
    Open = models.FloatField(null=True, blank=True)
    High = models.FloatField(null=True, blank=True)
    Low = models.FloatField(null=True, blank=True)
    Close = models.FloatField(null=True, blank=True)
    Volume = models.IntegerField(null=True, blank=True)
    unix_time = models.IntegerField(null=True, blank=True)
    length = models.IntegerField(null=True, blank=True)
    date_time = models.CharField(max_length=50, null=True, blank=True)

    def save(self, *args, **kwargs):
        self.date_time = datetime.fromtimestamp(self.unix_time, tz=tz).strftime("%d-%m-%Y %H:%M")
        return super(CandleFifteen, self).save(*args, *kwargs)

    class Meta:
        db_table = "candle_fifteen"


class CandleThirty(models.Model):
    tick = models.ForeignKey(SubscribedData, on_delete=models.DO_NOTHING, to_field="token", db_column="tick",
                             related_name="candle_thirty")
    Open = models.FloatField(null=True, blank=True)
    High = models.FloatField(null=True, blank=True)
    Low = models.FloatField(null=True, blank=True)
    Close = models.FloatField(null=True, blank=True)
    Volume = models.IntegerField(null=True, blank=True)
    unix_time = models.IntegerField(null=True, blank=True)
    length = models.IntegerField(null=True, blank=True)
    date_time = models.CharField(max_length=50, null=True, blank=True)

    def save(self, *args, **kwargs):
        self.date_time = datetime.fromtimestamp(self.unix_time, tz=tz).strftime("%d-%m-%Y %H:%M")
        return super(CandleThirty, self).save(*args, *kwargs)

    class Meta:
        db_table = "candle_thirty"


class CandleSixty(models.Model):
    tick = models.ForeignKey(SubscribedData, on_delete=models.DO_NOTHING, to_field="token", db_column="tick",
                             related_name="candle_sixty")
    Open = models.FloatField(null=True, blank=True)
    High = models.FloatField(null=True, blank=True)
    Low = models.FloatField(null=True, blank=True)
    Close = models.FloatField(null=True, blank=True)
    Volume = models.IntegerField(null=True, blank=True)
    unix_time = models.IntegerField(null=True, blank=True)
    length = models.IntegerField(null=True, blank=True)
    date_time = models.CharField(max_length=50, null=True, blank=True)

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
    readable_function = models.TextField(null=True, blank=True)
    serialized_function = models.BinaryField(null=True, blank=True)
    interval = models.CharField(max_length=10, null=True, blank=True)
    last_run = models.IntegerField(null=True, blank=True)
    next_run = models.IntegerField(null=True, blank=True)
    is_enabled = models.BooleanField(default=True)
    status = models.CharField(max_length=50, default="scheduled")  # (scheduled, running, stopped)
    last_status = models.CharField(max_length=50, null=True, blank=True)
    run_counts = models.IntegerField(default=0)
    successful = models.IntegerField(default=0)
    failed = models.IntegerField(default=0)
    last_run_datetime = models.CharField(max_length=50, null=True, blank=True)
    next_run_datetime = models.CharField(max_length=50, null=True, blank=True)
    function_hash = models.CharField(max_length=250, null=True, blank=True)

    def save(self, *args, **kwargs):
        self.next_run_datetime = datetime.fromtimestamp(self.next_run, tz=tz).strftime("%d-%m-%Y %H:%M:%S")
        self.last_run_datetime = datetime.fromtimestamp(self.last_run, tz=tz).strftime("%d-%m-%Y %H:%M:%S")
        return super(SchedularTable, self).save(*args, *kwargs)

    class Meta:
        db_table = "schedular_table"


class SchedularHistory(models.Model):
    run_at = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=50, null=True, blank=True)
    exception = models.TextField(null=True, blank=True)
    scheduler_details = models.ForeignKey(SchedularTable, on_delete=models.DO_NOTHING, null=True, blank=True,
                                          related_name='history')

    class Meta:
        db_table = "schedular_history"


class StockWatcher(models.Model):
    tick = models.ForeignKey(SubscribedData, on_delete=models.DO_NOTHING, to_field="token", db_column="tick",
                             related_name="watcher")
    price_low = models.FloatField(default=0)
    price_high = models.FloatField()
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "stock_watcher"


class WatcherHistory(models.Model):
    stock = models.ForeignKey(StockWatcher, on_delete=models.DO_NOTHING, related_name="history", db_column="stock")
    ltp = models.FloatField()
    unix_time = models.IntegerField()
    date_time = models.CharField(max_length=50, null=True, blank=True)

    def save(self, *args, **kwargs):
        self.date_time = datetime.fromtimestamp(self.unix_time, tz=tz).strftime("%d-%m-%Y %H:%M:%S")
        return super(WatcherHistory, self).save(*args, **kwargs)

    class Meta:
        db_table = "watcher_history"


class Strategies(models.Model):
    name = models.CharField(max_length=200, unique=True, null=False)

    class Meta:
        db_table = "strategies"


class SymbolStrategy(models.Model):
    tick = models.ForeignKey(SubscribedData, on_delete=models.DO_NOTHING, to_field="token", db_column="tick",
                             related_name="active_strategies")
    strategy = models.ForeignKey(Strategies, on_delete=models.DO_NOTHING, related_name="active_symbols")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "symbol_strategy"
