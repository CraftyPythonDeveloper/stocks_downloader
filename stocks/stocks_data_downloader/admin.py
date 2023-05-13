from django.contrib import admin
from .models import TestModelMongo
# Register your models here.


@admin.register(TestModelMongo)
class TestModelMongoAdmin(admin.ModelAdmin):
    readonly_fields = ("created_at", "modified")
