# -*- coding: utf-8 -*-

__author__  = 'StranikS_Scan'
__version__ = 'V1.4 P2.7 W0.9.22 20.02.2018'

import BigWorld
from Event import Event
import BattleReplay
from Avatar import PlayerAvatar
from PlayerEvents import g_playerEvents
from helpers import isPlayerAccount

from os import path, makedirs
from StringIO import StringIO
import json, gzip, cPickle, urllib2, threading
from math import log

# Consts .....................................................................

#API_VERSION in "xvm_main\python\consts.py"-module
API_VERSION = '4.0'

#SERVERS in "xvm_main\python\consts.py"-module
XVM_SERVER     = 'https://static.modxvm.com'
XVM_SERVER_API = 'https://stat.modxvm.com:443/{API}/{REQ}'

#Request a token from the server, example
#---> https://stat.modxvm.com/4.0/getToken/-/2365719
#{"status":"badToken"}
#---> https://stat.modxvm.com/4.0/getToken/a5257ae7-2e3a-368b-6a2c-b78e5f240f72/2365719
#{"_id":2365719,"expires_at":1516976873394,
# "services":{"statBattle":true,"statAwards":true,"statCompany":true,"comments":true,"chance":false,"chanceLive":false,"chanceResults":false,
#             "scale":"xvm","rating":"xte","topClansCount":50,"flag":"default","xmqp":true},
# "status":"active"}
XVM_GETTOKEN = XVM_SERVER_API.format(API=API_VERSION, REQ='getToken/{TOKEN}/{ID}')

#Get info by current version of XVM, example
#---> https://stat.modxvm.com:443/4.0/getVersionWithLimit/a5257ae7-2e3a-368b-6a2c-b78e5f240f72/2365719/50
#{"topClansWGM":{},
# "topClansWSH":{"KOPM2":{"cid":223790,"rank":1,"emblem":"http://stat.modxvm.com/emblems/top/{size}/223790.png"},...},
# "info":{"ver":"7.3.3","wot":"0.9.21.0.3","message":" • WoT 9.21.0.3\nПодробности на <a href='#XVM_SITE#'>официальном сайте XVM</a>"}}
XVM_GETVERSION = XVM_SERVER_API.format(API=API_VERSION, REQ='getVersionWithLimit/{TOKEN}/{ID}/50')

#Get stats for one player with all the tanks by a accountDBID, example:
#----> https://stat.modxvm.com/4.0/getStatsByID/a5257ae7-2e3a-368b-6a2c-b78e5f240f72/2365719
#{"b":19807,
# "e":1462,
# "v":{"63505":{"b":1,"w":0,"cap":0,"def":0,"dmg":52,"frg":0,"spo":0,"srv":0,"wtr":753}},
# "w":11594,
# "dt":"2018-01-30T00:52:23.465+00:00",
# "nm":"StranikS_Scan",
# "ts":1517273543000,"xp":null,"_id":2365719,"cap":38210,"cid":69731,"def":14537,"dmg":29176230,"frg":23928,"hip":71,"lvl":7.53855,
# "spo":22198,"srv":null,"wgr":8989,"wn8":2103,"wtr":6744,"flag":null,"lang":null,"dmg_r":null,"max_xp":null,
# "status":1,"max_dmg":null,"max_frg":null,"is_banned":null}
XVM_STATSBYID = XVM_SERVER_API.format(API=API_VERSION, REQ='getStatsByID/{TOKEN}/{ID}')

#The same, but with the help of the player's nickname, example:
#---> https://stat.modxvm.com/4.0/getStatsByNick/a5257ae7-2e3a-368b-6a2c-b78e5f240f72/RU/StranikS_Scan
#{"b":19807,
# "e":1462,
# "v":{"63505":{"b":1,"w":0,"cap":0,"def":0,"dmg":52,"frg":0,"spo":0,"srv":0,"wtr":753},...},
# "w":11594,
# "dt":"2018-01-30T00:52:23.465+00:00",
# "nm":"StranikS_Scan",
# "ts":1517273543000,"xp":null,"_id":2365719,"cap":38210,"cid":69731,"def":14537,"dmg":29176230,"frg":23928,"hip":71,"lvl":7.53855,
# "spo":22198,"srv":null,"wgr":8989,"wn8":2103,"wtr":6744,"flag":null,"lang":null,"dmg_r":null,"max_xp":null,
# "status":null,"max_dmg":null,"max_frg":null,"is_banned":null}
XVM_STATSBYNICK = XVM_SERVER_API.format(API=API_VERSION, REQ='getStatsByNick/{TOKEN}/{REGION}/{NICK}')

