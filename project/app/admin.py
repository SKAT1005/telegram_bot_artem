from django.contrib import admin
from .models import API, User, Orders, WaveTime


@admin.register(API)
class ApiAdmin(admin.ModelAdmin):
    pass


@admin.register(Orders)
class OrderAdmin(admin.ModelAdmin):
    pass

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass

@admin.register(WaveTime)
class WaveTimeAdmin(admin.ModelAdmin):
    pass