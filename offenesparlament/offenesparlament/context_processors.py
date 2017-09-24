from django.conf import settings

def analytics_code(request):
    return {'ANALYTICS_CODE': settings.ANALYTICS_CODE if hasattr(settings,
        'ANALYTICS_CODE') else None}
