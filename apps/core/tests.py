from django.conf import settings
from django.test import RequestFactory, TestCase

from apps.accounts.models import User
from apps.expenses.models import Category

from .context_processors import site_meta


class SiteMetaContextProcessorTests(TestCase):
    def test_exposes_branding_settings(self):
        request = RequestFactory().get("/")
        context = site_meta(request)
        self.assertEqual(
            context,
            {
                "SITE_NAME": settings.SITE_NAME,
                "DEVELOPER_NAME": settings.DEVELOPER_NAME,
                "DEVELOPER_WEBSITE": settings.DEVELOPER_WEBSITE,
                "DEFAULT_CURRENCY": settings.DEFAULT_CURRENCY,
            },
        )


class TimeStampedModelTests(TestCase):
    def test_created_and_updated_at_are_set_automatically(self):
        user = User.objects.create_user(email="person@example.com", password="pass12345")
        category = Category.objects.create(owner=user, name="Books")

        self.assertIsNotNone(category.created_at)
        self.assertIsNotNone(category.updated_at)

        original_updated_at = category.updated_at
        category.name = "Novels"
        category.save()
        category.refresh_from_db()

        self.assertGreaterEqual(category.updated_at, original_updated_at)
