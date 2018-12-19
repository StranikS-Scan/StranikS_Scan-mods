# -*- coding: utf-8 -*-

__author__  = 'StranikS_Scan'
__version__ = 'V2.0 P2.7 W1.2.0 07.12.2018'

import BigWorld
from Event import Event
import BattleReplay
from Avatar import PlayerAvatar
from PlayerEvents import g_playerEvents
from avatar_helpers import getAvatarDatabaseID
from helpers import isPlayerAccount
from constants import CURRENT_REALM, DEFAULT_LANGUAGE

from os import path, makedirs
import cPickle, threading

from http_methods import loadJsonUrl
from time import sleep

# Consts .....................................................................

#API_VERSION in "xvm_main\python\consts.py"-module
API_VERSION = '4.0'
#SERVERS in "xvm_main\python\consts.py"-module
XVM_SERVER_API = 'https://stat.modxvm.com:443/{API}/{REQ}'

#Different regions
REGION_RU = 'RU'
REGION_EU = 'EU'
REGION_NA = 'NA'
REGION_AS = 'ASIA'

#Request a token from the server, example:
#---> https://stat.modxvm.com/4.0/getToken/-/2365719
#{"status":"badToken"}
#---> https://stat.modxvm.com/4.0/getToken/a5257ae7-2e3a-368b-6a2c-b78e5f240f72/2365719
#{"_id":2365719,"expires_at":1516976873394,
# "services":{"statBattle":true,"statAwards":true,"statCompany":true,"comments":true,"chance":false,"chanceLive":false,"chanceResults":false,
#             "scale":"xvm","rating":"xte","topClansCount":50,"flag":"default","xmqp":true},
# "status":"active"}
XVM_GETTOKEN = XVM_SERVER_API.format(API=API_VERSION, REQ='getToken/{TOKEN}/{ID}')

#Get info by current version of XVM, example:
#---> https://stat.modxvm.com:443/4.0/getVersionWithLimit/a5257ae7-2e3a-368b-6a2c-b78e5f240f72/2365719/50
#{"topClansWGM":{},
# "topClansWSH":{"KOPM2":{"cid":223790,"rank":1,"emblem":"http://stat.modxvm.com/emblems/top/{size}/223790.png"},...},
# "info":{"ver":"7.3.3","wot":"0.9.21.0.3","message":" • WoT 9.21.0.3\nПодробности на <a href='#XVM_SITE#'>официальном сайте XVM</a>"}}
XVM_GETVERSION = XVM_SERVER_API.format(API=API_VERSION, REQ='getVersionWithLimit/{TOKEN}/{ID}/50')

#Get stats for one player with all the tanks by a accountDBID, example:
#----> https://stat.modxvm.com/4.0/getStatsByID/a5257ae7-2e3a-368b-6a2c-b78e5f240f72/2365719
#{"b":19807,
# "e":1462,
# "v":{"63505":{"b":1,"w":0,"cap":0,"def":0,"dmg":52,"frg":0,"spo":0,"srv":0,"wtr":753,"id":63505}},
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
# "v":{"63505":{"b":1,"w":0,"cap":0,"def":0,"dmg":52,"frg":0,"spo":0,"srv":0,"wtr":753,"id":63505},...},
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
#             "v":{"b":331,"w":202,"cap":1159,"def":286,"dmg":98371,"frg":592,"spo":459,"srv":122,"wtr":2919,"id":63505},
#             "w":11594,
#             "nm":"StranikS_Scan",
#             "ts":1517273543465,"xp":null,"_id":2365719,"cap":38210,"cid":69731,"def":14537,"dmg":29176230,"frg":23928,"hip":71,"lvl":7.53855,
#             "spo":22198,"srv":null,"wgr":8989,"wn8":2103,"wtr":6744,"flag":null,"lang":null,"dmg_r":null,"max_xp":null,"status":1,"max_dmg":null,"max_frg":null,"is_banned":null},
#            {"b":39441,
#             "e":881,
#             "r":4981,
#             "v":{"b":40,"w":20,"xp":6367,"cap":0,"def":0,"dmg":2682,"frg":13,"mom":3,"spo":35,"srv":7,"wtr":2642,"id":63505},
#             "w":19317,
#             "nm":"JM71",
#             "ts":1517552268047,"xp":14205000,"_id":4100782,"cap":24261,"cid":null,"def":22125,"dmg":33753828,"frg":26228,"hip":51,"lvl":7.27749,
#             "spo":40334,"srv":8651,"wgr":4981,"wn8":1082,"wtr":4186,"flag":null,"lang":null,"dmg_r":25312886,"max_xp":2306,"status":null,"max_dmg":6392,"max_frg":8,"is_banned":null}]}
XVM_STATS       = XVM_SERVER_API.format(API=API_VERSION, REQ='getStats/{TOKEN}/{DICT}')
XVM_STATSREPLAY = XVM_SERVER_API.format(API=API_VERSION, REQ='getStatsReplay/{TOKEN}/{DICT}')

