# -*- coding: utf-8 -*-

__author__  = 'StranikS_Scan'
__version__ = 'V1.0 P2.7 W1.2.0 29.11.2018'

import BigWorld
from items import vehicles
from gui.shared.gui_items.Vehicle import getVehicleClassTag

from os import path, makedirs
from StringIO import StringIO
import json, gzip, cPickle
from math import log, ceil

from http_methods import loadUrl

# Consts .....................................................................

#SERVERS in "xvm_main\python\consts.py"-module
XVM_SERVER = 'https://static.modxvm.com'

#{'xwgr': [1361, ...], 'xeff': [378, ...], 'xwn8': [56,...], 'xwin': [43.44, ...], 'xwtr': [1409, ...]}
TABLE_XVMSCALE = XVM_SERVER + '/xvmscales.json.gz'
#{'header': {'url': 'https://...', 'source': 'XVM', 'version': '2018-02-12'},
# 'data': [{'expDamage': 1079.886, 'expSpot': 0.769, 'IDNum': 55297, 'expWinRate': 52.995, 'expDef': 0.881, 'expFrag': 1.146}, ...]}
TABLE_WN8 = XVM_SERVER + '/wn8-data-exp/json/wn8exp.json.gz'
#{'62737': {'tf': 1.64, 'x': [342, ...], 'td': 2168, 'ad': 1171, 'af': 0.78}, ...}
TABLE_XTE = XVM_SERVER + '/xte.json.gz'
#{'62737': {'tf': 1.64, 'x': [726, ...], 'td': 2168, 'ad': 1171, 'af': 0.78}, ...}
TABLE_XTDB = XVM_SERVER + '/xtdb.json.gz'

SHORT_TAGS_XVM = {'account_id':             '_id',
                  'vehicles':               'v',
                  'tank_id':                'id',
                  'nickname':               'nm',
                  'clan_id':                'cid',
                  'client_language':        'lang',
                  'battles':                'b',
                  'wins':                   'w',
                  'survived_battles':       'srv',
                  'damage_dealt':           'dmg',
                  'frags':                  'frg',
                  'spotted':                'spo',
                  'dropped_capture_points': 'def',
                  'capture_points':         'cap',
                  'hits_percents':          'hip',
                  'damage_received':        'dmg_r',
                  'max_damage':             'max_dmg',
                  'max_frags':              'max_frg',
                  'mark_of_mastery':        'mom',
                  'global_rating':          'wgr',
                  'avg_level':              'lvl'}

SHORT_TAGS_WG = {'avg_damage_blocked':        'avg_dbl',
                 'avg_damage_assisted':       'avg_das',
                 'avg_damage_assisted_radio': 'avg_dar',
                 'avg_damage_assisted_track': 'avg_dat',
                 'stun_assisted_damage':      'sad'}

SHORT_TAGS = {}
SHORT_TAGS.update(SHORT_TAGS_XVM)
SHORT_TAGS.update(SHORT_TAGS_WG)
LONG_TAGS = dict(map(reversed, SHORT_TAGS.items()))

# Classes ====================================================================

class TABLE_ERRORS:
    OK          = 0
    NOT_READED  = 1
    NOT_UPDATED = 2

