import pandas as pd

from stocks_data_downloader.models import (CandleOne, CandleFive, CandleFifteen, CandleThirty, CandleSixty)


CANDLE_TIMEFRAMES = {1: CandleOne, 5: CandleFive, 15: CandleFifteen, 30: CandleThirty, 60: CandleSixty}
VALID_TIMEFRAMES = (1, 5, 15, 30, 60)
COLUMN_NAMES = ["unix_time", "Open", "High", "Low", "Close", "Volume"]


def get_data(tick, interval=5, limit=40, ordering="asc", ordering_column="unix_time"):
    if interval not in VALID_TIMEFRAMES:
        raise AssertionError("Not a valid timeframe")
    if ordering == "desc":
        ordering_column = "-"+ordering_column
    data = CANDLE_TIMEFRAMES[interval].objects.filter(tick=tick).order_by(ordering_column)[:limit]\
        .values_list(*COLUMN_NAMES)
    df = pd.DataFrame(list(data.values()), columns=COLUMN_NAMES)
    return df
