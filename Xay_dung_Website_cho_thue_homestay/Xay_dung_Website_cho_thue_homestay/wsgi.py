"""
WSGI config for Xay_dung_Website_cho_thue_homestay project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "Xay_dung_Website_cho_thue_homestay.settings"
)

application = get_wsgi_application()
