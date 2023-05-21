from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseNotFound, FileResponse
from .shoonya.custom_api import ShoonyaAPI
from .models import SubscribedData, WebSocketData
from django.conf import settings
from utils.decorators import allowed_methods
from utils.threadings import (one_minutes_candle, five_minutes_candle, fifteen_minutes_candle, thirty_minutes_candle, sixty_minutes_candle)
from utils.make_candles import CANDLE_TIMEFRAMES
from django.conf import settings


# run threads
if settings.RUN_THREADS:
    print("running threads")
    one_minutes_candle.start()
    five_minutes_candle.start()
    fifteen_minutes_candle.start()
    thirty_minutes_candle.start()
    sixty_minutes_candle.start()

sapi = ShoonyaAPI()
shoonya_api = sapi.login()
sapi.open_websocket()
print(f"login status {sapi.is_loggedin}")


@allowed_methods(["GET"])
def index(request):
    data = SubscribedData.objects.filter(is_active=True)
    return render(request, "home.html", context={"subscribed_data": data})


@allowed_methods(["GET"])
def search_token(request):
    symbol = request.GET.get("symbol")
    # print(symbol)
    if not symbol:
        return JsonResponse({"message": "symbol parameter missing.."})
    subscribed_data = SubscribedData.objects.filter(is_active=True)
    try:
        data = sapi.get_token(symbol=symbol, multiple=True)[:10]
        data = {"status": True, "data": data}
    except TypeError:
        data = {"status": False, "data": []}
    return render(request, "home.html", context={"symbol_data": data, "subscribed_data": subscribed_data})


@allowed_methods(["GET"])
def subscribe_token(request):
    token = request.GET.get("token")
    if not token:
        return redirect("/")
    subscribe = sapi.subscribe_wsticks(token)
    if not subscribe:
        return JsonResponse({"message": f"Error while subscribing token {token}. Please try again.."})
    data = sapi.get_token_info(token)
    if not data:
        return JsonResponse({"message": "Unable to get the tick data. Please try again"})
    old_data = SubscribedData.objects.filter(token=token).last()
    if not old_data:
        subscribed_data = SubscribedData(token=token, exchange=data.get("exch"), symbol=data.get("tsym"),
                                         cname=data.get("cname"), is_active=True)
        subscribed_data.save()
    else:
        old_data.is_active = True
        old_data.save()
    return redirect("/")


@allowed_methods(["GET"])
def unsubscribe_token(request):
    token = request.GET.get("token")
    if not token:
        return JsonResponse({"message": "token parameter not passed.."})
    token_data = SubscribedData.objects.filter(token=token).last()
    token_data.is_active = False
    token_data.save()
    sapi.unsubscribe_wsticks(token)
    return redirect("/")


@allowed_methods(["GET"])
def live_data(request):
    limit = 200
    rows = request.GET.get("rows")
    tick = request.GET.get("tick")
    if rows:
        limit = int(rows)
    if tick:
        data = WebSocketData.objects.filter(tick=tick).order_by("-unix_time")[:limit]
    else:
        data = WebSocketData.objects.all().order_by("-unix_time")[:limit]
    return render(request, "live_data.html", context={"latest_data": data})


@allowed_methods(["GET"])
def download_db(request):
    db_location = settings.BASE_DIR / 'db.sqlite3'
    try:
        response = FileResponse(open(db_location, 'rb'), as_attachment=True)
    except IOError:
        response = HttpResponseNotFound('<h1>File not exist</h1>')
    return response


@allowed_methods(["GET"])
def shoonya_login(request):
    try:
        sapi.logout()
    except AttributeError:
        pass
    sapi.login()
    sapi.open_websocket()
    print("loggedin to api")
    return render(request, "api_login.html", context={"message": "Logged in to shoonya api"})


@allowed_methods(["GET"])
def show_candles(request):
    limit = 200
    timeframe = 1
    tick = request.GET.get("tick")
    time_interval = request.GET.get("timeframe")
    rows = request.GET.get("limit")
    if rows:
        limit = int(rows)
    if time_interval:
        timeframe = int(time_interval)
    if tick:
        tick = int(tick)
        data = CANDLE_TIMEFRAMES[timeframe].objects.filter(Tick=tick).order_by("-unix_time")[:limit]
    else:
        data = CANDLE_TIMEFRAMES[timeframe].objects.all().order_by("-unix_time")[:limit]

    return render(request, "candles.html", context={"latest_data": data})
