from threading import Thread
from .make_candles import draw_candle
from .db_migrations import migrate_tables


class CustomThread:
    one_minutes_candle = Thread(target=draw_candle, args=(1,), daemon=True, name="One Minutes Candle Thread")
    five_minutes_candle = Thread(target=draw_candle, args=(5,), daemon=True, name="Five Minutes Candle Thread")
    fifteen_minutes_candle = Thread(target=draw_candle, args=(15,), daemon=True, name="Fifteen Minutes Candle Thread")
    thirty_minutes_candle = Thread(target=draw_candle, args=(30,), daemon=True, name="Thirty Minutes Candle Thread")
    sixty_minutes_candle = Thread(target=draw_candle, args=(60,), daemon=True, name="Sixty Minutes Candle Thread")
    migrate_tables_to_mongo = Thread(target=migrate_tables, args=(50,), daemon=True, name="Migrating data to mongo")


LIST_OF_THREADS = [v for k, v in CustomThread.__dict__.items() if not k.startswith("_")]

# ToDo Implement re-run threads
# pass threading.Event() as an argument to each function and check is_set() attribute is True, default is False,
# if True stop the thread. you can use .set() to make it True.
# You can create dict to store thread id and flag & this dict can be used to check the flag
