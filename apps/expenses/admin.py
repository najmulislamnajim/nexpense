from django.contrib import admin

from .models import Category, Expense


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "icon", "owner")
    search_fields = ("name",)
    list_filter = ("owner",)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("user", "category", "amount", "date", "payment_method")
    list_filter = ("category", "payment_method", "date")
    search_fields = ("note", "user__email")
    date_hierarchy = "date"