#Based on then code from vehinfo.py
class _Tables(object):
    errorStatus   = property(lambda self: self.__getErrorStatus())
    xvmscaleTable = property(lambda self: self.__xvmscale)
    wn8Table      = property(lambda self: self.__wn8)
    wn8idsTable   = property(lambda self: self.__wn8ids)
    xteTable      = property(lambda self: self.__xte)
    xtdbTable     = property(lambda self: self.__xtdb)
    supTable      = property(lambda self: self.__sup)

    def __init__(self):
        self.__error = TABLE_ERRORS.OK
        self.__xvmscale_filename = CACHE_PATH + 'cache/' + path.basename(TABLE_XVMSCALE) + '.dat'
        self.__wn8_filename      = CACHE_PATH + 'cache/' + path.basename(TABLE_WN8)      + '.dat'
        self.__xte_filename      = CACHE_PATH + 'cache/' + path.basename(TABLE_XTE)      + '.dat'
        self.__xtdb_filename     = CACHE_PATH + 'cache/' + path.basename(TABLE_XTDB)     + '.dat'
        #Сorresponds to the XVM 7.4.0 of 06/02/2018
        self.__sup = [1.2, 1.5, 1.9, 2.5, 3.1, 3.8, 4.6, 5.5, 6.6, 7.7, 9.0, 10, 12, 14, 15, 17, 19, 21, 24, 26, 28, 31, 33, 36, 38, 41, 43, 46, 48, 51, 53, 56, 58, 60, 63, 65, 67, 69, 71, 73, 74, 76, 78, 79, 80.8, 82.2, 83.6, 84.8, 86.0, 87.1, 88.1, 89.0, 89.9, 90.8, 91.6, 92.3, 92.9, 93.6, 94.1, 94.7, 95.1, 95.6, 96.0, 96.4, 96.7, 97.0, 97.3, 97.6, 97.8, 98.0, 98.2, 98.4, 98.6, 98.7, 98.9, 99.0, 99.1, 99.2, 99.3, 99.37, 99.44, 99.51, 99.57, 99.62, 99.67, 99.71, 99.75, 99.78, 99.81, 99.84, 99.86, 99.88, 99.90, 99.92, 99.93, 99.95, 99.96, 99.97, 99.98, 99.99]
        self.init()

    def init(self):
        self.__xvmscale = \
        self.__wn8      = \
        self.__wn8ids   = \
        self.__xte      = \
        self.__xtdb     = None
        if self.__downloadTable(TABLE_XVMSCALE, self.__xvmscale_filename) and \
           self.__downloadTable(TABLE_WN8,      self.__wn8_filename) and \
           self.__downloadTable(TABLE_XTE,      self.__xte_filename) and \
           self.__downloadTable(TABLE_XTDB,     self.__xtdb_filename):
            self.__error = TABLE_ERRORS.OK
        else:
            self.__error = TABLE_ERRORS.NOT_UPDATED
        self.__xvmscale = self.__getTable(self.__xvmscale_filename)
        self.__wn8      = self.__getTable(self.__wn8_filename)
        self.__xte      = self.__getTable(self.__xte_filename)
        self.__xtdb     = self.__getTable(self.__xtdb_filename)
        if not isinstance(self.__xvmscale, dict) or \
           not isinstance(self.__wn8, dict) or \
           not isinstance(self.__xte, dict) or \
           not isinstance(self.__xtdb, dict):
            self.__error = TABLE_ERRORS.NOT_READED
        if self.__wn8:
            self.__wn8ids = {}
            for stat in self.__wn8['data']:
                self.__wn8ids[int(stat['IDNum'])] = dict([x for x in stat.iteritems() if x[0] != 'IDNum'])

    def __getTable(self, filename):
        if path.exists(filename):
            try:
                with open(filename,'rb') as f:
                    content = f.read()
                return json.loads(gzip.GzipFile(fileobj=StringIO(cPickle.loads(content))).read())
            except:
                pass

    def __downloadTable(self, url, filename):
        content = loadUrl(url)
        if content:
            dirname = path.dirname(filename)
            try:
                if not path.exists(dirname):
                    makedirs(dirname)
                with open(filename, 'wb') as f:
                    f.write(cPickle.dumps(content))
                return True
            except:
                pass
        return False

    def __getErrorStatus(self):
        if self.__error == TABLE_ERRORS.NOT_READED:
            return 'One or more tables are not read from disk!'
        elif self.__error == TABLE_ERRORS.NOT_UPDATED:
            return 'One or more tables are not updated from the XVM-site!'       
        return ''

