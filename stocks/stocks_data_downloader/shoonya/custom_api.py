from .api_helper import ShoonyaApiPy
from datetime import datetime, timedelta
import pyotp
from stocks_data_downloader.models import WebSocketData
import pytz
from decouple import config
import logging

tz = pytz.timezone("Asia/Kolkata")
logger = logging.getLogger(__name__)


def insert_into_database(model, data):
    if ("tk" in data.keys()) and ("ft" in data.keys()):
        old = model.objects.filter(tick=data.get("tk"), unix_time=data.get("ft")).last()
        if old:
            if data.get("lp"):
                old.ltp = float(data["lp"])
            if data.get("v"):
                old.volume = int(data["v"])
            old.save()
            return old
        new = model(tick_id=int(data.get("tk")), unix_time=int(data.get("ft")))
        if data.get("lp"):
            new.ltp = float(data["lp"])
        if data.get("v"):
            new.volume = int(data["v"])
        new.save()
        return new


class ShoonyaAPI:

    def __init__(self):
        self.api = ShoonyaApiPy()
        self.is_loggedin = False
        self.is_feed_opened = False

    def login(self, yaml_file=None):
        ret = self.api.login(userid=config('SHOONYA_USER'), password=config('SHOONYA_PWD'),
                             twoFA=pyotp.TOTP(config('SHOONYA_TOKEN')).now(), vendor_code=config('SHOONYA_VC'),
                             api_secret=config('SHOONYA_APIKEY'), imei=config('SHOONYA_IMEI'))
        if ret:
            logger.info("login successful to shoonya api..")
            self.is_loggedin = True
            return self.api
        logger.error("Login failed to shoonya api, please check your credentials..")
        self.is_loggedin = False
        return self.api

    def logout(self):
        self.api.logout()
        logger.info("Logged out from shoonya api..")
        self.is_loggedin = False
        return True

    def get_token(self, symbol, exchange="NSE", multiple=False):
        if not self.is_loggedin:
            logger.error("Unable to get token. Please login first")
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
            insert_into_database(WebSocketData, tick_data)
        except Exception:
            logger.exception("Exception while updating websocket data on_update method..")

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
            logger.info("websocket connection is opened to shoonya api, subscribe to events..")
            self.is_feed_opened = True
            return True
        return False

    def close_websocket(self):
        if self.is_loggedin:
            self.api.close_websocket()
            self.is_feed_opened = False
            logger.info("Closing the websocket connection to shoonya api")
            return True
        logger.info("Seems user is not logged in..")
        return False

    def subscribe_wsticks(self, tick, exchange="NSE"):
        if self.is_feed_opened:
            self.api.subscribe(f"{exchange}|{tick}")
            logger.info(f'Subscribed to {f"{exchange}|{tick}"}')
            return True
        logger.error("websocket not running to shoonya api, start the websocket first by calling "
                     "start_websocket() method..")
        return False

    def unsubscribe_wsticks(self, ticks, exchange="NSE"):
        if not isinstance(ticks, list):
            ticks = [ticks]

        if self.is_feed_opened:
            feds = [f"{exchange}|{t}" for t in ticks]
            self.api.unsubscribe(feds)
            logger.info(f"unsubscribed {ticks} ticks to shoonya api")
            return True
        return False
