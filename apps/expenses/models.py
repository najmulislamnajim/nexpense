from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel

PAYMENT_METHOD_CHOICES = [
    ("cash", "Cash"),
    ("card", "Card"),
    ("bank", "Bank Transfer"),
    ("mobile_banking", "Mobile Banking"),
    ("other", "Other"),
]

DEFAULT_CATEGORIES = [
    ("Food & Groceries", "🍔"),
    ("Transport", "🚌"),
    ("Housing & Rent", "🏠"),
    ("Utilities", "💡"),
    ("Health", "🩺"),
    ("Education", "📚"),
    ("Entertainment", "🎬"),
    ("Shopping", "🛍️"),
    ("Savings & Investment", "💰"),
    ("Other", "🧾"),
]


class Category(TimeStampedModel):
    """Expense category. Global defaults (owner=None) plus per-user custom categories."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="categories",
        null=True,
        blank=True,
        help_text="Blank for built-in default categories shared by everyone.",
    )
    name = models.CharField(max_length=80)
    icon = models.CharField(max_length=8, default="🧾")

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["owner", "name"], name="unique_category_per_owner"),
        ]

    def __str__(self):
        return self.name


class Expense(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="expenses")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="expenses")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default="cash")
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        indexes = [
            models.Index(fields=["user", "date"]),
            models.Index(fields=["user", "category"]),
        ]

    def __str__(self):
        return f"{self.category} - {self.amount} ({self.date})"
