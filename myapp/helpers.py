import calendar
from datetime import datetime
from django.utils import timezone


def end_of_month():
    today = timezone.now()
    end_of_month = calendar.monthrange(today.year, today.month)[1]
    end_of_month_date = datetime(today.year, today.month, end_of_month)
    return end_of_month_date.astimezone()
