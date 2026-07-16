from django.contrib import admin
from .models import WrappedShare

@admin.register(WrappedShare)
class WrappedShareAdmin(admin.ModelAdmin):
    list_display = ("slug", "spotify_account", "period", "year", "is_active", "updated_at")
    list_filter = ("period", "is_active", "year")
    readonly_fields = ("slug", "summary", "created_at", "updated_at")