#Get statistics for a specific tank for one or multiple users, example:
#---> https://stat.modxvm.com/4.0/getStats/a5257ae7-2e3a-368b-6a2c-b78e5f240f72/2365719=54529,4100782=51841
#{"players":[{"b":19807,
#             "e":1462,
#             "r":8989,
#             "v":{"b":331,"w":202,"cap":1159,"def":286,"dmg":98371,"frg":592,"spo":459,"srv":122,"wtr":2919},
#             "w":11594,
#             "nm":"StranikS_Scan",
#             "ts":1517273543465,"xp":null,"_id":2365719,"cap":38210,"cid":69731,"def":14537,"dmg":29176230,"frg":23928,"hip":71,"lvl":7.53855,
#             "spo":22198,"srv":null,"wgr":8989,"wn8":2103,"wtr":6744,"flag":null,"lang":null,"dmg_r":null,"max_xp":null,"status":1,"max_dmg":null,"max_frg":null,"is_banned":null},
#            {"b":39441,
#             "e":881,
#             "r":4981,
#             "v":{"b":40,"w":20,"xp":6367,"cap":0,"def":0,"dmg":2682,"frg":13,"mom":3,"spo":35,"srv":7,"wtr":2642},
#             "w":19317,
#             "nm":"JM71",
#             "ts":1517552268047,"xp":14205000,"_id":4100782,"cap":24261,"cid":null,"def":22125,"dmg":33753828,"frg":26228,"hip":51,"lvl":7.27749,
#             "spo":40334,"srv":8651,"wgr":4981,"wn8":1082,"wtr":4186,"flag":null,"lang":null,"dmg_r":25312886,"max_xp":2306,"status":null,"max_dmg":6392,"max_frg":8,"is_banned":null}]}
XVM_STATS       = XVM_SERVER_API.format(API=API_VERSION, REQ='getStats/{TOKEN}/{DICT}')
XVM_STATSREPLAY = XVM_SERVER_API.format(API=API_VERSION, REQ='getStatsReplay/{TOKEN}/{DICT}')

#Get online WOT-server statistics
#---> https://stat.modxvm.com/4.0/getOnlineUsersCount/a5257ae7-2e3a-368b-6a2c-b78e5f240f72
#{"ru":[{"players_online":17522,"server":"RU8"},...],
# "asia":[{"players_online":2353,"server":"501"}],
# "eu":[{"players_online":73905,"server":"EU2"},...],
# "na":[{"players_online":10146,"server":"303"},{"players_online":1859,"server":"304"}]}
XVM_ONLINE = XVM_SERVER_API.format(API=API_VERSION, REQ='getOnlineUsersCount/{TOKEN}')

#{'xwgr': [1361, ...], 'xeff': [378, ...], 'xwn8': [56,...], 'xwin': [43.44, ...], 'xwtr': [1409, ...]}
TABLE_XVMSCALE = XVM_SERVER + '/xvmscales.json.gz'
#{'header': {'url': 'https://...', 'source': 'XVM', 'version': '2018-02-12'},
# 'data': [{'expDamage': 1079.886, 'expSpot': 0.769, 'IDNum': 55297, 'expWinRate': 52.995, 'expDef': 0.881, 'expFrag': 1.146}, ...]}
TABLE_WN8 = XVM_SERVER + '/wn8-data-exp/json/wn8exp.json.gz'
#{'62737': {'tf': 1.64, 'x': [342, ...], 'td': 2168, 'ad': 1171, 'af': 0.78}, ...}
TABLE_XTE = XVM_SERVER + '/xte.json.gz'
#{'62737': {'tf': 1.64, 'x': [726, ...], 'td': 2168, 'ad': 1171, 'af': 0.78}, ...}
TABLE_XTDB = XVM_SERVER + '/xtdb.json.gz'

# Static functions ***********************************************************

