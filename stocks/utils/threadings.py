from threading import Thread
from .make_candles import draw_candle
from .db_migrations import migrate_tables

one_minutes_candle = Thread(target=draw_candle, args=(1,), daemon=True, name="One Minutes Candle Thread")
five_minutes_candle = Thread(target=draw_candle, args=(5,), daemon=True, name="Five Minutes Candle Thread")
fifteen_minutes_candle = Thread(target=draw_candle, args=(15,), daemon=True, name="Fifteen Minutes Candle Thread")
thirty_minutes_candle = Thread(target=draw_candle, args=(30,), daemon=True, name="Thirty Minutes Candle Thread")
sixty_minutes_candle = Thread(target=draw_candle, args=(60,), daemon=True, name="Sixty Minutes Candle Thread")
migrate_tables_to_mongo = Thread(target=migrate_tables, args=(50,), daemon=True, name="Migrating data to mongo")
