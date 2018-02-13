# -*- coding: utf-8 -*-

__author__  = 'StranikS_Scan'
__version__ = 'V1.2 P2.7 W0.9.22 13.02.2018'

import BigWorld
from Event import Event
import BattleReplay
from Avatar import PlayerAvatar
from PlayerEvents import g_playerEvents
from helpers import isPlayerAccount

from os import path, makedirs
from StringIO import StringIO
import json, gzip, cPickle, urllib2, threading

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

TABLE_XVMSCALE = XVM_SERVER + '/xvmscales.json.gz'
TABLE_WN8      = XVM_SERVER + '/wn8-data-exp/json/wn8exp.json.gz'
TABLE_XTE      = XVM_SERVER + '/xte.json.gz'
TABLE_XTDB     = XVM_SERVER + '/xtdb.json.gz'

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

class TABLE_ERRORS:
    OK          = 0
    NOT_READED  = 1
    NOT_UPDATED = 2

#Based on then code from vehinfo.py
class _Tables(object):
    errorStatus   = property(lambda self: self.__getErrorStatus())
    xvmscaleTable = property(lambda self: self.__xvmscale)
    wn8Table      = property(lambda self: self.__wn8)
    xteTable      = property(lambda self: self.__xte)
    xtdbTable     = property(lambda self: self.__xtdb)

    def __init__(self):
        self.__error = TABLE_ERRORS.OK
        self.__xvmscale_filename = CACHE_PATH + 'cache/' + path.basename(TABLE_XVMSCALE) + '.dat'
        self.__wn8_filename      = CACHE_PATH + 'cache/' + path.basename(TABLE_WN8) + '.dat'
        self.__xte_filename      = CACHE_PATH + 'cache/' + path.basename(TABLE_XTE) + '.dat'
        self.__xtdb_filename     = CACHE_PATH + 'cache/' + path.basename(TABLE_XTDB) + '.dat'
        self.init()

    def init(self):
        self.__xvmscale = \
        self.__wn8      = \
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