class _Calculator(object):
    #Converting an absolute value to an index or float value of a universal XVM-Scale
    #rating = ['wgr', 'eff', 'wn8', 'win', 'wtr', 'xte', 'xtdb', 'sup']
    def globalRating(self, value, rating, exact=False):
        if rating in ['xte', 'xtdb']:
            return max(0, min(value, 100))
        else:
            stat = None
            if rating == 'sup':
                stat = g_Tables.supTable
            elif rating in ['wgr', 'eff', 'wn8', 'win', 'wtr']:
                if g_Tables.xvmscaleTable:
                    stat = g_Tables.xvmscaleTable.get('x'+rating)
            if stat:
                index = next((i for i,x in enumerate(stat) if x > value), 100)
                if exact:
                    if index < 100:
                        if index == 0:
                            if value > 0:
                                return float(value) / stat[0]
                        else:
                            return index + (float(value) - stat[index-1]) / (stat[index] - stat[index-1])
                    return float(index)
                return index

    #Get the value of the specific rating by the XVM-Scale
    #rating = ['wgr', 'eff', 'wn8', 'win', 'wtr', 'xte', 'xtdb', 'sup']
    def specificRating(self, value, rating): 
        if rating in ['xte', 'xtdb']:
            return max(0, min(value, 100))
        else:
            if rating == 'sup':
                stat = g_Tables.supTable
            elif rating in ['wgr', 'eff', 'wn8', 'win', 'wtr']:
                if g_Tables.xvmscaleTable:
                    stat = g_Tables.xvmscaleTable.get('x' + rating)
            if stat:
                if value > 0:
                    if int(value) == 0:
                        return float(value) * stat[0]
                    indexed_value = stat[min(int(value), 100)-1]
                    if value < 100 and isinstance(value, float): 
                        return indexed_value + (float(value) - int(value)) * (stat[int(value)] - stat[int(value)-1])
                    return indexed_value
                return 0.0

    #Return the average level of player's tanks
    #params = {'id': {'b':int}, ...} and also WG-tags are supported
    def avgTIER(self, params):
        if isinstance(params, dict):
            avgLevel = battles = 0
            for id, value in params.items():
                allBAT = value.get('b', 0) if 'b' in value else value.get(LONG_TAGS['b'], 0)
                vehicle = vehicles.getVehicleType(int(id))
                if vehicle:
                    battles += allBAT
                    avgLevel += vehicle.level * allBAT
            if battles:
                avgLevel = round(float(avgLevel) / battles, 5)
            return avgLevel

    #Return the number of wins to increase the percentage of wins by a given amount and final winning percentage
    #params = {'b': int, 'w': int} and also WG-tags are supported; incPercentage = float
    def needWin(self, params, incPercentage):
        if isinstance(params, dict):
            allBAT = params.get('b', 0) if 'b' in params else params.get(LONG_TAGS['b'], 0)
            allWIN = params.get('w', 0) if 'w' in params else params.get(LONG_TAGS['w'], 0)
            if allBAT:
                battles = int(ceil(incPercentage * allBAT * allBAT / (allBAT * (100.0 - incPercentage) - 100.0 * allWIN))) \
                          if allWIN < allBAT and (0 < incPercentage < 100 * (1 - float(allWIN) / allBAT)) else 0
                return battles, 100.0 * (allWIN + battles) / (allBAT + battles)

    #Return the number of wins to increase the percentage of wins to the next half percent value and final winning percentage
    #params = {'b': int, 'w': int} and also WG-tags are supported
    def needWinHalf(self, params):
        if isinstance(params, dict):
            allBAT = params.get('b', 0) if 'b' in params else params.get(LONG_TAGS['b'], 0)
            allWIN = params.get('w', 0) if 'w' in params else params.get(LONG_TAGS['w'], 0)
            if allBAT:
                currentWiR = 100.0 * allWIN / allBAT
                newWiR = int(currentWiR) + (0.5 if int(currentWiR) > currentWiR - 0.5 else 1)
                battles = int(ceil((100.0 * allWIN - newWiR * allBAT) / (newWiR - 100.0))) if allWIN < allBAT and newWiR < 100 else 0
                return battles, 100.0 * (allWIN + battles) / (allBAT + battles)

    #Return the number of wins to increase the percentage of wins to the next whole percent value and final winning percentage
    #params = {'b': int, 'w': int} and also WG-tags are supported
    def needWinWhole(self, params):
        if isinstance(params, dict):
            allBAT = params.get('b', 0) if 'b' in params else params.get(LONG_TAGS['b'], 0)
            allWIN = params.get('w', 0) if 'w' in params else params.get(LONG_TAGS['w'], 0)
            if allBAT:
                newWiR = int(100.0 * allWIN / allBAT) + 1
                battles = int(ceil((100.0 * allWIN - newWiR * allBAT) / (newWiR - 100))) if allWIN < allBAT and newWiR < 100 else 0
                return battles, 100.0 * (allWIN + battles) / (allBAT + battles)

    #Tank rating, based on https://koreanrandom.com/forum/topic/13386-
    #params = {'id':int, 'b':int, 'dmg':int, 'frg':int, 'spo':int, 'cap':int, 'def':int} and also WG-tags are supported
    def eff(self, params):
        if isinstance(params, dict):
            id      = params.get('id', 0) if 'id' in params else params.get(LONG_TAGS['id'], 0)
            allBAT  = params.get('b', 0) if 'b' in params else params.get(LONG_TAGS['b'], 0)
            allDMG  = params.get('dmg', 0) if 'dmg' in params else params.get(LONG_TAGS['dmg'], 0)
            allFRG  = params.get('frg', 0) if 'frg' in params else params.get(LONG_TAGS['frg'], 0)
            allSPO  = params.get('spo', 0) if 'spo' in params else params.get(LONG_TAGS['spo'], 0)
            allCAP  = params.get('cap', 0) if 'cap' in params else params.get(LONG_TAGS['cap'], 0)
            allDEF  = params.get('def', 0) if 'def' in params else params.get(LONG_TAGS['def'], 0)
            if id and allBAT:
                vehicle = vehicles.getVehicleType(int(id))
                if vehicle:
                    avgTIER = vehicle.level
                    avgDMG = float(allDMG) / allBAT
                    avgFRG = float(allFRG) / allBAT
                    avgSPO = float(allSPO) / allBAT
                    avgCAP = float(allCAP) / allBAT
                    avgDEF = float(allDEF) / allBAT
                    return 10*(0.23 + 2.0*avgTIER/100.0)/(avgTIER + 2.0)*avgDMG + 250*avgFRG + 150*avgSPO + 150*log(avgCAP + 1, 1.732) + 150*avgDEF

    #Tank rating, based on https://koreanrandom.com/forum/topic/13434-
    #params = {'id':int, 'b':int, 'w':int, 'dmg':int, 'frg':int, 'spo':int, 'def':int} and also WG-tags are supported
    def wn8(self, params):
        if isinstance(params, dict):
            id     = params.get('id', 0) if 'id' in params else params.get(LONG_TAGS['id'], 0)
            allBAT = params.get('b', 0) if 'b' in params else params.get(LONG_TAGS['b'], 0)
            allWIN = params.get('w', 0) if 'w' in params else params.get(LONG_TAGS['w'], 0)
            allDMG = params.get('dmg', 0) if 'dmg' in params else params.get(LONG_TAGS['dmg'], 0)
            allFRG = params.get('frg', 0) if 'frg' in params else params.get(LONG_TAGS['frg'], 0)
            allSPO = params.get('spo', 0) if 'spo' in params else params.get(LONG_TAGS['spo'], 0)
            allDEF = params.get('def', 0) if 'def' in params else params.get(LONG_TAGS['def'], 0)
            if id and allBAT:
                stat = g_Tables.wn8idsTable.get(int(id))
                if stat:
                    #Weighted values
                    weiWIR = 100 * float(allWIN) / (allBAT * stat['expWinRate'])
                    weiDAM =       float(allDMG) / (allBAT * stat['expDamage'])
                    weiFRG =       float(allFRG) / (allBAT * stat['expFrag'])
                    weiSPO =       float(allSPO) / (allBAT * stat['expSpot'])
                    weiDEF =       float(allDEF) / (allBAT * stat['expDef'])
                    #Normalized values
                    normWIR = max(0,                    (weiWIR - 0.71) / (1 - 0.71)  )
                    normDAM = max(0,                    (weiDAM - 0.22) / (1 - 0.22)  )
                    normFRG = max(0, min(normDAM + 0.2, (weiFRG - 0.12) / (1 - 0.12) ))
                    normSPO = max(0, min(normDAM + 0.1, (weiSPO - 0.38) / (1 - 0.38) ))
                    normDEF = max(0, min(normDAM + 0.1, (weiDEF - 0.10) / (1 - 0.10) ))
                    return 980*normDAM + 210*normDAM*normFRG + 155*normFRG*normSPO + 75*normDEF*normFRG + 145*min(1.8, normWIR)

    #Tank rating, based on https://koreanrandom.com/forum/topic/23829-
    #params = {'id':int, 'b':int, 'dmg':int, 'frg':int} and also WG-tags are supported
    def xte(self, params):
        if isinstance(params, dict):
            id     = params.get('id', 0) if 'id' in params else params.get(LONG_TAGS['id'], 0)
            allBAT = params.get('b', 0) if 'b' in params else params.get(LONG_TAGS['b'], 0)
            allDMG = params.get('dmg', 0) if 'dmg' in params else params.get(LONG_TAGS['dmg'], 0)
            allFRG = params.get('frg', 0) if 'frg' in params else params.get(LONG_TAGS['frg'], 0)
            if id and allBAT:
                stat = g_Tables.xteTable.get(str(id))
                if stat:
                    avgDMG = stat['ad']
                    avgFRG = stat['af']
                    diffDMG = float(allDMG) / allBAT - avgDMG
                    diffFRG = float(allFRG) / allBAT - avgFRG
                    normDMG = (1 + diffDMG / (stat['td'] - avgDMG)) if diffDMG >= 0 else (1 + diffDMG / (avgDMG - 0.4 * avgDMG))
                    normFRG = (1 + diffFRG / (stat['tf'] - avgFRG)) if diffFRG >= 0 else (1 + diffFRG / (avgFRG - 0.4 * avgFRG))
                    TEFF = 750*normDMG + 250*normFRG
                    index = next((i for i,x in enumerate(stat['x']) if x > TEFF), 100)
                    if index < 100:
                        if index == 0:
                            #Minimum is reached when dmg=frg=0, it corresponds normDMG=normFRG=-2/3 and TEFF = -2000/3 = -666.66(6)
                            if TEFF >= -666:
                                return (TEFF + 666) / (stat['x'][0] + 666)
                        else:
                            return index + (TEFF - stat['x'][index-1]) / (stat['x'][index] - stat['x'][index-1])
                    return float(index)

    #Tank rating, based on 'calculateXTDB' in "xvm_main\python\vehinfo.py"-module
    #params = {'id':int, 'b':int, 'dmg':int} and also WG-tags are supported
    def xtdb(self, params):
        if isinstance(params, dict):
            id     = params.get('id', 0) if 'id' in params else params.get(LONG_TAGS['id'], 0)
            allBAT = params.get('b', 0) if 'b' in params else params.get(LONG_TAGS['b'], 0)
            allDMG = params.get('dmg', 0) if 'dmg' in params else params.get(LONG_TAGS['dmg'], 0)
            if id and allBAT:
                stat = g_Tables.xtdbTable.get(str(id))
                if stat:
                    avgDMG = float(allDMG) / allBAT
                    index = next((i for i,x in enumerate(stat['x']) if x > avgDMG), 100)
                    if index < 100:
                        if index == 0:
                            if avgDMG > 0:
                                return avgDMG / stat['x'][0]
                        else:
                            return index + (avgDMG - stat['x'][index-1]) / (stat['x'][index] - stat['x'][index-1])
                    return float(index) 

    #Total rating by account
    #params = {'b':int, 'lvl':float, 'dmg':int, 'frg':int, 'spo':int, 'cap':int, 'def':int} and also WG-tags are supported
    def EFF(self, params):
        if isinstance(params, dict):
            allBAT  = params.get('b', 0) if 'b' in params else params.get(LONG_TAGS['b'], 0)
            avgTIER = params.get('lvl', 0) if 'lvl' in params else params.get(LONG_TAGS['lvl'], 0)
            allDMG  = params.get('dmg', 0) if 'dmg' in params else params.get(LONG_TAGS['dmg'], 0)
            allFRG  = params.get('frg', 0) if 'frg' in params else params.get(LONG_TAGS['frg'], 0)
            allSPO  = params.get('spo', 0) if 'spo' in params else params.get(LONG_TAGS['spo'], 0)
            allCAP  = params.get('cap', 0) if 'cap' in params else params.get(LONG_TAGS['cap'], 0)
            allDEF  = params.get('def', 0) if 'def' in params else params.get(LONG_TAGS['def'], 0)
            if allBAT and avgTIER:
                avgDMG = float(allDMG) / allBAT
                avgFRG = float(allFRG) / allBAT
                avgSPO = float(allSPO) / allBAT
                avgCAP = float(allCAP) / allBAT
                avgDEF = float(allDEF) / allBAT
                return 10*(0.23 + 2.0*avgTIER/100.0)/(avgTIER + 2.0)*avgDMG + 250*avgFRG + 150*avgSPO + 150*log(avgCAP + 1, 1.732) + 150*avgDEF

    #Total rating by account
    #params = {'b':int, 'w':int, 'dmg':int, 'frg':int, 'spo':int, 'def':int,
    #          'v': {'id':{'b':int, 'w':int, 'dmg':int, 'frg':int, 'spo':int, 'def':int}, 'id':{...}, ...}}
    def WN8(self, params):
        if isinstance(params, dict):
            allBAT = params.get('b', 0) if 'b' in params else params.get(LONG_TAGS['b'], 0)
            allWIN = params.get('w', 0) if 'w' in params else params.get(LONG_TAGS['w'], 0)
            allDMG = params.get('dmg', 0) if 'dmg' in params else params.get(LONG_TAGS['dmg'], 0)
            allFRG = params.get('frg', 0) if 'frg' in params else params.get(LONG_TAGS['frg'], 0)
            allSPO = params.get('spo', 0) if 'spo' in params else params.get(LONG_TAGS['spo'], 0)
            allDEF = params.get('def', 0) if 'def' in params else params.get(LONG_TAGS['def'], 0)
            allVeh = params.get('v', {}) if 'v' in params else params.get(LONG_TAGS['v'], {})
            if allBAT and allVeh:
                allBAT = sumWIN = sumDMG = sumFRG = sumSPO = sumDEF = expWIR = expDMG = expFRG = expSPO = expDEF = 0
                for id, stat in allVeh.items():
                    data = g_Tables.wn8idsTable.get(int(id))
                    if data:
                        idBAT = stat.get('b', 0) if 'b' in stat else stat.get(LONG_TAGS['b'], 0)
                        if idBAT:
                            allBAT += idBAT
                            sumWIN += stat.get('w', 0) if 'w' in stat else stat.get(LONG_TAGS['w'], 0)
                            sumDMG += stat.get('dmg', 0) if 'dmg' in stat else stat.get(LONG_TAGS['dmg'], 0)
                            sumFRG += stat.get('frg', 0) if 'frg' in stat else stat.get(LONG_TAGS['frg'], 0)
                            sumSPO += stat.get('spo', 0) if 'spo' in stat else stat.get(LONG_TAGS['spo'], 0)
                            sumDEF += stat.get('def', 0) if 'def' in stat else stat.get(LONG_TAGS['def'], 0)
                            expWIR += data['expWinRate'] * idBAT
                            expDMG += data['expDamage'] * idBAT
                            expFRG += data['expFrag'] * idBAT
                            expSPO += data['expSpot'] * idBAT
                            expDEF += data['expDef'] * idBAT
                if allBAT:
                    #Weighted values
                    weiWIR = 100 * float(sumWIN) / expWIR
                    weiDAM =       float(sumDMG) / expDMG
                    weiFRG =       float(sumFRG) / expFRG
                    weiSPO =       float(sumSPO) / expSPO
                    weiDEF =       float(sumDEF) / expDEF
                    #Normalized values
                    normWIR = max(0,                    (weiWIR - 0.71) / (1 - 0.71)  )
                    normDAM = max(0,                    (weiDAM - 0.22) / (1 - 0.22)  )
                    normFRG = max(0, min(normDAM + 0.2, (weiFRG - 0.12) / (1 - 0.12) ))
                    normSPO = max(0, min(normDAM + 0.1, (weiSPO - 0.38) / (1 - 0.38) ))
                    normDEF = max(0, min(normDAM + 0.1, (weiDEF - 0.10) / (1 - 0.10) ))
                    return 980*normDAM + 210*normDAM*normFRG + 155*normFRG*normSPO + 75*normDEF*normFRG + 145*min(1.8, normWIR)

    #Total rating by account
    #params = {'id': {'b':int, 'dmg': int, 'frg': int}, ...}
    def XTE(self, params):
        if isinstance(params, dict):
            typesBAT = {}
            typesUNP = {}
            LEVELS = range(1,11)
            for tag in vehicles.VEHICLE_CLASS_TAGS:
                typesBAT[tag] = {}
                typesUNP[tag] = {}
                for level in LEVELS:
                    typesBAT[tag][level] = typesUNP[tag][level] = 0
            for id, stat in params.items():
                allBAT = stat.get('b', 0) if 'b' in stat else stat.get(LONG_TAGS['b'], 0)
                allDMG = stat.get('dmg', 0) if 'dmg' in stat else stat.get(LONG_TAGS['dmg'], 0)
                allFRG = stat.get('frg', 0) if 'frg' in stat else stat.get(LONG_TAGS['frg'], 0)
                if allBAT >= 10 and allDMG and allFRG:
                    if 'id' not in stat:
                        stat['id'] = int(id)
                    xte = self.xte(stat)
                    vehicle = vehicles.getVehicleType(int(id))
                    if vehicle and xte:
                        tag = getVehicleClassTag(vehicle.tags)
                        typesBAT[tag][vehicle.level] += allBAT
                        typesUNP[tag][vehicle.level] += float(allBAT) / (100 - self.specificRating(xte, 'sup'))
            tags = finalUNP = 0
            for tag in typesBAT:
                levels = levelsUNP = 0
                for level in typesBAT[tag]:
                    if typesBAT[tag][level]:
                        levelsUNP += typesUNP[tag][level] * level / typesBAT[tag][level]
                        levels += level 
                if levels:
                    finalUNP += levelsUNP / levels
                    tags += 1
            return self.globalRating(100 - tags / finalUNP, 'sup', True) if finalUNP else 0.0

# Vars .......................................................................

#This is "Wargaming.net\WorldOfTanks\xvm\"-dir from the '_UserPrefs' in "xvm_main\python\userprefs.py"-module
CACHE_PATH = path.dirname(unicode(BigWorld.wg_getPreferencesFilePath(), 'utf-8', errors='ignore')) + '/xvm/' 

#"*.json.gz"-files in the cache-folder
g_Tables = _Tables()
g_Calculator = _Calculator()

if g_Tables.errorStatus:
    print '[%s] "rating_calculation": %s' % (__author__, g_Tables.errorStatus)