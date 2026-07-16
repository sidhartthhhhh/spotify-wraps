from collections import Counter
from datetime import date, timedelta

from django.db.models import Count, Sum
from django.db.models.functions import ExtractHour, ExtractMonth, ExtractWeekDay, TruncDate, TruncMonth
from django.utils import timezone

from listening.models import ListeningHistory


def history_for(account, start=None, end=None):
    qs = ListeningHistory.objects.filter(spotify_account=account).select_related("track", "track__album").prefetch_related("track__artists")
    if start:
        qs = qs.filter(played_at__date__gte=start)
    if end:
        qs = qs.filter(played_at__date__lte=end)
    return qs


def listening_personality(summary):
    if summary["night_percent"] >= 40:
        return "Night Listener"
    if summary["weekend_percent"] >= 45:
        return "Weekend Explorer"
    if summary["total_events"] and summary["unique_tracks"] / summary["total_events"] < .35:
        return "Repeat Specialist"
    if summary["unique_artists"] >= 50:
        return "Genre Wanderer"
    if summary["unique_tracks"] >= 100:
        return "Discovery Driven"
    return "Loyal Fan"


def summary(account, start=None, end=None):
    qs = history_for(account, start, end)
    total = qs.count()
    top_track = qs.values("track__name", "track__album__image_url").annotate(count=Count("id")).order_by("-count").first()
    top_artist = qs.values("track__artists__name", "track__artists__image_url").annotate(count=Count("id")).order_by("-count").first()
    day = qs.annotate(day=TruncDate("played_at")).values("day").annotate(count=Count("id")).order_by("-count").first()
    hour = qs.annotate(hour=ExtractHour("played_at")).values("hour").annotate(count=Count("id")).order_by("-count").first()
    weekdays = list(qs.annotate(day=ExtractWeekDay("played_at")).values("day").annotate(count=Count("id")).order_by("day"))
    hours = list(qs.annotate(hour=ExtractHour("played_at")).values("hour").annotate(count=Count("id")).order_by("hour"))
    months = list(qs.annotate(month=TruncMonth("played_at")).values("month").annotate(count=Count("id")).order_by("month"))
    weekend = sum(row["count"] for row in weekdays if row["day"] in (1, 7))
    night = sum(row["count"] for row in hours if row["hour"] < 6 or row["hour"] >= 22)
    days = sorted(set(qs.values_list("played_at__date", flat=True)))
    longest = current = 0
    previous = None
    for value in days:
        current = current + 1 if previous and value == previous + timedelta(days=1) else 1
        longest, previous = max(longest, current), value
    data = {
        "total_events": total,
        "estimated_minutes": round((qs.aggregate(ms=Sum("track__duration_ms"))["ms"] or 0) / 60000),
        "unique_tracks": qs.values("track").distinct().count(),
        "unique_artists": qs.values("track__artists").distinct().count(),
        "most_played_track": top_track,
        "most_played_artist": top_artist,
        "most_active_day": day,
        "most_active_hour": hour,
        "weekend_percent": round(weekend * 100 / total) if total else 0,
        "night_percent": round(night * 100 / total) if total else 0,
        "monthly": [{"label": row["month"].strftime("%b %Y"), "count": row["count"]} for row in months],
        "weekday": weekdays,
        "hourly": hours,
        "top_albums": list(qs.values("track__album__name").annotate(count=Count("id")).order_by("-count")[:5]),
        "top_tracks": list(qs.values("track__name").annotate(count=Count("id")).order_by("-count")[:5]),
        "top_artists": list(qs.values("track__artists__name").annotate(count=Count("id")).order_by("-count")[:5]),
        "longest_streak": longest,
    }
    data["personality"] = listening_personality(data)
    return data


def monthly_summary(account, year=None, month=None):
    today = timezone.localdate()
    year, month = year or today.year, month or today.month
    return summary(account, date(year, month, 1), date(year + (month == 12), month % 12 + 1, 1) - timedelta(days=1))


def yearly_summary(account, year=None):
    year = year or timezone.localdate().year
    return summary(account, date(year, 1, 1), date(year, 12, 31))
