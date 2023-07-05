from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="home"),
    path("search-symbol/", views.search_token, name="search-symbol"),
    path("subscribe-token/", views.subscribe_token, name="subscribe-token"),
    path("unsubscribe-token/", views.unsubscribe_token, name="unsubscribe-token"),
    path("live-data/", views.live_data, name="live-data"),
    path("download-db/", views.download_db, name="download-db"),
    path("api-login/", views.shoonya_login, name="api-login"),
    path("live-candles/", views.show_candles, name="live-candles"),
    path("clear-logs/", views.clear_logs, name="clear-logs"),
    path("login/", views.stocks_login, name="login"),
    path("logout/", views.stocks_logout, name="logout"),
    path("ping/", views.ping, name="ping"),
    path("websocket-ops/", views.websocket_ops, name="websocket-ops"),
    path("watch-list/", views.watch_list, name="watch-list"),
    path("watch-list/delete", views.del_watch_list, name="watch-list-delete"),
    path("candles/", views.candles, name="candles"),
]