from django.db import migrations

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


def seed_categories(apps, schema_editor):
    Category = apps.get_model("expenses", "Category")
    for name, icon in DEFAULT_CATEGORIES:
        Category.objects.get_or_create(owner=None, name=name, defaults={"icon": icon})


def remove_categories(apps, schema_editor):
    Category = apps.get_model("expenses", "Category")
    Category.objects.filter(owner=None, name__in=[name for name, _ in DEFAULT_CATEGORIES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("expenses", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_categories, remove_categories),
    ]
