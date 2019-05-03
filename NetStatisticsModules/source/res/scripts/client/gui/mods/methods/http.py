# -*- coding: utf-8 -*-

__author__  = 'StranikS_Scan'
__version__ = 'V1.2 P2.7 W1.2.0 03.05.2019'

from urllib2 import urlopen
from json import loads

URL_TIMEOUT = 3
STATUS_ERRORS = frozenset(['error', 'badRequest', 'badToken'])

def loadUrl(request):
    try:
        response = urlopen(url=request, timeout=URL_TIMEOUT)
        if response.code == 200:
            return response.read()
    except:
        pass

def loadJsonUrl(request):
    stats = loadUrl(request)
    if stats:
        try:
            stats = loads(stats)
        except:
            pass
        else:
            if isinstance(stats, dict):
                return stats if stats.get('status', '') not in STATUS_ERRORS else {}
