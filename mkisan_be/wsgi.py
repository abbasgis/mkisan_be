"""
WSGI config for mkisan_be project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

import os

import sys

sys.path.append('/home/python-www/mkisan_be')
sys.path.append('/home/python-www/mkisan_be/venv/lib/python3.8/site-packages')

from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.wsgi import get_wsgi_application

from mkisan_be import settings

#
# # add the virtualenv site-packages path to the sys.path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mkisan_be.settings")

if settings.DEBUG:
    application = StaticFilesHandler(get_wsgi_application())
else:
    application = get_wsgi_application()
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mkisan_be.settings")
#
# application = get_wsgi_application()
