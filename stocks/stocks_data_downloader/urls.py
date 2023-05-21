from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("search-symbol/", views.search_token, name="search_symbol"),
    path("subscribe-token/", views.subscribe_token, name="subscribe_token"),
    path("unsubscribe-token/", views.unsubscribe_token, name="unsubscribe_token"),
    path("live-data/", views.live_data, name="live-data"),
    path("download-db/", views.download_db, name="download-db"),
    path("api-login/", views.shoonya_login, name="api-login"),
    path("live-candles/", views.show_candles, name="live-candles"),
]