from django.conf import settings


def leadhub_config(_request):
    return {"leadhub_base_url": settings.LEADHUB_BASE_URL}
