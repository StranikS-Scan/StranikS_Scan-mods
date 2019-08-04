# -*- coding: utf-8 -*-

__author__  = 'StranikS_Scan'
__version__ = 'V1.0 P2.7 W1.5.1 04.08.2019'

import os, codecs
from datetime import datetime
from json import dumps
from Math import Vector3

def getGlobalID():
    now = datetime.now()
    return now.strftime('%d%m%y'), now.strftime('%H%M%S%f')[:9] #('030819', 113960123)

DATE_GLOBAL_ID, TIME_GLOBAL_ID = getGlobalID()

def updateGlobalID():
    global DATE_GLOBAL_ID, TIME_GLOBAL_ID
    DATE_GLOBAL_ID, TIME_GLOBAL_ID = getGlobalID()

#Simple log-file
class _LogFile(object):
    fileName = property(lambda self: self.__file)

    #logName='hits_%date%time.log'                      -> ./mods/hits_030819113960123.txt
    #logName='hits_%date_%time.txt' logDir='logs/mylog' -> ./mods/logs/mylog/hits_030819_113960123.txt
    #logName='hits_%date_%time.dat' logDir='C:\\mylog'  -> C:/mylog/hits_030819_113960123.csv
    def __init__(self, logName, logDir='', useGlobalID=True):
        self.__file = logDir
        if self.__file:
            self.__file = self.__file.replace('\\', '/')
            if self.__file[-1] != '/':
                self.__file += '/'
            self.__file = ('./mods/' if ':' not in self.__file else '') + self.__file #Absolute path is also supported
            if not os.path.exists(self.__file):
                try:
                    os.makedirs(self.__file)
                except:
                    self.__file = './mods/'
        else:
            self.__file = './mods/'
        #---
        if useGlobalID:
            dateID = DATE_GLOBAL_ID
            timeID = TIME_GLOBAL_ID
        else:
            dateID, timeID = getGlobalID()
        if '%date' in logName:
            logName = logName.replace('%date', dateID)
        if '%time' in logName:
            logName = logName.replace('%time', timeID)
        self.__file += logName

    def destroy(self):
        self.__file = None

    def clearText(self):
        if self.__file:
            with open(self.__file,'w'): pass

    #value='abc' -> abc\n
    def writeText(self, value): 
        if self.__file:
            with codecs.open(self.__file, 'a', 'utf-8') as f:
                f.write(value + '\n')

    #values=('123','abc') -> 123\nabc\n
    def writeStrings(self, values): 
        if self.__file:
            with codecs.open(self.__file, 'a', 'utf-8') as f:
                if isinstance(values, list) or isinstance(values, tuple):
                    f.write('\n'.join(values) + '\n')
                else:
                    f.write(values + '\n')

#CSV log-file
class _CSVLog(_LogFile):
    headersCount = property(lambda self: len(self.__headers))
    valuesCount = property(lambda self: len(self.__values))

    #logName='hits_ver_%csv_%date%time.txt' -> ./mods/hits_ver_1.1_030819113960123.txt
    def __init__(self, logName, logDir='', csvVersion='', useGlobalID=True):
        _LogFile.__init__(self, logName, logDir, useGlobalID)
        #---
        self.__headers = []
        self.__values = []
        self.__floatMask = '%.10f'
        self.__noneMask = '' #Example '"null"' or '"None"'
        self.__vectorToXYZ = True
        #--
        if csvVersion and '%csv' in self._LogFile__file:
            self._LogFile__file = self._LogFile__file.replace('%csv', csvVersion)

    def destroy(self):
        self.__headers = self.__values = []
        _LogFile.destroy(self)

    @property
    def floatMask(self):
        return self.__floatMask

    @floatMask.setter
    def floatMask(self, value):
        self.__floatMask = value

    @property
    def noneMask(self):
        return self.__noneMask

    @noneMask.setter
    def noneMask(self, value):
        self.__noneMask = value

    @property
    def vectorToXYZ(self):
        return self.__vectorToXYZ

    @vectorToXYZ.setter
    def vectorToXYZ(self, value):
        self.__vectorToXYZ = value

    def __convertValueToStr(self, value):
        if value is None:
            return self.__noneMask
        elif isinstance(value, str):
            return value
        elif isinstance(value, int):
            return '%d' % value
        elif isinstance(value, float):
            return (self.__floatMask % value).replace('.',',')
        elif isinstance(value, Vector3):
            if self.__vectorToXYZ:
                return ((self.__floatMask % value[0]).replace('.',','), \
                        (self.__floatMask % value[1]).replace('.',','), \
                        (self.__floatMask % value[2]).replace('.',','))
            else:
                return '%s' % value
        elif isinstance(value, list) or isinstance(value, tuple) or isinstance(value, dict):
            try:
                return dumps(value)
            except:
                return '%s' % value
        else:
            return '%s' % value

    def addHeaders(self, values):
        if isinstance(values, list) or isinstance(values, tuple):
            for value in values:
                self.__headers.append('"%s"' % value)
        else:
            self.__headers.append('"%s"' % values)

    def clearHeaders(self):
        self.__headers = []

    #('123','abc') -> "123";"abc"\n
    def writeStoreHeaders(self):
        if self.__headers:
            self.writeText(';'.join(self.__headers) if isinstance(self.__headers, list) or isinstance(self.__headers, tuple) else self.__headers)

    #value=12.333, mask='%.2f' -> 12,33
    #value=('45','78'), mask='"%s"' -> "45", "78"
    def addMaskedValues(self, values, mask='%s'):
        if isinstance(values, list) or isinstance(values, tuple):
            for value in values:
                if isinstance(value, float) and mask[-1] == 'f':
                    self.__values.append((mask % value).replace('.',','))
                else:
                    self.__values.append(mask % value)
        else:
            if isinstance(values, float):
                self.__values.append((mask % values).replace('.',','))
            else:
                self.__values.append(mask % values)

    #values=Vector3(1.0,2.0,3.0) -> 1,0, 2,0, 3,0
    #values=('45', 12.334455, 78, {'hello':1, 'world':2}) -> 45, 12,33, 78, {"hello": 1, "world": 2}
    def addValues(self, values):
        if isinstance(values, list) or isinstance(values, tuple):
            for value in values:
                new_values = self.__convertValueToStr(value)
                if isinstance(new_values, str):
                    self.__values.append(new_values)
                else:
                    for new_value in new_values:
                        self.__values.append(new_value)
        else:
            new_values = self.__convertValueToStr(values)
            if isinstance(new_values, str):
                self.__values.append(new_values)
            else:
                for new_value in new_values:
                    self.__values.append(new_value)

    def clearValues(self):
        self.__values = []

    #('123','abc') -> 123;abc\n
    def writeStoreValues(self):
        if self.__values:
            self.writeText(';'.join(self.__values) if isinstance(self.__values, list) or isinstance(self.__values, tuple) else self.__values)
            self.clearValues()

g_Logs = {}