#Get online WOT-server statistics, example:
#---> https://stat.modxvm.com/4.0/getOnlineUsersCount/a5257ae7-2e3a-368b-6a2c-b78e5f240f72
#{"ru":[{"players_online":17522,"server":"RU8"},...],
# "asia":[{"players_online":2353,"server":"501"}],
# "eu":[{"players_online":73905,"server":"EU2"},...],
# "na":[{"players_online":10146,"server":"303"},{"players_online":1859,"server":"304"}]}
XVM_ONLINE = XVM_SERVER_API.format(API=API_VERSION, REQ='getOnlineUsersCount/{TOKEN}')

# Static functions ***********************************************************

def _userRegion(accountDBID):
    return REGION_RU if accountDBID < 500000000 else REGION_EU if accountDBID < 1000000000 else REGION_NA if accountDBID < 2000000000 else REGION_AS

# Classes ====================================================================

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
            stats = loadJsonUrl(XVM_GETTOKEN.format(TOKEN='-', ID=self.__accountDBID))
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
                    stats = loadJsonUrl(XVM_GETTOKEN.format(TOKEN=self.__userToken, ID=self.__accountDBID))
                    if stats is None:
                        self.__error = TOKEN_ERRORS.NOT_CONNECTION
                    elif not stats or stats.get('status', None) in [None, 'inactive']:
                        self.__userToken = ''
            #V3. Search and check the token from the cache
            if not self.__userToken:
                self.__userToken = self.__getLocalToken()
                if self.__userToken:
                    stats = loadJsonUrl(XVM_GETTOKEN.format(TOKEN=self.__userToken, ID=self.__accountDBID))
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
        else:
            return accountDBID

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
            return 'Requires activation on the XVM-site (https://modxvm.com/) and restart the game client!'
        elif self.__error == TOKEN_ERRORS.NOT_CONNECTION:
            return 'No connection to the XVM-server!'        
        return ''

#Determines the home region of the game client or authorized player
class _HomeRegion(object):
    homeRegion  = property(lambda self: self.__homeRegion)
    accountDBID = property(lambda self: self.__accountDBID)

    def __init__(self):
        self.__accountDBID = 0
        self.__homeRegion = REGION_RU if CURRENT_REALM == 'RU' else REGION_EU if CURRENT_REALM == 'EU' else \
                            REGION_NA if CURRENT_REALM == 'NA' else REGION_AS if CURRENT_REALM in ('ASIA', 'CN', 'KR') else \
                            REGION_RU if DEFAULT_LANGUAGE == 'ru' else REGION_NA

    def setAccountDBID(self, accountDBID):
        if accountDBID:
            self.__accountDBID = accountDBID
            self.__homeRegion = _userRegion(self.__accountDBID)
            return True
        self.__accountDBID = 0
        return False

