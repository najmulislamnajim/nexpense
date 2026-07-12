from django.db.models import Sum
from django.utils import timezone

from apps.expenses.models import Expense


def filtered_expenses(user, start_date=None, end_date=None, category=None):
    qs = Expense.objects.filter(user=user).select_related("category")
    if start_date:
        qs = qs.filter(date__gte=start_date)
    if end_date:
        qs = qs.filter(date__lte=end_date)
    if category:
        qs = qs.filter(category=category)
    return qs


def default_date_range():
    today = timezone.localdate()
    return today.replace(day=1), today


def category_breakdown(queryset):
    return (
        queryset.values("category__name", "category__icon")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )


def report_summary(queryset):
    total = queryset.aggregate(total=Sum("amount"))["total"] or 0
    breakdown = list(category_breakdown(queryset))
    max_total = max((row["total"] for row in breakdown), default=0)
    return {
        "total": total,
        "count": queryset.count(),
        "breakdown": breakdown,
        "max_total": max_total,
    }
