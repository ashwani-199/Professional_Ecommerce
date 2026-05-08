from django.conf import settings


def seo_settings(request):
    return {
        'GA_TRACKING_ID': getattr(settings, 'GA_TRACKING_ID', ''),
        'ADSENSE_CLIENT_ID': getattr(settings, 'ADSENSE_CLIENT_ID', ''),
        'ADSENSE_SLOT_HOME': getattr(settings, 'ADSENSE_SLOT_HOME', ''),
        'ADSENSE_SLOT_LIST': getattr(settings, 'ADSENSE_SLOT_LIST', ''),
        'ADSENSE_SLOT_DETAIL': getattr(settings, 'ADSENSE_SLOT_DETAIL', ''),
        'SITE_NAME': getattr(settings, 'SITE_NAME', 'American Owl'),
        'SITE_DESCRIPTION': getattr(settings, 'SITE_DESCRIPTION', 'Your trusted American marketplace for quality products at unbeatable prices.'),
        'SITE_URL': getattr(settings, 'SITE_URL', 'https://americanowl.com'),
    }