#Sending typical requests to the XVM-server
class _XVMConsole(object):
    def __init__(self):
        self.OnAsyncReports = Event()
        self.__timeDelay = 0.5

    def __prepareRequest(self, async, url, onAsyncReport=None):
        if async:
            thread = threading.Thread(target=self.__sendRequest, args=[async, url, onAsyncReport])
            thread.setDaemon(True)
            thread.start()
        else:
            return self.__sendRequest(async, url, None)

    def __sendRequest(self, async, url, onAsyncReport):
        answer = loadJsonUrl(url)
        if async:
            if onAsyncReport:
                onAsyncReport(answer)
            else:
                self.OnAsyncReports(answer)
        return answer

    def getVersion(self):
        if g_UserToken.accountDBID and g_UserToken.userToken:
            return self.__prepareRequest(False, XVM_GETVERSION.format(TOKEN=g_UserToken.userToken, ID=g_UserToken.accountDBID))

    def getOnlineUsersCount(self):
        if g_UserToken.userToken:
            return self.__prepareRequest(False, XVM_ONLINE.format(TOKEN=g_UserToken.userToken))

    def __prepareStatsByParamsRequest(self, async, params, onAsyncReport, timeout):
        if async:
            thread = threading.Thread(target=self.__sendStatsByParamsRequest, args=[async, params, onAsyncReport, timeout])
            thread.setDaemon(True)
            thread.start()
        else:
            return self.__sendStatsByParamsRequest(async, params, None, timeout)

    def __sendQuery(self, query, players, timeout):
        answer = None
        while not answer and timeout >= 0:
            answer = loadJsonUrl(query)
            if not answer:
                timeout -= self.__timeDelay
                sleep(self.__timeDelay)
        if answer:
            if 'v' in answer and answer['v']:
                vehicle = answer['v']
                for id in vehicle:
                    vehicle[id]['id'] = id
            players['players'].append(answer)

    def __sendStatsByParamsRequest(self, async, params, onAsyncReport, timeout):
        players = {'players': []}
        if len(params) == 3:
            XVM_QUERY, tags, region = params
        else:
            XVM_QUERY, tags = params
        threads = []
        for tag in tags:
            thread = threading.Thread(target=self.__sendQuery, args=[XVM_QUERY.format(TOKEN=g_UserToken.userToken, ID=tag) if XVM_QUERY == XVM_STATSBYID else \
                                                                     XVM_QUERY.format(TOKEN=g_UserToken.userToken, REGION=region, NICK=tag), players, timeout])
            thread.setDaemon(True)
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()
        if async:
            if onAsyncReport:
                onAsyncReport(players)
            else:
                self.OnAsyncReports(players)
        return players

    #IDs=[2365719, 34483, accountDBID, ...] or 2365719 only
    def getStatsByID(self, IDs, timeout=5.0):
        if g_UserToken.userToken and IDs:
            if isinstance(IDs, int):
                IDs = [IDs]
            return self.__prepareStatsByParamsRequest(False, [XVM_STATSBYID, IDs], None, timeout)

    def getStatsByID_Async(self, IDs, onAsyncReport=None, timeout=5):
        if g_UserToken.userToken and IDs:
            if isinstance(IDs, int):
                IDs = [IDs]
            self.__prepareStatsByParamsRequest(True, [XVM_STATSBYID, IDs], onAsyncReport, timeout)
        elif onAsyncReport:
            onAsyncReport(None)
        else:
            self.OnAsyncReports(None)

    #nicknames = ['Straik','MeeGo'] or 'Straik' only; region='RU' 
    def getStatsByNick(self, nicknames, region='', timeout=5.0):
        if g_UserToken.userToken and nicknames:
            if isinstance(nicknames, str):
                nicknames = [nicknames]
            if not region:
                region = g_HomeRegion.homeRegion
            return self.__prepareStatsByParamsRequest(False, [XVM_STATSBYNICK, nicknames, region], None, timeout)

    def getStatsByNick_Async(self, nicknames, region='', onAsyncReport=None, timeout=5):
        if g_UserToken.userToken and nicknames:
            if isinstance(nicknames, str):
                nicknames = [nicknames]
            if not region:
                region = g_HomeRegion.homeRegion
            self.__prepareStatsByParamsRequest(True, [XVM_STATSBYNICK, nicknames, region], onAsyncReport, timeout)
        elif onAsyncReport:
            onAsyncReport(None)
        else:
            self.OnAsyncReports(None)

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
            return self.__prepareRequest(False, XVM_STATSREPLAY.format(TOKEN=g_UserToken.userToken, DICT=ids) if replay else \
                                                XVM_STATS.format(TOKEN=g_UserToken.userToken, DICT=ids))

    def getStats_Async(self, ids, onAsyncReport=None):
        if g_UserToken.userToken and ids:
            requestList = []
            replay = BattleReplay.isPlaying()
            for accountDBID, vehCD in ids.items():
                if vehCD != 65281:
                    requestList.append('%d=%d%s' % (accountDBID, vehCD, '=1' if not replay and accountDBID == g_UserToken.accountDBID else ''))
            ids = ','.join(requestList) 
            self.__prepareRequest(True, XVM_STATSREPLAY.format(TOKEN=g_UserToken.userToken, DICT=ids) if replay else \
                                        XVM_STATS.format(TOKEN=g_UserToken.userToken, DICT=ids), onAsyncReport)
        elif onAsyncReport:
            onAsyncReport(None)
        else:
            self.OnAsyncReports(None)

