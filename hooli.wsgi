#!/usr/bin/python

import sys
import site

from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.wrappers import Response

site.addsitedir('/var/www/hooli/venv/lib/python3.11/site-packages')
sys.path.insert(0,"/var/www/hooli/")

#from hooli_colab import app
#
## Configure DispatcherMiddleware to mount the app under /hooli
#application = DispatcherMiddleware(
#    Response('Not Found', status=404),
#    {'/hooli': app}
#)

from hooli_colab import app as application

import logging

logging.basicConfig(stream=sys.stderr)


