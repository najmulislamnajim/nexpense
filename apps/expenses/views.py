from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import ProtectedError, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import CategoryForm, ExpenseFilterForm, ExpenseForm
from .models import Category, Expense


def _user_categories(user):
    return Category.objects.filter(Q(owner__isnull=True) | Q(owner=user))


@login_required
def dashboard(request):
    today = timezone.localdate()
    month_start = today.replace(day=1)

    month_expenses = Expense.objects.filter(user=request.user, date__gte=month_start, date__lte=today)
    today_expenses = Expense.objects.filter(user=request.user, date=today)

    month_total = month_expenses.aggregate(total=Sum("amount"))["total"] or 0
    today_total = today_expenses.aggregate(total=Sum("amount"))["total"] or 0

    by_category = (
        month_expenses.values("category__name", "category__icon")
        .annotate(total=Sum("amount"))
        .order_by("-total")[:6]
    )
    max_category_total = max((row["total"] for row in by_category), default=0)

    recent = Expense.objects.filter(user=request.user).select_related("category")[:8]

    context = {
        "month_total": month_total,
        "today_total": today_total,
        "by_category": by_category,
        "max_category_total": max_category_total,
        "recent": recent,
        "month_label": today.strftime("%B %Y"),
    }
    return render(request, "expenses/dashboard.html", context)


class ExpenseListView(LoginRequiredMixin, ListView):
    model = Expense
    template_name = "expenses/expense_list.html"
    context_object_name = "expenses"
    paginate_by = 20

    def get_queryset(self):
        qs = Expense.objects.filter(user=self.request.user).select_related("category")
        self.filter_form = ExpenseFilterForm(self.request.GET or None, user=self.request.user)
        if self.filter_form.is_valid():
            data = self.filter_form.cleaned_data
            if data.get("start_date"):
                qs = qs.filter(date__gte=data["start_date"])
            if data.get("end_date"):
                qs = qs.filter(date__lte=data["end_date"])
            if data.get("category"):
                qs = qs.filter(category=data["category"])
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = self.filter_form
        context["total"] = self.get_queryset().aggregate(total=Sum("amount"))["total"] or 0
        return context


class ExpenseCreateView(LoginRequiredMixin, CreateView):
    model = Expense
    form_class = ExpenseForm
    template_name = "expenses/expense_form.html"
    success_url = reverse_lazy("expenses:list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, "Expense added.")
        return super().form_valid(form)


class ExpenseUpdateView(LoginRequiredMixin, UpdateView):
    model = Expense
    form_class = ExpenseForm
    template_name = "expenses/expense_form.html"
    success_url = reverse_lazy("expenses:list")

    def get_queryset(self):
        return Expense.objects.filter(user=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Expense updated.")
        return super().form_valid(form)


class ExpenseDeleteView(LoginRequiredMixin, DeleteView):
    model = Expense
    template_name = "expenses/expense_confirm_delete.html"
    success_url = reverse_lazy("expenses:list")

    def get_queryset(self):
        return Expense.objects.filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Expense deleted.")
        return super().form_valid(form)


class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = "expenses/category_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        return _user_categories(self.request.user)


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "expenses/category_form.html"
    success_url = reverse_lazy("expenses:category_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, "Category created.")
        return super().form_valid(form)


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Category
    template_name = "expenses/category_confirm_delete.html"
    success_url = reverse_lazy("expenses:category_list")

    def get_queryset(self):
        return Category.objects.filter(owner=self.request.user)

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, "This category has expenses linked to it and can't be deleted.")
            return redirect("expenses:category_list")
        messages.success(self.request, "Category deleted.")
        return response