def _loadUrl(request):
    try:
        response = urllib2.urlopen(request)
        if response.code == 200:
            return response.read()
    except:
        pass

def _loadJsonUrl(request):
    stats = _loadUrl(request)
    if stats:
        try:
            stats = json.loads(stats)
        except:
            pass
        else:
            if isinstance(stats, dict):
                return stats if stats.get('status', '') not in ['badRequest', 'badToken'] else {}

# Classes ====================================================================

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

    #Based on https://koreanrandom.com/forum/topic/13434-
    #params = {'id':int, 'b':int, 'w':int, 'dmg':int, 'frg':int, 'spo':int, 'def':int}
    def wn8(self, params):
        if isinstance(params, dict):
            id     = params.get('id')
            allBAT = params.get('b', 0)
            allWIN = params.get('w', 0)
            allDMG = params.get('dmg', 0)
            allFRG = params.get('frg', 0)
            allSPO = params.get('spo', 0)
            allDEF = params.get('def', 0)
            if id is not None and allBAT:
                stat = g_Tables.wn8idsTable.get(id)
                if stat:
                    #Weighted values
                    weiWIN = 100 * float(allWIN) / (allBAT * stat['expWinRate'])
                    weiDAM =       float(allDMG) / (allBAT * stat['expDamage'])
                    weiFRG =       float(allFRG) / (allBAT * stat['expFrag'])
                    weiSPO =       float(allSPO) / (allBAT * stat['expSpot'])
                    weiDEF =       float(allDEF) / (allBAT * stat['expDef'])
                    #Normalized values
                    normWIN = max(0,                    (weiWIN - 0.71) / (1 - 0.71)  )
                    normDAM = max(0,                    (weiDAM - 0.22) / (1 - 0.22)  )
                    normFRG = max(0, min(normDAM + 0.2, (weiFRG - 0.12) / (1 - 0.12) ))
                    normSPO = max(0, min(normDAM + 0.1, (weiSPO - 0.38) / (1 - 0.38) ))
                    normDEF = max(0, min(normDAM + 0.1, (weiDEF - 0.10) / (1 - 0.10) ))
                    return 980*normDAM + 210*normDAM*normFRG + 155*normFRG*normSPO + 75*normDEF*normFRG + 145*min(1.8, normWIN)

    #Based on https://koreanrandom.com/forum/topic/23829-
    #params = {'id':int, 'b':int, 'dmg':int, 'frg':int}
    def xte(self, params):
        if isinstance(params, dict):
            id     = params.get('id')
            allBAT = params.get('b', 0)
            allDMG = params.get('dmg', 0)
            allFRG = params.get('frg', 0)
            if id is not None and allBAT:
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

    #Based on 'calculateXTDB' in "xvm_main\python\vehinfo.py"-module
    #params = {'id':int, 'b':int, 'dmg':int}
    def xtdb(self, params):
        if isinstance(params, dict):
            id     = params.get('id')
            allBAT = params.get('b', 0)
            allDMG = params.get('dmg', 0)
            if id is not None and allBAT:
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

    #Based on https://koreanrandom.com/forum/topic/13386-
    #params = {'b':int, 'avglvl':float, 'dmg':int, 'frg':int, 'spo':int, 'cap':int, 'def':int}
    def eff(self, params):
        if isinstance(params, dict):
            allBAT  = params.get('b', 0)
            avgTIER = params.get('avglvl', 0.0)
            allDMG  = params.get('dmg', 0)
            allFRG  = params.get('frg', 0)
            allSPO  = params.get('spo', 0)
            allCAP  = params.get('cap', 0)
            allDEF  = params.get('def', 0)
            if allBAT and avgTIER:
                avgDMG = float(allDMG) / allBAT
                avgFRG = float(allFRG) / allBAT
                avgSPO = float(allSPO) / allBAT
                avgCAP = float(allCAP) / allBAT
                avgDEF = float(allDEF) / allBAT
                return 10*(0.23 + 2.0*avgTIER/100.0)/(avgTIER + 2.0)*avgDMG + 250*avgFRG + 150*avgSPO + 150*log(avgCAP + 1, 1.732) + 150*avgDEF

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
        content = _loadUrl(url)
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

