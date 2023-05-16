from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("fake-api/", views.fake_api, name="fake_api"),
    path("search-symbol/", views.search_token, name="search_symbol"),
    path("subscribe-token/", views.subscribe_token, name="subscribe_token"),
    path("unsubscribe-token/", views.unsubscribe_token, name="unsubscribe_token"),
    path("live-data/", views.live_data, name="live-data"),
    path("download-db/", views.download_db, name="download-db"),
]