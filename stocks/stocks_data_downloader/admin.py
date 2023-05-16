from django.contrib import admin
from .models import WebSocketData, SubscribedData
# Register your models here.

admin.site.register(WebSocketData)
admin.site.register(SubscribedData)
