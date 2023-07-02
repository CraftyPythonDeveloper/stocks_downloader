import pandas_ta as ta
import pandas as pd
from custom_strategies.utils import get_data
from utils.misc import send_telegram_msg
import logging
from stocks_data_downloader.models import SubscribedData

logger = logging.getLogger(__name__)


def macd_strategy(**kwargs):
    # read latest data
    # tick = kwargs.pop("tick")
    timeframe = kwargs.pop("interval", 1)
    subscribed_stocks = SubscribedData.objects.filter(is_active=True)
    for stock in subscribed_stocks:
        df = get_data(tick=stock.token, interval=timeframe)
        macd = ta.macd(df.Close)
        # df = pd.concat([df, macd], axis=1).reindex(df.index)
        df = df.assign(MACD_12_26_9=ta.macd(df.Close)['MACD_12_26_9'], MACDs_12_26_9=ta.macd(df.Close)['MACDs_12_26_9'])
        if df.shape[0] < 35:
            logger.error(f"Not enough data for macd_strategy to run.. Required minimum 35 rows, available {df.shape[0]}")
            continue
            # return 0
        if df['MACD_12_26_9'].iloc[-1] > df['MACDs_12_26_9'].iloc[-1] and \
                df['MACD_12_26_9'].iloc[-2] < df['MACDs_12_26_9'].iloc[-2]:
            msg = f"Buy signal from MACD on timeframe of {timeframe}. \n Tick: {stock.tick} \n Stock Name: " \
                  f"{stock.symbol} Buy Price ==> {df.Close.iloc[-1]}"
            logger.info(msg)
            result = send_telegram_msg(msg)
            if not result:
                logger.error(f"unable to send buy macd_signal to telegram group.. {msg}")
            # return 1
            continue
        elif df['MACD_12_26_9'].iloc[-1] < df['MACDs_12_26_9'].iloc[-1] and \
                df['MACD_12_26_9'].iloc[-2] > df['MACDs_12_26_9'].iloc[-2]:
            msg = f"Sell signal from MACD on timeframe of {timeframe}. \n Tick: {stock.tick} \n Stock Name: " \
                  f"{stock.symbol} Buy Price ==> {df.Close.iloc[-1]}"
            logger.info(msg)
            result = send_telegram_msg(msg)
            if not result:
                logger.error(f"unable to send sel macd_signal to telegram group.. {msg}")
            # return -1
            continue
        else:
            logger.info(f"No signal from MACD for {stock.symbol}")
            # return 0
            continue
