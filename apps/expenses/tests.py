from datetime import date

from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User

from .forms import ExpenseFilterForm
from .models import Category, Expense


def make_user(email="person@example.com"):
    return User.objects.create_user(email=email, password="pass12345")


class CategoryModelTests(TestCase):
    def test_unique_constraint_per_owner(self):
        user = make_user()
        Category.objects.create(owner=user, name="Books")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Category.objects.create(owner=user, name="Books")

    def test_same_name_allowed_for_different_owners(self):
        user_a = make_user("a@example.com")
        user_b = make_user("b@example.com")
        Category.objects.create(owner=user_a, name="Books")
        # Should not raise: different owner.
        Category.objects.create(owner=user_b, name="Books")

    def test_expense_protects_its_category_from_deletion(self):
        user = make_user()
        category = Category.objects.create(owner=user, name="Books")
        Expense.objects.create(user=user, category=category, amount="10.00", date=date.today())
        with self.assertRaises(ProtectedError):
            category.delete()
        self.assertTrue(Category.objects.filter(pk=category.pk).exists())


class CategoryDeleteViewTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.login(username="person@example.com", password="pass12345")
        self.category = Category.objects.create(owner=self.user, name="Books")

    def test_delete_category_without_expenses_succeeds(self):
        response = self.client.post(reverse("expenses:category_delete", args=[self.category.pk]))
        self.assertRedirects(response, reverse("expenses:category_list"))
        self.assertFalse(Category.objects.filter(pk=self.category.pk).exists())

    def test_delete_category_with_expenses_is_handled_gracefully(self):
        Expense.objects.create(user=self.user, category=self.category, amount="10.00", date=date.today())
        response = self.client.post(reverse("expenses:category_delete", args=[self.category.pk]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Category.objects.filter(pk=self.category.pk).exists())
        messages = [str(m) for m in response.context["messages"]]
        self.assertTrue(any("expenses linked" in m for m in messages))


class DashboardViewTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.login(username="person@example.com", password="pass12345")
        self.category = Category.objects.create(owner=self.user, name="Books")

    def test_totals_only_include_current_user_and_current_month(self):
        today = date.today()
        earlier_in_month = today.replace(day=1) if today.day > 1 else today.replace(day=2)
        Expense.objects.create(user=self.user, category=self.category, amount="20.00", date=today)
        Expense.objects.create(user=self.user, category=self.category, amount="5.00", date=earlier_in_month)
        # Different user's expense must not be counted.
        other = make_user("other@example.com")
        Expense.objects.create(user=other, category=self.category, amount="100.00", date=today)

        response = self.client.get(reverse("expenses:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["month_total"], 25)
        self.assertEqual(response.context["today_total"], 20)


class ExpenseOwnershipTests(TestCase):
    def setUp(self):
        self.owner = make_user("owner@example.com")
        self.intruder = make_user("intruder@example.com")
        self.category = Category.objects.create(owner=self.owner, name="Books")
        self.expense = Expense.objects.create(
            user=self.owner, category=self.category, amount="10.00", date=date.today()
        )

    def test_other_user_cannot_update_expense(self):
        self.client.login(username="intruder@example.com", password="pass12345")
        response = self.client.get(reverse("expenses:update", args=[self.expense.pk]))
        self.assertEqual(response.status_code, 404)

    def test_other_user_cannot_delete_expense(self):
        self.client.login(username="intruder@example.com", password="pass12345")
        response = self.client.post(reverse("expenses:delete", args=[self.expense.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Expense.objects.filter(pk=self.expense.pk).exists())

    def test_owner_can_update_own_expense(self):
        self.client.login(username="owner@example.com", password="pass12345")
        response = self.client.get(reverse("expenses:update", args=[self.expense.pk]))
        self.assertEqual(response.status_code, 200)


class ExpenseFilterFormTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.category_a = Category.objects.create(owner=self.user, name="Books")
        self.category_b = Category.objects.create(owner=self.user, name="Food")
        Expense.objects.create(user=self.user, category=self.category_a, amount="10.00", date=date(2026, 1, 5))
        Expense.objects.create(user=self.user, category=self.category_b, amount="20.00", date=date(2026, 2, 5))

    def test_filters_by_date_range(self):
        form = ExpenseFilterForm(
            data={"start_date": "2026-01-01", "end_date": "2026-01-31"}, user=self.user
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.client.login(username="person@example.com", password="pass12345")
        response = self.client.get(reverse("expenses:list"), {"start_date": "2026-01-01", "end_date": "2026-01-31"})
        self.assertEqual(list(response.context["expenses"]), [Expense.objects.get(category=self.category_a)])

    def test_filters_by_category(self):
        self.client.login(username="person@example.com", password="pass12345")
        response = self.client.get(reverse("expenses:list"), {"category": self.category_b.pk})
        self.assertEqual(list(response.context["expenses"]), [Expense.objects.get(category=self.category_b)])
