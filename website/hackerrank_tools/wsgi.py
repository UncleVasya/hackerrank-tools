"""
WSGI config for hackerrank_tools project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
"""

import os
from os.path import dirname
from os.path import realpath
from django.core.wsgi import get_wsgi_application
import sys
from whitenoise.django import DjangoWhiteNoise

sys.path.append(dirname(dirname(realpath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hackerrank_tools.settings")

virtenv = os.environ.get('OPENSHIFT_PYTHON_DIR', '.') + '/virtenv/'
virtualenv = os.path.join(virtenv, 'bin/activate_this.py')
try:
    execfile(virtualenv, dict(__file__=virtualenv))
except IOError:
    pass

application = get_wsgi_application()
application = DjangoWhiteNoise(application)
