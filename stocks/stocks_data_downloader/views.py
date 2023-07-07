from datetime import datetime
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseNotFound, FileResponse
from stocks_data_downloader.models import SubscribedData, WebSocketData, StockWatcher, WatcherHistory
from utils.decorators import allowed_methods
from utils.threadings import LIST_OF_THREADS, run_thread
from utils.shoonya_api import sapi
from utils.initial_run_functions import register_all_functions_to_schedular, auto_subscribe_on_run
from utils.misc import subscribe_all_tokens, load_data
from utils.scheduler_functions import CANDLE_TIMEFRAMES
from django.conf import settings
import logging
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.template.defaulttags import register


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

CANDLE_TIMEFRAMES_TEXT = {1: "candle_one", 5: "candle_five", 15: "candle_fifteen", 30: "candle_thirty", 60: "candle_sixty"}
logger = logging.getLogger(__name__)

running_threads = LIST_OF_THREADS
# run threads
if settings.RUN_THREADS:
    # Register all functions to schedular on initial run
    register_all_functions_to_schedular()
    auto_subscribe_on_run()

    logger.info("Running threads in background..")
    running_threads = [run_thread(t) for t in LIST_OF_THREADS if not t.is_alive()]

shoonya_api = sapi.login()
load_data()
logger.info(f"Login status {sapi.is_loggedin}")


@allowed_methods(["GET"])
@login_required
def index(request):
    data = SubscribedData.objects.filter(is_active=True)
    logger.info(f"Subscribed tokens are {len(data)} | {request.path}")
    return render(request, "home.html", context={"subscribed_data": data})


@allowed_methods(["GET"])
@login_required
def search_token(request):
    symbol = request.GET.get("symbol")
    stock_type = request.GET.get("type", "NSE")
    print(stock_type)
    if not symbol:
        logger.info("symbol parameter missing..")
        return JsonResponse({"message": "symbol parameter missing.."})
    subscribed_data = SubscribedData.objects.filter(is_active=True)
    try:
        data = sapi.get_token(symbol=symbol, multiple=True, exchange=stock_type)[:10]
        data = {"status": True, "data": data}
        logger.info(f"Found {len(data)} tokens for {symbol} symbol")
    except TypeError:
        data = {"status": False, "data": []}
        logger.info(f"No search token data for {symbol}")
    return render(request, "home.html", context={"symbol_data": data, "subscribed_data": subscribed_data})


@allowed_methods(["GET"])
@login_required
def subscribe_token(request):
    token = request.GET.get("token")
    stock_type = request.GET.get("type", "NSE")
    print(stock_type, token)
    if not token:
        return redirect("/")
    if token == "all":
        subscribe_all_tokens()
        return redirect("/")
    if sapi.is_feed_opened:
        subscribe = sapi.subscribe_wsticks(token, exchange=stock_type)
    else:
        subscribe = True
        logger.info("Websocket feed is not open.. Skipping single subscribe token..")
    if not subscribe:
        logger.error(f"Error while subscribing token {token}. Please try again..")
        return JsonResponse({"message": f"Error while subscribing token {token}. Please try again.."})
    data = sapi.get_token_info(token)
    if not data:
        logger.error(f"Unable to get the tick data for token {token}. Please try again")
        return JsonResponse({"message": "Unable to get the tick data. Please try again"})
    old_data = SubscribedData.objects.filter(token=token).last()
    if not old_data:
        logger.info(f"Subscribing new token {token} {data.get('tsym')}")
        subscribed_data = SubscribedData(token=token, exchange=data.get("exch"), symbol=data.get("tsym"),
                                         cname=data.get("cname"), is_active=True)
        subscribed_data.save()
        logger.info(f"Subscribed new token {token} {data.get('tsym')}")
    else:
        logger.info(f"Subscribing existing token {token} again..")
        old_data.is_active = True
        old_data.save()
        logger.info(f"Subscribed existing token {token} again..")
    return redirect("/")


@allowed_methods(["GET"])
@login_required
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
@login_required
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
    return render(request, "live_data.html", context={"latest_data": data}, )


@allowed_methods(["GET"])
@login_required
def download_db(request):
    download = request.GET.get("download", default="db")
    file_location = settings.BASE_DIR / 'db.sqlite3'
    if download == "logs":
        file_location = settings.LOGFILE_PATH
    try:
        response = FileResponse(open(file_location, 'rb'), as_attachment=True)
    except IOError:
        response = HttpResponseNotFound('<h1>File not exist</h1>')
    return response


@allowed_methods(["GET"])
@login_required
def shoonya_login(request):
    try:
        sapi.logout()
    except AttributeError:
        pass
    sapi.login()
    # sapi.open_websocket()
    logger.info("Loggedin to api from endpoint /api-login")
    return render(request, "api_login.html", context={"message": "Logged in to shoonya api"})


