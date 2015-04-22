#!/usr/bin/env python

"""
Call a json endpoint and return metrics about the page call
Also allow metrics for content in the json
"""

import requests
import sys

BASE_URL = 'https://CHANGEME.COM'
URL = '/'
URL_PARAMS = { 'ANY': 'VALUE'}  # can be left blank
EXIT = 0

# setup a metrics dictionary for metrics output
metrics = {}

# Try and get the json api endpoint
try:
    url = '%s%s' % (BASE_URL, URL)
    req = requests.get(url, params=URL_PARAMS)
    json_content = req.json()
except Exception as e:
    print "CRITICAL - %s" % str(e)
    sys.exit(2)

# Build the exit message. Anything other then 200 is not ideal
if req.status_code == 200:
    message = "OK | "
else:
    message = "Critical | "
    EXIT = 2

# return the time taken
metrics['time'] = str(req.elapsed.total_seconds()) + 's'
# return the http status code
metrics['http_status_code'] = req.status_code
# return the content size
metrics['size'] = str(req.headers['content-length']) + 'B'

for k,v in metrics.iteritems():
    message += "%s=%s;;; " % (k,v)

print message
sys.exit(EXIT)