class _XVMStatisticsEvents(object):
    def __init__(self):
        self.OnStatsAccountBecomePlayer = Event()
        self.OnStatsBattleLoaded        = Event()
        self.OnStatsFullBattleLoaded    = Event()

# Vars .......................................................................

#This is "Wargaming.net\WorldOfTanks\xvm\"-dir from the '_UserPrefs' in "xvm_main\python\userprefs.py"-module
CACHE_PATH = path.dirname(unicode(BigWorld.wg_getPreferencesFilePath(), 'utf-8', errors='ignore')) + '/xvm/' 

g_HomeRegion          = _HomeRegion()
#'token' in "<token>.dat"-file from the cache-folder
g_UserToken           = _UserToken()
g_XVMConsole          = _XVMConsole()
g_XVMStatisticsEvents = _XVMStatisticsEvents()

# Hooks ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

from hook_methods import g_overrideLib

@g_overrideLib.registerEvent(PlayerAvatar, '_PlayerAvatar__startGUI')
def new__startGUI(self):
    g_HomeRegion.setAccountDBID(getAvatarDatabaseID())
    if g_XVMStatisticsEvents.OnStatsFullBattleLoaded._delegates:
        IDs = []
        for vID, vData in self.arena.vehicles.iteritems():
            IDs.append(vData['accountDBID'])
        if IDs:
            g_XVMConsole.getStatsByID_Async(IDs, g_XVMStatisticsEvents.OnStatsFullBattleLoaded)
        else:
            g_XVMStatisticsEvents.OnStatsFullBattleLoaded(None)
    elif g_XVMStatisticsEvents.OnStatsBattleLoaded._delegates:
        IDs = {}
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
            IDs[vData['accountDBID']] = vehCD
        if IDs:
            g_XVMConsole.getStats_Async(IDs, g_XVMStatisticsEvents.OnStatsBattleLoaded)
        else:
            g_XVMStatisticsEvents.OnStatsBattleLoaded(None)

def addStatsAccountBecomePlayer():
    if isPlayerAccount():
        if getattr(BigWorld.player(), 'databaseID', None) is None:
            BigWorld.callback(0.2, addStatsAccountBecomePlayer)
        else:
            g_UserToken.init()
            g_HomeRegion.setAccountDBID(BigWorld.player().databaseID)
            if g_UserToken.errorStatus:
                print '[%s] "xvm_statistics": %s' % (__author__, g_UserToken.errorStatus)
            elif g_XVMStatisticsEvents.OnStatsAccountBecomePlayer._delegates:
                g_XVMConsole.getStatsByID_Async(g_UserToken.accountDBID, g_XVMStatisticsEvents.OnStatsAccountBecomePlayer)

g_playerEvents.onAccountBecomePlayer += addStatsAccountBecomePlayer

print '[%s] Loading mod: "xvm_statistics" %s (http://www.koreanrandom.com)' % (__author__, __version__)
