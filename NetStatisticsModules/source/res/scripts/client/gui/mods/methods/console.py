# -*- coding: utf-8 -*-

__author__  = 'StranikS_Scan'
__version__ = 'V1.0 P2.7 W1.3.0 17.01.2019'

import threading
from copy import deepcopy

from http import loadJsonUrl

class _StatisticsConsole(object):
    def __init__(self):
        self.__onAsyncReports = {}

    def addAsyncReports(self, appToken, event):
        if appToken and event:
            if appToken in self.__onAsyncReports:
                self.__onAsyncReports[appToken].append(event)
            else:
                self.__onAsyncReports[appToken] = [event]

    def delAsyncReports(self, appToken, event=None):
        if appToken and appToken in self.__onAsyncReports:
            if event:
                if event in self.__onAsyncReports[appToken]:
                    self.__onAsyncReports[appToken].remove(event)
                if not self.__onAsyncReports[appToken]:
                    self.__onAsyncReports[appToken].pop(appToken)
            else:
                self.__onAsyncReports.pop(appToken)

    def __prepareRequest(self, appToken, async, url, onAsyncReports=None):
        if async:
            thread = threading.Thread(target=self.__sendRequest, args=[appToken, async, url, onAsyncReports])
            thread.setDaemon(True)
            thread.start()
        else:
            return self.__sendRequest(appToken, async, url, None)

    def __sendRequest(self, appToken, async, url, onAsyncReports):
        answer = loadJsonUrl(url)
        if async:
            if onAsyncReports:
                if isinstance(onAsyncReports, list):
                    for delegate in onAsyncReports[0:-1]:
                        delegate(deepcopy(answer))
                    onAsyncReports[-1](answer)
                else:
                    onAsyncReports(answer)
            else:
                if appToken in self.__onAsyncReports:
                    for delegate in self.__onAsyncReports[appToken][0:-1]:
                        delegate(deepcopy(answer))
                    self.__onAsyncReports[appToken][-1](answer)
        return answer
