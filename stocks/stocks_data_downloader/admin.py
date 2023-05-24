from django.apps import apps
from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered
from .models import *

app_models = apps.get_app_config('stocks_data_downloader').get_models()
for model in app_models:
    try:
        class AdminModel(admin.ModelAdmin):
            list_display = [f.name for f in model._meta.fields]
        admin.site.register(model, AdminModel)
    except AlreadyRegistered:
        pass