class TOKEN_ERRORS:
    OK              = 0
    NEED_LOGIN      = 1
    NEED_ACTIVATION = 2
    NOT_CONNECTION  = 3

#Based on the code from:
# '_UserPrefs' in "xvm_main\python\userprefs.py"-module
# 'XvmServicesToken' in "xvm_main\python\config.py"-module
class _UserToken(object):
    errorStatus = property(lambda self: self.__getErrorStatus())
    accountDBID = property(lambda self: self.__accountDBID)
    userToken   = property(lambda self: self.__userToken)

    def __init__(self):
        self.__error = TOKEN_ERRORS.OK
        self.__userToken = ''
        self.__accountDBID = None
        self.init()

    def init(self):
        self.__error = TOKEN_ERRORS.OK
        self.__userToken = ''
        self.__accountDBID = self.__getAccountDBID()
        if self.__accountDBID:
            self.__saveAccountDBID()
            self.__tokensBase = self.__getTokensBase()
            #V1. Сheck for a new token on the server
            stats = _loadJsonUrl(XVM_GETTOKEN.format(TOKEN='-', ID=self.__accountDBID))
            if stats is None:
                self.__error = TOKEN_ERRORS.NOT_CONNECTION
                return
            elif stats:
                self.__userToken = stats.get('token','')
                if self.__userToken:
                    self.__saveLocalToken()
            #V2. Search and check the token in the local database for use without activation on the website
            if not self.__userToken:
                self.__userToken = self.__tokensBase.get(self.__accountDBID, '')
                if self.__userToken:
                    stats = _loadJsonUrl(XVM_GETTOKEN.format(TOKEN=self.__userToken, ID=self.__accountDBID))
                    if stats is None:
                        self.__error = TOKEN_ERRORS.NOT_CONNECTION
                    elif not stats or stats.get('status', None) in [None, 'inactive']:
                        self.__userToken = ''
            #V3. Search and check the token from the cache
            if not self.__userToken:
                self.__userToken = self.__getLocalToken()
                if self.__userToken:
                    stats = _loadJsonUrl(XVM_GETTOKEN.format(TOKEN=self.__userToken, ID=self.__accountDBID))
                    if stats is None:
                        self.__error = TOKEN_ERRORS.NOT_CONNECTION
                    elif not stats or stats.get('status', None) in [None, 'inactive']:
                        self.__error = TOKEN_ERRORS.NEED_ACTIVATION
                else:
                    self.__error = TOKEN_ERRORS.NEED_ACTIVATION
            #Save the token in the local database
            if self.__error == TOKEN_ERRORS.OK and self.__userToken:
                self.__tokensBase[self.__accountDBID] = self.__userToken
                self.__saveTokensBase()
        else:
            self.__error = TOKEN_ERRORS.NEED_LOGIN

    def __getAccountDBID(self):
        accountDBID = getattr(BigWorld.player(), 'databaseID', None) if not BattleReplay.isPlaying() else None
        if accountDBID is None:
            accountDBID = CACHE_PATH + 'tokens/lastAccountDBID.dat'
            if path.exists(accountDBID):
                try:
                    with open(accountDBID, 'rb') as f:
                        return cPickle.loads(f.read())
                except:
                    pass

    def __saveAccountDBID(self):
        filename = CACHE_PATH + 'tokens/lastAccountDBID.dat'
        dirname = path.dirname(filename)
        try:
            if not path.exists(dirname):
                makedirs(dirname)
            with open(filename, 'wb') as f:
                f.write(cPickle.dumps(self.__accountDBID))
            return True
        except:
            pass
        return False

    def __getTokensBase(self):
        tokensBase = CACHE_PATH + 'tokens/tokensBase.dat'
        if path.exists(tokensBase):
            try:
                with open(tokensBase, 'rb') as f:
                    return cPickle.loads(f.read())
            except:
                pass
        return {}

    def __saveTokensBase(self):
        filename = CACHE_PATH + 'tokens/tokensBase.dat'
        dirname = path.dirname(filename)
        try:
            if not path.exists(dirname):
                makedirs(dirname)
            with open(filename, 'wb') as f:
                f.write(cPickle.dumps(self.__tokensBase))
            return True
        except:
            pass
        return False

    def __getLocalToken(self):
        localToken = CACHE_PATH + 'tokens/%d.dat' % self.__accountDBID
        if path.exists(localToken):
            try:
                with open(localToken, 'rb') as f:
                    localToken = cPickle.loads(f.read())
                return localToken.get('token','') if isinstance(localToken, dict) else ''
            except:
                pass
        return ''

    def __saveLocalToken(self):
        filename = CACHE_PATH + 'tokens/%d.dat' % self.__accountDBID
        dirname = path.dirname(filename)
        try:
            if not path.exists(dirname):
                makedirs(dirname)
            userToken = {}
            if path.exists(filename):
                try:
                    with open(filename, 'rb') as f:
                        localToken = cPickle.loads(f.read())
                        if isinstance(localToken, dict):
                            userToken = localToken
                except:
                    pass
            userToken['accountDBID'] = self.__accountDBID
            userToken['token']       = self.__userToken
            with open(filename, 'wb') as f:
                f.write(cPickle.dumps(userToken))
            return True
        except:
            pass
        return False

    def __getErrorStatus(self):
        if self.__error == TOKEN_ERRORS.NEED_LOGIN:
            return 'You need to be logged in once for authorization!'
        elif self.__error == TOKEN_ERRORS.NEED_ACTIVATION:
            return 'Requires activation on the XVM-site (https://modxvm.com/)!'
        elif self.__error == TOKEN_ERRORS.NOT_CONNECTION:
            return 'No connection to the XVM-server!'        
        return ''

