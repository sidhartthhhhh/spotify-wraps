import secrets

from django.db import models

from spotify_auth.models import SpotifyAccount


def share_slug():
    return secrets.token_urlsafe(12)


class WrappedShare(models.Model):
    spotify_account = models.ForeignKey(SpotifyAccount, on_delete=models.CASCADE, related_name="wrapped_shares")
    slug = models.SlugField(max_length=64, unique=True, default=share_slug)
    period = models.CharField(max_length=16, default="yearly")
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    month = models.PositiveSmallIntegerField(null=True, blank=True)
    summary = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
