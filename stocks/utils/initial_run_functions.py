from utils.misc import register_function, is_working_hr, subscribe_all_tokens
from utils.shoonya_api import shoonya_refresh
from utils.scheduler_functions import (draw_candle_v2, self_ping, subscribe_unsubscribe_market, upload_logs,
                                              migrate_table, purge_old_data)

functions = {draw_candle_v2: ["1m", "5m", "15m", "30m", "60m"], self_ping: "1m", subscribe_unsubscribe_market: "1m",
             upload_logs: "3h", migrate_table: "50s", purge_old_data: "1d"}


def register_all_functions_to_schedular():
    # Register functions to schedular is not exists
    for func, intervals in functions.items():
        if isinstance(intervals, str):
            intervals = [intervals]
        for interval in intervals:
            register_function(func, interval)


def auto_subscribe_on_run():
    if is_working_hr():
        shoonya_refresh("logout")
        shoonya_refresh("login")
        subscribe_all_tokens()