#Sending typical requests to the XVM-server
class _XVMConsole(object):
    def __init__(self):
        self.OnAsyncReports = Event()

    def __prepareRequest(self, async, url, onAsyncReport):
        if async:
            thread = threading.Thread(target=self.__sendRequest, args=[async, url, onAsyncReport])
            thread.setDaemon(True)
            thread.start()
        else:
            return self.__sendRequest(async, url, None)

    def __sendRequest(self, async, url, onAsyncReport):
        stats = _loadJsonUrl(url)
        if async:
            if onAsyncReport:
                onAsyncReport(stats)
            else:
                self.OnAsyncReports(stats)
        return stats

    def getVersionWithLimit(self):
        if g_UserToken.accountDBID and g_UserToken.userToken:
            return self.__prepareRequest(False, XVM_GETVERSION.format(TOKEN=g_UserToken.userToken, ID=g_UserToken.accountDBID), None)

    def getVersionWithLimit_Async(self, onAsyncReport=None):
        if g_UserToken.accountDBID and g_UserToken.userToken:
            return self.__prepareRequest(True, XVM_GETVERSION.format(TOKEN=g_UserToken.userToken, ID=g_UserToken.accountDBID), onAsyncReport)

    #accountDBID=2365719
    def getStatsByID(self, accountDBID):
        if g_UserToken.userToken:
            return self.__prepareRequest(False, XVM_STATSBYID.format(TOKEN=g_UserToken.userToken, ID=accountDBID), None)

    def getStatsByID_Async(self, accountDBID, onAsyncReport=None):
        if g_UserToken.userToken:
            return self.__prepareRequest(True, XVM_STATSBYID.format(TOKEN=g_UserToken.userToken, ID=accountDBID), onAsyncReport)

    #region='RU', nick='StranikS_Scan'
    def getStatsByNick(self, region, nick):
        if g_UserToken.userToken:
            return self.__prepareRequest(False, XVM_STATSBYNICK.format(TOKEN=g_UserToken.userToken, REGION=region, NICK=nick), None)

    def getStatsByNick_Async(self, region, nick, onAsyncReport=None):
        if g_UserToken.userToken:
            return self.__prepareRequest(True, XVM_STATSBYNICK.format(TOKEN=g_UserToken.userToken, REGION=region, NICK=nick), onAsyncReport)

    #See "_load_stat" in xvm_main\python\stats.py
    #ids={2365719:54529, 4100782:51841, accountDBID:compactDescr, ...}
    def getStats(self, ids):
        if g_UserToken.userToken and ids:
            requestList = []
            replay = BattleReplay.isPlaying()
            for accountDBID, vehCD in ids.items():
                if vehCD != 65281:
                    requestList.append('%d=%d%s' % (accountDBID, vehCD, '=1' if not replay and accountDBID == g_UserToken.accountDBID else ''))
            ids = ','.join(requestList)
            url = XVM_STATSREPLAY.format(TOKEN=g_UserToken.userToken, DICT=ids) if replay else XVM_STATS.format(TOKEN=g_UserToken.userToken, DICT=ids)
            return self.__prepareRequest(False, url, None)

    def getStats_Async(self, ids, onAsyncReport=None):
        if g_UserToken.userToken and ids:
            requestList = []
            replay = BattleReplay.isPlaying()
            for accountDBID, vehCD in ids.items():
                if vehCD != 65281:
                    requestList.append('%d=%d%s' % (accountDBID, vehCD, '=1' if not replay and accountDBID == g_UserToken.accountDBID else ''))
            ids = ','.join(requestList)
            url = XVM_STATSREPLAY.format(TOKEN=g_UserToken.userToken, DICT=ids) if replay else XVM_STATS.format(TOKEN=g_UserToken.userToken, DICT=ids)
            return self.__prepareRequest(True, url, onAsyncReport)

    def getOnlineUsersCount(self):
        if g_UserToken.userToken:
            return self.__prepareRequest(False, XVM_ONLINE.format(TOKEN=g_UserToken.userToken), None)

    def getOnlineUsersCount_Async(self, onAsyncReport=None):
        if g_UserToken.userToken:
            return self.__prepareRequest(True, XVM_ONLINE.format(TOKEN=g_UserToken.userToken), onAsyncReport)

