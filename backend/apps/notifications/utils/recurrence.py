from __future__ import annotations

from datetime import datetime, timedelta

from django.utils import timezone

from apps.couples.models import (
    REPEAT_ALL_DAYS_MASK,
    REPEAT_FRIDAY,
    REPEAT_MONDAY,
    REPEAT_SATURDAY,
    REPEAT_SUNDAY,
    REPEAT_THURSDAY,
    REPEAT_TUESDAY,
    REPEAT_WEDNESDAY,
)

WEEKDAY_TO_REPEAT_FLAG = {
    0: REPEAT_MONDAY,
    1: REPEAT_TUESDAY,
    2: REPEAT_WEDNESDAY,
    3: REPEAT_THURSDAY,
    4: REPEAT_FRIDAY,
    5: REPEAT_SATURDAY,
    6: REPEAT_SUNDAY,
}


def _make_aware_event_datetime(event_date, event_time):
    naive_event_datetime = datetime.combine(event_date, event_time)
    if timezone.is_aware(naive_event_datetime):
        return naive_event_datetime
    return timezone.make_aware(naive_event_datetime)


def iter_upcoming_occurrences(event_date, event_time, repeat_mask, window_start, window_end):
    """Yield event occurrence datetimes inside a bounded window.

    The schedule stays rolling, not infinite. That keeps recurring events
    from generating unbounded future notification rows.
    """

    if window_end < window_start:
        return

    if repeat_mask == 0:
        occurrence = _make_aware_event_datetime(event_date, event_time)
        if window_start <= occurrence <= window_end and occurrence.date() >= event_date:
            yield occurrence
        return

    current_date = max(event_date, window_start.date())
    end_date = window_end.date()
    current_time = event_time

    while current_date <= end_date:
        weekday_flag = WEEKDAY_TO_REPEAT_FLAG.get(current_date.weekday())
        if weekday_flag and repeat_mask & weekday_flag:
            occurrence = _make_aware_event_datetime(current_date, current_time)
            if window_start <= occurrence <= window_end:
                yield occurrence
        current_date += timedelta(days=1)


def event_occurs_within_window(event_date, event_time, repeat_mask, window_start, window_end):
    return any(iter_upcoming_occurrences(event_date, event_time, repeat_mask, window_start, window_end))
