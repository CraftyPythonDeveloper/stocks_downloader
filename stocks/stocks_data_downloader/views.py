from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseNotFound, FileResponse
from .models import SubscribedData, WebSocketData
from utils.decorators import allowed_methods
from utils.threadings import LIST_OF_THREADS
from utils.make_candles import CANDLE_TIMEFRAMES, is_working_hr
from utils.shoonya_api import sapi
from django.conf import settings
import logging
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout

logger = logging.getLogger(__name__)


running_threads = LIST_OF_THREADS
# run threads
if settings.RUN_THREADS:
    logger.info("Running threads in background..")

    def run_thread(thread):
        try:
            thread.start()
            logger.info(f"Started running thread {thread.name} in background..")
            return thread
        except RuntimeError:
            logger.error(f"Thread {thread.name} is already running..")
            return thread
    running_threads = [run_thread(t) for t in LIST_OF_THREADS if not t.is_alive()]


shoonya_api = sapi.login()
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
    if not symbol:
        logger.info("symbol parameter missing..")
        return JsonResponse({"message": "symbol parameter missing.."})
    subscribed_data = SubscribedData.objects.filter(is_active=True)
    try:
        data = sapi.get_token(symbol=symbol, multiple=True)[:10]
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
    if not token:
        return redirect("/")
    if token == "all":
        subscribed_tokens = SubscribedData.objects.filter(is_active=True)
        logger.info(f"Subscribing all {len(subscribed_tokens)} tokens")
        if sapi.is_feed_opened:
            for t in subscribed_tokens:
                sapi.subscribe_wsticks(t.token)
            logger.info(f"Subscribed all {len(subscribed_tokens)} tokens")
        else:
            logger.info("Websocket feed is not open.. Skipping subscribe token..")
        return redirect("/")
    if sapi.is_feed_opened:
        subscribe = sapi.subscribe_wsticks(token)
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
    return render(request, "live_data.html", context={"latest_data": data},)


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


def get_running_threads(request):
    return


@allowed_methods(["GET"])
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
