from django.conf import settings


def site_meta(request):
    """Expose site-wide branding info (header logo, footer credit) to all templates."""
    return {
        "SITE_NAME": settings.SITE_NAME,
        "DEVELOPER_NAME": settings.DEVELOPER_NAME,
        "DEVELOPER_WEBSITE": settings.DEVELOPER_WEBSITE,
        "DEFAULT_CURRENCY": settings.DEFAULT_CURRENCY,
    }
