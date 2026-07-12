from django.core import mail
from django.test import TestCase
from django.urls import reverse

from .forms import SignUpForm
from .models import User


class UserManagerTests(TestCase):
    def test_create_user_requires_email(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password="pass12345")

    def test_create_user_normalizes_email_domain(self):
        user = User.objects.create_user(email="person@EXAMPLE.com", password="pass12345")
        self.assertEqual(user.email, "person@example.com")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser_sets_staff_and_superuser_flags(self):
        user = User.objects.create_superuser(email="admin@example.com", password="pass12345")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_create_superuser_rejects_is_staff_false(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(email="admin@example.com", password="pass12345", is_staff=False)

    def test_get_short_and_full_name_fallback_to_email(self):
        user = User.objects.create_user(email="noname@example.com", password="pass12345")
        self.assertEqual(user.get_short_name(), "noname")
        self.assertEqual(user.get_full_name(), "noname@example.com")

        user.full_name = "Jane Doe"
        self.assertEqual(user.get_short_name(), "Jane")
        self.assertEqual(user.get_full_name(), "Jane Doe")


class SignUpFormTests(TestCase):
    def setUp(self):
        User.objects.create_user(email="existing@example.com", password="pass12345")

    def test_rejects_case_insensitive_duplicate_email(self):
        form = SignUpForm(
            data={
                "full_name": "New Person",
                "email": "Existing@Example.com",
                "currency": "BDT",
                "password1": "a-strong-pass1",
                "password2": "a-strong-pass1",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_accepts_new_unique_email(self):
        form = SignUpForm(
            data={
                "full_name": "New Person",
                "email": "new@example.com",
                "currency": "BDT",
                "password1": "a-strong-pass1",
                "password2": "a-strong-pass1",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)


class SignUpViewTests(TestCase):
    def test_signup_creates_user_and_logs_in(self):
        response = self.client.post(
            reverse("accounts:signup"),
            data={
                "full_name": "New Person",
                "email": "new@example.com",
                "currency": "BDT",
                "password1": "a-strong-pass1",
                "password2": "a-strong-pass1",
            },
        )
        self.assertRedirects(response, reverse("expenses:dashboard"))
        self.assertTrue(User.objects.filter(email="new@example.com").exists())

        # Auto-login: the session is authenticated for the follow-up request.
        dashboard_response = self.client.get(reverse("expenses:dashboard"))
        self.assertEqual(dashboard_response.status_code, 200)


class LoginLogoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="person@example.com", password="pass12345")

    def test_login_with_email_then_logout(self):
        login_ok = self.client.login(username="person@example.com", password="pass12345")
        self.assertTrue(login_ok)

        response = self.client.get(reverse("expenses:dashboard"))
        self.assertEqual(response.status_code, 200)

        self.client.logout()
        response = self.client.get(reverse("expenses:dashboard"))
        self.assertNotEqual(response.status_code, 200)

    def test_login_requires_correct_password(self):
        login_ok = self.client.login(username="person@example.com", password="wrong-password")
        self.assertFalse(login_ok)


class PasswordResetTests(TestCase):
    def setUp(self):
        User.objects.create_user(email="person@example.com", password="pass12345")

    def test_password_reset_sends_email(self):
        response = self.client.post(reverse("accounts:password_reset"), data={"email": "person@example.com"})
        self.assertRedirects(response, reverse("accounts:password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("person@example.com", mail.outbox[0].to)

    def test_password_reset_unknown_email_does_not_error(self):
        response = self.client.post(reverse("accounts:password_reset"), data={"email": "unknown@example.com"})
        self.assertRedirects(response, reverse("accounts:password_reset_done"))
        self.assertEqual(len(mail.outbox), 0)
