from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseNotFound, FileResponse
from .shoonya.custom_api import ShoonyaAPI
from .models import SubscribedData, WebSocketData
from django.conf import settings

sapi = ShoonyaAPI()
shoonya_api = sapi.login()
sapi.open_websocket()


# Create your views here.
def index(request):
    data = SubscribedData.objects.all()
    return render(request, "home.html", context={"subscribed_data": data})


def fake_api(request):
    return JsonResponse({"results": ["a", "b", "c", "d"]})


def search_token(request):
    symbol = request.GET.get("symbol")
    # print(symbol)
    if not symbol:
        return JsonResponse({"message": "symbol parameter missing.."})
    subscribed_data = SubscribedData.objects.all()
    try:
        data = sapi.get_token(symbol=symbol, multiple=True)[:10]
        data = {"status": True, "data": data}
    except TypeError:
        data = {"status": False, "data": []}
    return render(request, "home.html", context={"symbol_data": data, "subscribed_data": subscribed_data})


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
    old_data = SubscribedData.objects.filter(token=token)
    if not old_data:
        subscribed_data = SubscribedData(token=token, exchange=data.get("exch"), symbol=data.get("tsym"),
                                         cname=data.get("cname"))
        subscribed_data.save()
    return redirect("/")


def unsubscribe_token(request):
    token = request.GET.get("token")
    SubscribedData.objects.filter(token=token).delete()
    sapi.unsubscribe_wsticks(token)
    return redirect("/")


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


def download_db(request):
    db_location = settings.BASE_DIR / 'db.sqlite3'
    try:
        response = FileResponse(open(db_location, 'rb'), as_attachment=True)
    except IOError:
        response = HttpResponseNotFound('<h1>File not exist</h1>')
    return response
