from datetime import datetime, timedelta
from stocks_data_downloader.models import WebSocketData, SubscribedData, CandleOne, CandleFive, CandleFifteen, CandleThirty, CandleSixty
import time
import pytz

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
    print("not a working hr")
    return False


def get_ohlvc(queryset, meta):
    candle = {"Tick": meta.token, "Symbol": meta.symbol, "Open": None, "High": None, "Low":  None,
              "Close": None, "Volume": 0, "unix_time": None, "length": None}
    temp_volume = 0
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
        candle["unix_time"] = record.unix_time
    candle["length"] = len(candle["unix_time"])

    # candle = {"Tick": meta.token, "Symbol": meta.symbol, "Open": first_record, "High": None, "Low":  None,
    #           "Close": last_record, "Volume": None, "unix_time": queryset[len(queryset)].unix_time}
    # candle.update(queryset.aggregate(High=Max('ltp'), Low=Min('ltp'), Volume=Sum('volume')))
    return candle



def draw_candle(timeframe):
    if timeframe not in CANDLE_TIMEFRAMES.keys():
        return "Not a valid timeframe.. use (1, 5, 15, 30 ,60)"
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
            print(f"getting data form {start} to {end}")
            try:
                active_ticks = SubscribedData.objects.filter(is_active=True).all()
                for tick in active_ticks:
                    queryset = WebSocketData.objects.filter(tick=tick.token, unix_time__gt=start,
                                                            unix_time__lte=end).order_by("unix_time")
                    if queryset:
                        candle = get_ohlvc(queryset=queryset, meta=tick)
                        CANDLE_TIMEFRAMES[timeframe].objects.create(**candle)
                        print("done inserting data..")
                    else:
                        a = datetime.fromtimestamp(start, tz=tz).strftime("%d-%m-%Y %H:%M:%S")
                        b = datetime.fromtimestamp(end, tz=tz).strftime('%d-%m-%Y %H:%M:%S')
                        print(f"No data for tick {tick.token} timeframe {timeframe} from {a} to {b}")
            except Exception as e:
                print(f"Exception occurred while generating {timeframe} minutes candle..", str(e))
            continue
        time.sleep(1)

