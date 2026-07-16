from django.conf import settings
from django.db import models


class SpotifyAccount(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="spotify_account")
    spotify_user_id = models.CharField(max_length=128, unique=True)
    display_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    country = models.CharField(max_length=8, blank=True)
    product_type = models.CharField(max_length=32, blank=True)
    access_token = models.TextField()
    refresh_token = models.TextField(blank=True)
    token_expiry = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.display_name or self.spotify_user_id
