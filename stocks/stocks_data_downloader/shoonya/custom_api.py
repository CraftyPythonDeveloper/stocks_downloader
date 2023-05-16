import pytz
from .api_helper import ShoonyaApiPy
import time
from datetime import datetime, timedelta
import pandas as pd
import pyotp
import pandas_ta as ta
from stocks_data_downloader.models import WebSocketData
import pytz
from decouple import config
import logging

tz = pytz.timezone("Asia/Kolkata")
logger = logging.getLogger(__name__)


def generate_candle(data):
    return {"open": data["price"][0], "close": data["price"][-1], "high": max(data["price"]), "low": min(data["price"]),
            "time": data["time"][-1], "tick": data["tick"], "length": len(data["time"])}


class ShoonyaAPI:

    def __init__(self):
        self.api = ShoonyaApiPy()
        self.is_loggedin = False
        self.is_feed_opened = False
        self.stock_data_dict = {}

    def login(self, yaml_file=None):
        ret = self.api.login(userid=config('SHOONYA_USER'), password=config('SHOONYA_PWD'),
                             twoFA=pyotp.TOTP(config('SHOONYA_TOKEN')).now(), vendor_code=config('SHOONYA_VC'),
                             api_secret=config('SHOONYA_APIKEY'), imei=config('SHOONYA_IMEI'))
        if ret:
            logger.info("login successful..")
            self.is_loggedin = True
            return self.api
        logger.info("Login failed, please check your credentials..")
        self.is_loggedin = False
        return self.api

    def logout(self):
        self.api.logout()
        self.is_loggedin = False
        return True

    def get_token(self, symbol, exchange="NSE", multiple=False):
        if not self.is_loggedin:
            logger.error("Not Logged in")
            return False
        data = self.api.searchscrip(exchange=exchange, searchtext=symbol)
        if multiple:
            return data["values"]
        return data["values"][0]

    def get_token_info(self, token, exchange="NSE"):
        data = self.api.get_security_info(exchange=exchange, token=token)
        return data

    @staticmethod
    def is_candle_ended(start_time, candle_length):
        current_time = datetime.now().replace(second=0, microsecond=0)
        return current_time >= start_time + timedelta(minutes=candle_length)

    @staticmethod
    def convert_dtype(data_dict):
        data_dict["lp"] = float(data_dict["lp"])
        data_dict["ft"] = int(data_dict["ft"])
        return data_dict

    @staticmethod
    def on_update(tick_data):
        try:
            if tick_data.get("ft") and tick_data.get("lp"):
                dt = datetime.fromtimestamp(tick_data.get("ft"), tz=tz)
                data = WebSocketData(tick=tick_data.get("tk"), unix_time=int(tick_data.get("ft")),
                                     ltp=float(tick_data.get("lp")), date_time=dt)
                data.save(using="sqlite_db")
        except Exception as e:
            print(e)
        # if tick_data.get("ft") and tick_data.get("v"):
        #     obj, created = WebSocketData.objects.update_or_create(tick=int(tick_data["tk"]), unix_time=int(tick_data["ft"]),
        #                                            defaults={"volume": tick_data["v"]})
        #     print(created, obj)

    def event_handler_feed_update1(self, tick_data):
        print(f"feed update {tick_data}")

    @staticmethod
    def event_handler_order_update(tick_data):
        pass

    def open_callback(self):
        self.is_feed_opened = True

    def open_websocket(self):
        if self.is_loggedin:
            self.api.start_websocket(order_update_callback=self.event_handler_order_update,
                                     subscribe_callback=self.on_update,
                                     socket_open_callback=self.open_callback)
            print("websocket is opened, subscribe to events..")
            self.is_feed_opened = True
            return True
        return False

    def close_websocket(self):
        if self.is_loggedin:
            self.api.close_websocket()

    def subscribe_wsticks(self, tick, exchange="NSE"):
        if self.is_feed_opened:
            self.api.subscribe(f"{exchange}|{tick}")
            return True
        print("websocket not running, start the websocket first by calling start_websocket() method..")
        return False

    def unsubscribe_wsticks(self, ticks, exchange="NSE"):
        if not isinstance(ticks, list):
            ticks = [ticks]

        if self.is_feed_opened:
            feds = [f"{exchange}|{t}" for t in ticks]
            self.api.unsubscribe(feds)
            print(f"unsubscribed {ticks} ticks")
            return True
        return False