class _XVMStatisticsEvents(object):
    def __init__(self):
        self.OnStatsAccountBecomePlayer = Event()
        self.OnStatsBattleLoaded        = Event()

# Vars .......................................................................

#This is "Wargaming.net\WorldOfTanks\xvm\"-dir from the '_UserPrefs' in "xvm_main\python\userprefs.py"-module
CACHE_PATH = path.dirname(unicode(BigWorld.wg_getPreferencesFilePath(), 'utf-8', errors='ignore')) + '/xvm/' 

g_Calculator          = _Calculator()
#'token' in "<token>.dat"-file from the cache-folder
g_UserToken           = _UserToken()
#"*.json.gz"-files in the cache-folder
g_Tables              = _Tables()
g_XVMConsole          = _XVMConsole()
g_XVMStatisticsEvents = _XVMStatisticsEvents()

# Hooks ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

def new__startGUI(self):
    old__startGUI(self)
    if g_XVMStatisticsEvents.OnStatsBattleLoaded._Event__delegates:
        ids = {}
        for vID, vData in self.arena.vehicles.iteritems():
            vehCD = None
            if 'typeCompDescr' in vData:
                vehCD = vData['typeCompDescr']
            elif 'vehicleType' in vData:
                vtype = vData['vehicleType']
                if hasattr(vtype, 'type'):
                    vehCD = vData['vehicleType'].type.compactDescr
            if vehCD is None:
                vehCD = 0
            ids[vData['accountDBID']] = vehCD
        if ids:
            g_XVMConsole.getStats_Async(ids, g_XVMStatisticsEvents.OnStatsBattleLoaded)

def addStatsAccountBecomePlayer():
    if isPlayerAccount():
        if getattr(BigWorld.player(), 'databaseID', None) is None:
            BigWorld.callback(0.2, addStatsAccountBecomePlayer)
        else:
            g_UserToken.init()
            if g_UserToken.errorStatus:
                print '[%s] XVMStatistics: %s' % (__author__, g_UserToken.errorStatus)
            elif g_XVMStatisticsEvents.OnStatsAccountBecomePlayer._Event__delegates:
                g_XVMConsole.getStatsByID_Async(g_UserToken.accountDBID, g_XVMStatisticsEvents.OnStatsAccountBecomePlayer)

old__startGUI = PlayerAvatar._PlayerAvatar__startGUI
PlayerAvatar._PlayerAvatar__startGUI = new__startGUI

g_playerEvents.onAccountBecomePlayer += addStatsAccountBecomePlayer

print '[%s] Loading mod: XVMStatistics %s (http://www.koreanrandom.com)' % (__author__, __version__)

if g_Tables.errorStatus:
    print '[%s] XVMStatistics: %s' % (__author__, g_Tables.errorStatus)