@allowed_methods(["GET"])
@login_required
def show_candles(request):
    """
    API to fetch candle data,
    parameters:
    timeframe: (1,5,15,30,60). default 1
    limit: default 50 records
    # ordering: default descending
    from: unix_time to filter data, default last 50 records
    to: unix_time to filter data
    tick: token to filter specific stock
    """
    filters = {}
    valid_timeframes = ("1", "5", "15", "30", "60")
    limit = 200
    timeframe = 1
    tick = request.GET.get("tick")
    time_interval = request.GET.get("timeframe")
    rows = request.GET.get("limit")
    if rows:
        limit = int(rows)
    if time_interval:
        if time_interval not in valid_timeframes:
            return JsonResponse({"message": False, "results": []})
        timeframe = int(time_interval)
    if tick:
        filters["tick"] = int(tick)
    if request.GET.get("from"):
        filters["unix_time__gte"] = request.GET.get("from")
    if request.GET.get("to"):
        filters["unix_time__lt"] = request.GET.get("to")

    data = CANDLE_TIMEFRAMES[timeframe].objects.filter(*filters).order_by("-unix_time")[:limit]
    return render(request, "candles.html", context={"latest_data": data})


@allowed_methods(["GET"])
@login_required
def clear_logs(request):
    confirm = request.GET.get("confirm", default="no")
    if confirm.lower() == "yes":
        open(settings.LOGFILE_PATH, 'w').close()
        return render(request, "api_login.html", context={"message": "Log file cleared.."})
    return redirect("/")


@allowed_methods(["GET", "POST"])
def stocks_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request=request, user=user)
            return redirect("/")
        else:
            return render(request, "registration/login.html", context={"message": "Incorrect Credentials.."})
    return render(request, "registration/login.html", context={"message": None})


@allowed_methods(["GET"])
@login_required
def stocks_logout(request):
    logout(request)
    return redirect("/login")


def ping(request):
    return JsonResponse({"status": "ok"})


@allowed_methods(["GET"])
@login_required
def websocket_ops(request):
    ops = request.GET.get("ops")
    if ops == "open":
        sapi.open_websocket()
        logger.info("Websocket is open on request websocket_ops().. ")
        return JsonResponse({"message": "Websocket is open"})
    elif ops == "close":
        sapi.close_websocket()
        logger.info("Websocket is close on request websocket_ops().. ")
        return JsonResponse({"message": "Websocket is closed.."})
    logger.info(f"Either ops param missing or not valid.. {ops}")
    return JsonResponse({"message", "Either ops param missing or not valid.."})


@allowed_methods(["GET", "POST"])
@login_required
def watch_list(request):
    if request.method == "POST":
        token = request.POST.get("token")
        price_low = request.POST.get("price_low")
        price_high = request.POST.get("price_high")
        if token and price_low and price_high:
            try:
                price_low = float(price_low)
                price_high = float(price_high)
            except ValueError:
                return JsonResponse(data={"message": "Unable to parse low and high price.."})
            old_data = StockWatcher.objects.filter(tick=token, is_active=True).first()
            if old_data:
                old_data.price_low = price_low
                old_data.price_high = price_high
                old_data.save()
            else:
                # token_data = SubscribedData.objects.filter(token=token).first()
                watcher = StockWatcher(tick_id=token, price_low=price_low, price_high=price_high)
                watcher.save()
        return redirect("/watch-list")
    else:
        all_subscribed_stocks = SubscribedData.objects.filter(is_active=True)
        all_watchlist_stocks = StockWatcher.objects.filter(is_active=True)
        data = {"stocks_data": all_subscribed_stocks, "watchlist_data": all_watchlist_stocks}
        return render(request, "watch_list.html", context=data)


@login_required()
def del_watch_list(request):
    pk = request.GET.get("id")
    # ltp = WebSocketData.objects.filter(tick=token).last()
    stock = StockWatcher.objects.get(pk=pk)
    history = WatcherHistory(stock=stock, ltp=stock.tick.data.last().ltp,
                             unix_time=datetime.now(tz=settings.INDIAN_TIMEZONE).timestamp())
    stock.is_active = False
    history.save()
    stock.save()
    return redirect("/watch-list")

from django.db.models import Q
def candles(request):
    ticks = request.GET.get("ticks")
    timeframe = request.GET.get("timeframe")
    order_by = request.GET.get("order_by")
    order_dir = request.GET.get("order_dir", "asc")
    limit = request.GET.get("limit")
    if not (timeframe and limit):
        return JsonResponse(dict(status=False, message="Required parameters missing..."))
    try:
        timeframe, limit = int(timeframe), int(limit)
        if timeframe not in (1, 5, 15, 30, 60):
            raise ValueError
    except ValueError:
        return JsonResponse(dict(status=False, message="Not a valid input.."))
    token_filters = {"is_active": True}
    if ticks:
        token_filters["token__in"] = ticks.split(",")
    ticks_objs = SubscribedData.objects.filter(*[Q(**{key: value}) for key, value in token_filters.items()])

    data = {}
    for tick in ticks_objs:
        queryset = getattr(tick, CANDLE_TIMEFRAMES_TEXT[timeframe]).filter( length__gt=20).order_by("-id")[:limit]
        if order_by:
            if order_dir == "desc":
                order_by = "-" + order_by
            queryset = getattr(queryset, "order_by")(order_by)
        data[tick.token] = list(queryset.values())[::-1]

    return JsonResponse(dict(status=True, data=data))
