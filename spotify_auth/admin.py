from django.contrib import admin
from .models import SpotifyAccount

@admin.register(SpotifyAccount)
class SpotifyAccountAdmin(admin.ModelAdmin):
    list_display = ("spotify_user_id", "display_name", "country", "product_type", "token_status", "updated_at")
    search_fields = ("spotify_user_id", "display_name", "email")
    readonly_fields = ("created_at", "updated_at", "token_status")
    exclude = ("access_token", "refresh_token")

    @admin.display(description="Tokens")
    def token_status(self, obj):
        return "Stored securely"
