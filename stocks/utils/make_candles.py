from datetime import datetime, timedelta
from stocks_data_downloader.models import WebSocketData, SubscribedData, CandleOne, CandleFive, CandleFifteen, \
    CandleThirty, CandleSixty
import time
import pytz
import logging

logger = logging.getLogger(__name__)

tz = pytz.timezone("Asia/Kolkata")

CANDLE_TIMEFRAMES = {1: CandleOne, 5: CandleFive, 15: CandleFifteen, 30: CandleThirty, 60: CandleSixty}


def is_candle_ended(start_time, candle_length):
    current_time = datetime.now().replace(second=0, microsecond=0)
    # print(current_time, start_time + timedelta(minutes=candle_length))
    return current_time >= start_time + timedelta(minutes=candle_length)


def is_working_hr():
    time_now = datetime.now()
    market_start_time = time_now.replace(hour=9, minute=14, second=0, microsecond=0)
    market_end_time = time_now.replace(hour=15, minute=31, second=0, microsecond=0)
    if time_now.weekday() < 5:
        return market_start_time <= time_now <= market_end_time
    return False


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
            logger.info(f"Getting data form {start} to {end} for {timeframe} timeframe to make candle.")
            try:
                active_ticks = SubscribedData.objects.filter(is_active=True).all()
                time_from = datetime.fromtimestamp(start, tz=tz).strftime("%d-%m-%Y %H:%M:%S")
                time_to = datetime.fromtimestamp(end, tz=tz).strftime('%d-%m-%Y %H:%M:%S')
                for tick in active_ticks:
                    queryset = WebSocketData.objects.filter(tick=tick.token, unix_time__gte=start,
                                                            unix_time__lt=end).order_by("unix_time")
                    if queryset:
                        candle = get_ohlvc(queryset=queryset, meta=tick, close_at=end)
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
