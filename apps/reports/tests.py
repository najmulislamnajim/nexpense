from datetime import date

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.expenses.models import Category, Expense

from .services import category_breakdown, filtered_expenses, report_summary


def make_user(email="person@example.com"):
    return User.objects.create_user(email=email, password="pass12345")


class ServicesTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.books = Category.objects.create(owner=self.user, name="Books")
        self.food = Category.objects.create(owner=self.user, name="Food")
        Expense.objects.create(user=self.user, category=self.books, amount="10.00", date=date(2026, 1, 5))
        Expense.objects.create(user=self.user, category=self.food, amount="15.00", date=date(2026, 1, 20))
        Expense.objects.create(user=self.user, category=self.books, amount="99.00", date=date(2026, 3, 1))

    def test_filtered_expenses_scopes_by_user_and_date_range(self):
        qs = filtered_expenses(self.user, date(2026, 1, 1), date(2026, 1, 31))
        self.assertEqual(qs.count(), 2)

    def test_filtered_expenses_filters_by_category(self):
        qs = filtered_expenses(self.user, date(2026, 1, 1), date(2026, 1, 31), category=self.books)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().category, self.books)

    def test_report_summary_totals_and_breakdown(self):
        qs = filtered_expenses(self.user, date(2026, 1, 1), date(2026, 1, 31))
        summary = report_summary(qs)
        self.assertEqual(summary["total"], 25)
        self.assertEqual(summary["count"], 2)
        self.assertEqual(len(summary["breakdown"]), 2)

    def test_category_breakdown_orders_by_total_descending(self):
        qs = filtered_expenses(self.user, date(2026, 1, 1), date(2026, 1, 31))
        breakdown = list(category_breakdown(qs))
        self.assertEqual(breakdown[0]["category__name"], "Food")
        self.assertEqual(breakdown[0]["total"], 15)


class ExportViewTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.login(username="person@example.com", password="pass12345")
        category = Category.objects.create(owner=self.user, name="Books")
        Expense.objects.create(user=self.user, category=category, amount="10.00", date=date.today())

    def test_csv_export(self):
        response = self.client.get(reverse("reports:export", args=["csv"]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("attachment; filename=", response["Content-Disposition"])
        self.assertTrue(response["Content-Disposition"].endswith('.csv"'))

    def test_xlsx_export(self):
        response = self.client.get(reverse("reports:export", args=["xlsx"]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertTrue(response["Content-Disposition"].endswith('.xlsx"'))

    def test_pdf_export(self):
        response = self.client.get(reverse("reports:export", args=["pdf"]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response["Content-Disposition"].endswith('.pdf"'))

    def test_unsupported_format_returns_bad_request(self):
        response = self.client.get(reverse("reports:export", args=["docx"]))
        self.assertEqual(response.status_code, 400)
