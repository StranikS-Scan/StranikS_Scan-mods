# -*- coding: utf-8 -*-

__author__  = 'StranikS_Scan'
__version__ = 'V2.0 P2.7 W1.3.0 17.01.2019'

#+-------------------------------------------- ATTENTION --------------------------------------------+
#| If you are a mods maker and want to using this module in your application, then you need to:      |
#| 1. Register your application in the developer's website (https://developers.wargaming.net) and    |
#|    get the code <application_id> (hereinafter the appToken)                                       |
#| 2. Use your appToken as the first argument when calling functions and registering event handlers: |
#|    g_WGConsole.getOnlineUsersCount(appToken, 'en')                                                |
#|    g_WGStatisticsEvents.addStatsAccountBecomePlayer(appToken, MyStats)                            |
#+---------------------------------------------------------------------------------------------------+

import BigWorld
from Avatar import PlayerAvatar
from PlayerEvents import g_playerEvents
from avatar_helpers import getAvatarDatabaseID
from helpers import isPlayerAccount
from constants import CURRENT_REALM, DEFAULT_LANGUAGE

from os import path, makedirs
import cPickle, threading
from copy import deepcopy
from time import sleep

from methods.http import loadJsonUrl
from methods.console import _StatisticsConsole
from methods.events import _StatisticsEvents
from methods.hook import g_overrideLib
from rating_calculation import g_Calculator

# Consts .....................................................................

#Servers in different regions
REGION_RU = 'ru'
REGION_EU = 'eu'
REGION_NA = 'com'
REGION_AS = 'asia'

WG_SERVER      = 'https://api.worldoftanks.{REGION}'
API_USERS      = '/wot/account/list/?application_id={TOKEN}&{REQ}'
API_USERSINFO  = '/wot/account/info/?application_id={TOKEN}&{REQ}'
API_USERSTANKS = '/wot/account/tanks/?application_id={TOKEN}&{REQ}'
API_TANKS      = '/wot/tanks/stats/?application_id={TOKEN}&{REQ}'
API_SERVERS    = '/wgn/servers/info/?application_id={TOKEN}&game=wot'

#Search player accountDBID by his nickname, example:
#---> https://api.worldoftanks.ru/wot/account/list/?application_id=76f79f28cc829699fe6225c90b7bda28&search=StranikS_Scan
#{"status":"ok","meta":{"count":1},"data":[{"nickname":"StranikS_Scan","account_id":2365719}]}
WG_IDBYNICK = WG_SERVER + API_USERS.format(TOKEN='{TOKEN}', REQ='search={NICK}')
API_IDBYNICK_FIELDS = '&fields={FIELDS}'
API_IDBYNICK_LIMIT  = '&limit={LIMIT}' #0-100

#Finding player accountDBIDs by their names, example:
#---> https://api.worldoftanks.ru/wot/account/list/?application_id=76f79f28cc829699fe6225c90b7bda28&search=StranikS_Scan,spoter&type=exact
#{"status":"ok","meta":{"count":2},"data":[{"nickname":"spoter","account_id":34483},{"nickname":"StranikS_Scan","account_id":2365719}]}
WG_IDSBYNICKS = WG_SERVER + API_USERS.format(TOKEN='{TOKEN}', REQ='search={NICKS}&type=exact')
API_IDSBYNICKS_FIELDS = '&fields={FIELDS}'

#Get total statistics of one or more players by their accountDBID, example:
#----> https://api.worldoftanks.ru/wot/account/info/?application_id=76f79f28cc829699fe6225c90b7bda28&account_id=2365719,34483
#{"status":"ok","meta":{"count":2},"data":{"34483": {"client_language":"ru",...}, "2365719": {"client_language":"ru",...}}}
WG_USERSSTATS = WG_SERVER + API_USERSINFO.format(TOKEN='{TOKEN}', REQ='account_id={IDS}')
API_USERSSTATS_EXTRA  = '&extra={EXTRA}'
API_USERSSTATS_FIELDS = '&fields={FIELDS}'

#Get main statistics for each player's tank of one or more players by their accountDBID, example:
#----> https://api.worldoftanks.ru/wot/account/tanks/?application_id=76f79f28cc829699fe6225c90b7bda28&account_id=2365719,34483
#{"status":"ok","meta":{"count":2},"data":{"34483":[{"statistics":{"wins":748,"battles":1357},"mark_of_mastery":4,"tank_id":53249},...], 
#                                          "2365719":[{"statistics":{"wins":686,"battles":1259},"mark_of_mastery":4,"tank_id":54289},...]}}
WG_USERSTANKS = WG_SERVER + API_USERSTANKS.format(TOKEN='{TOKEN}', REQ='account_id={IDS}')
API_USERSTANKS_FIELDS = '&fields={FIELDS}'

#Get detailed statistics for each player's tank by accountDBID, example:
#---> https://api.worldoftanks.ru/wot/tanks/stats/?application_id=76f79f28cc829699fe6225c90b7bda28&account_id=2365719
#{"status":"ok","meta":{"count":1},"data":{"2365719":[{"tank_id":769,"account_id":2365719,"max_xp":576,"max_frags":1,
#                                                      "frags":null,"mark_of_mastery":0,"in_garage":null,"clan":{"spotted":17,...},"all":{"spotted":17,...},...}]}}
WG_TANKS = WG_SERVER + API_TANKS.format(TOKEN='{TOKEN}', REQ='account_id={ID}')
API_TANKS_TANKIDS = '&tank_id={IDS}'
API_TANKS_EXTRA   = '&extra={EXTRA}'
API_TANKS_FIELDS  = '&fields={FIELDS}'

#Get online WOT-server statistics, example:
#---> https://api.worldoftanks.eu/wgn/servers/info/?application_id=76f79f28cc829699fe6225c90b7bda28&game=wot
#{"status":"ok","data":{"wot":[{"players_online":46579,"server":"EU2"},{"players_online":74296,"server":"EU1"}]}}
WG_ONLINE = WG_SERVER + API_SERVERS

# Static functions ***********************************************************

def _userRegion(accountDBID):
    return REGION_RU if accountDBID < 500000000 else REGION_EU if accountDBID < 1000000000 else REGION_NA if accountDBID < 2000000000 else REGION_AS

# Classes ====================================================================

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

#Sending typical requests to the WG-server
class _WGConsole(_StatisticsConsole):
    def __init__(self):
        _StatisticsConsole.__init__(self)
        self.__timeDelay = 0.5

    def _StatisticsConsole__sendRequest(self, appToken, async, url, onAsyncReports):
        answer = loadJsonUrl(url)
        if answer:
            meta = answer.get('meta', {})
            answer = answer['data'] if not meta or meta['count'] > 0 else {}
        if async:
            if onAsyncReports:
                if isinstance(onAsyncReports, list):
                    for delegate in onAsyncReports[0:-1]:
                        delegate(deepcopy(answer))
                    onAsyncReports[-1](answer)
                else:
                    onAsyncReports(answer)
            else:
                if appToken in self._StatisticsConsole__onAsyncReports:
                    for delegate in self._StatisticsConsole__onAsyncReports[appToken][0:-1]:
                        delegate(deepcopy(answer))
                    self._StatisticsConsole__onAsyncReports[appToken][-1](answer)
        return answer

    def getOnlineUsersCount(self, appToken, region=''):
        if appToken:
            if not region:
                region = g_HomeRegion.homeRegion
            return self._StatisticsConsole__prepareRequest(appToken, False, WG_ONLINE.format(TOKEN=appToken, REGION=region))

    #appToken=<application_id>; nicknames=['Straik','MeeGo'] or 'Straik' only; region='RU'; fields=['nickname','account_id']
    def getIDbyNick(self, appToken, nicknames, region='', fields=[]):
        if appToken and nicknames:
            if not region:
                region = g_HomeRegion.homeRegion
            fields = API_IDSBYNICKS_FIELDS.format(FIELDS=','.join(fields)) if fields else ''
            return self._StatisticsConsole__prepareRequest(appToken, False, WG_IDSBYNICKS.format(TOKEN=appToken, REGION=region, NICKS=','.join(nicknames)) + fields) if isinstance(nicknames, list) else \
                   self._StatisticsConsole__prepareRequest(appToken, False, WG_IDBYNICK.format(TOKEN=appToken, REGION=region, NICK=nicknames) + fields)

    def getIDbyNick_Async(self, appToken, nicknames, region='', fields=[], onAsyncReports=None):
        if appToken and nicknames:
            if not region:
                region = g_HomeRegion.homeRegion
            fields = API_IDSBYNICKS_FIELDS.format(FIELDS=','.join(fields)) if fields else ''
            return self._StatisticsConsole__prepareRequest(appToken, True, WG_IDSBYNICKS.format(TOKEN=appToken, REGION=region, NICKS=','.join(nicknames)) + fields, onAsyncReports) if isinstance(nicknames, list) else \
                   self._StatisticsConsole__prepareRequest(appToken, True, WG_IDBYNICK.format(TOKEN=appToken, REGION=region, NICK=nicknames) + fields, onAsyncReports)
        elif onAsyncReports:
            if isinstance(onAsyncReports, list):
                for delegate in onAsyncReports:
                    delegate(None)
            else:
                onAsyncReports(None)
        elif appToken in self._StatisticsConsole__onAsyncReports:
            for delegate in self._StatisticsConsole__onAsyncReports[appToken]:
                delegate(None)

    #appToken=<application_id>; accountDBIDs=[2365719,34483] or 2365719 only; fields=['client_language','last_battle_time']
    def getStatsByID(self, appToken, accountDBIDs, fields=[], extra=[]):
        if appToken and accountDBIDs:
            if isinstance(accountDBIDs, list):
                region = _userRegion(accountDBIDs[0])
                accountDBIDs = ','.join(accountDBIDs)
            else:
                region = _userRegion(accountDBIDs)
            extra = API_USERSSTATS_EXTRA.format(EXTRA=','.join(extra)) if extra else ''
            fields = API_USERSSTATS_FIELDS.format(FIELDS=','.join(fields)) if fields else ''
            return self._StatisticsConsole__prepareRequest(appToken, False, WG_USERSSTATS.format(TOKEN=appToken, REGION=region, IDS=accountDBIDs) + extra + fields)

    def getStatsByID_Async(self, appToken, accountDBIDs, fields=[], extra=[], onAsyncReports=None):
        if appToken and accountDBIDs:
            if isinstance(accountDBIDs, list):
                region = _userRegion(accountDBIDs[0])
                accountDBIDs = ','.join(map(str, accountDBIDs))
            else:
                region = _userRegion(accountDBIDs)
            extra = API_USERSSTATS_EXTRA.format(EXTRA=','.join(extra)) if extra else ''
            fields = API_USERSSTATS_FIELDS.format(FIELDS=','.join(fields)) if fields else ''
            return self._StatisticsConsole__prepareRequest(appToken, True, WG_USERSSTATS.format(TOKEN=appToken, REGION=region, IDS=accountDBIDs) + extra + fields, onAsyncReports)
        elif onAsyncReports:
            if isinstance(onAsyncReports, list):
                for delegate in onAsyncReports:
                    delegate(None)
            else:
                onAsyncReports(None)
        elif appToken in self._StatisticsConsole__onAsyncReports:
            for delegate in self._StatisticsConsole__onAsyncReports[appToken]:
                delegate(None)

    #appToken=<application_id>; accountDBIDs=[2365719,34483] or 2365719 only; fields=['statistics.wins','tank_id']
    def getTanksCompact(self, appToken, accountDBIDs, fields=[]):
        if appToken and accountDBIDs:
            if isinstance(accountDBIDs, list):
                region = _userRegion(accountDBIDs[0])
                accountDBIDs = ','.join(map(str, accountDBIDs))
            else:
                region = _userRegion(accountDBIDs)
            fields = API_USERSTANKS_FIELDS.format(FIELDS=','.join(fields)) if fields else ''
            return self._StatisticsConsole__prepareRequest(appToken, False, WG_USERSTANKS.format(TOKEN=appToken, REGION=region, IDS=accountDBIDs) + fields)

    def getTanksCompact_Async(self, appToken, accountDBIDs, fields=[], onAsyncReports=None):
        if appToken and accountDBIDs:
            if isinstance(accountDBIDs, list):
                region = _userRegion(accountDBIDs[0])
                accountDBIDs = ','.join(map(str, accountDBIDs))
            else:
                region = _userRegion(accountDBIDs)
            fields = API_USERSTANKS_FIELDS.format(FIELDS=','.join(fields)) if fields else ''
            return self._StatisticsConsole__prepareRequest(appToken, True, WG_USERSTANKS.format(TOKEN=appToken, REGION=region, IDS=accountDBIDs) + fields, onAsyncReports)
        elif onAsyncReports:
            if isinstance(onAsyncReports, list):
                for delegate in onAsyncReports:
                    delegate(None)
            else:
                onAsyncReports(None)
        elif appToken in self._StatisticsConsole__onAsyncReports:
            for delegate in self._StatisticsConsole__onAsyncReports[appToken]:
                delegate(None)

    #appToken=<application_id>; accountDBID=2365719; fields=['all','tank_id']; tankIDs=[113,769]
    def getTanksFull(self, appToken, accountDBID, fields=[], tankIDs=[], extra=[]):
        if appToken and accountDBID:
            extra = API_TANKS_EXTRA.format(EXTRA=','.join(extra)) if extra else ''
            tankIDs = API_TANKS_TANKIDS.format(IDS=','.join(map(str, tankIDs))) if tankIDs else ''
            fields = API_TANKS_FIELDS.format(FIELDS=','.join(fields)) if fields else ''
            return self._StatisticsConsole__prepareRequest(appToken, False, WG_TANKS.format(TOKEN=appToken, REGION=_userRegion(accountDBID), ID=accountDBID) + \
                                                                            extra + tankIDs + fields)

    def getTanksFull_Async(self, appToken, accountDBID, fields=[], tankIDs=[], extra=[], onAsyncReports=None):
        if appToken and accountDBID:
            extra = API_TANKS_EXTRA.format(EXTRA=','.join(extra)) if extra else ''
            tankIDs = API_TANKS_TANKIDS.format(IDS=','.join(map(str, tankIDs))) if tankIDs else ''
            fields = API_TANKS_FIELDS.format(FIELDS=','.join(fields)) if fields else ''
            return self._StatisticsConsole__prepareRequest(appToken, True, WG_TANKS.format(TOKEN=appToken, REGION=_userRegion(accountDBID), ID=accountDBID) + \
                                                                           extra + tankIDs + fields, onAsyncReports)
        elif onAsyncReports:
            if isinstance(onAsyncReports, list):
                for delegate in onAsyncReports:
                    delegate(None)
            else:
                onAsyncReports(None)
        elif appToken in self._StatisticsConsole__onAsyncReports:
            for delegate in self._StatisticsConsole__onAsyncReports[appToken]:
                delegate(None)

    def __prepareStatsRequest(self, appToken, async, IDs, onAsyncReports, timeout):
        if async:
            thread = threading.Thread(target=self.__sendStatsRequest, args=[appToken, async, IDs, onAsyncReports, timeout])
            thread.setDaemon(True)
            thread.start()
        else:
            return self.__sendStatsRequest(appToken, async, IDs, None, timeout)

    def __sendTankQuery(self, query, stats, timeout):
        answer = None
        while not answer and timeout >= 0:
            answer = loadJsonUrl(query)
            if not answer:
                timeout -= self.__timeDelay
                sleep(self.__timeDelay)
        if answer:
            meta = answer.get('meta', {})
            if meta and meta['count'] > 0:
                accountDBID = answer['data'].keys()[0]
                if answer['data'][accountDBID]:
                    statistics = answer['data'][accountDBID][0]
                    if statistics and 'all' in statistics:
                        statistics.update(statistics.pop('all'))
                    stats['vehicles'] = statistics

    def __sendStatsRequest(self, appToken, async, IDs, onAsyncReports, timeout): 
        players = {'players': []}
        region = _userRegion(IDs.keys()[0])
        fields = API_USERSSTATS_FIELDS.format(FIELDS='client_language,last_battle_time,account_id,statistics.all,global_rating,clan_id,nickname')
        answer = loadJsonUrl(WG_USERSSTATS.format(TOKEN=appToken, REGION=region, IDS=','.join(map(str, IDs.keys()))) + fields)
        if answer:
            meta = answer.get('meta', {})
            stats = answer['data'] if meta and meta['count'] > 0 else {}
            fields = API_TANKS_FIELDS.format(FIELDS='all,tank_id,mark_of_mastery,in_garage')
            threads = []
            for accountDBID in stats.keys():
                player = stats[accountDBID]
                if player:
                    statistics = player.pop('statistics', None)
                    if statistics and 'all' in statistics:
                        player.update(statistics['all'])
                    player['vehicles'] = None
                    ID = int(accountDBID)
                    if ID in IDs:
                        id = IDs[ID]
                        if id != 65281:
                            thread = threading.Thread(target=self.__sendTankQuery, args=[WG_TANKS.format(TOKEN=appToken, REGION=region, ID=ID) + \
                                                      API_TANKS_TANKIDS.format(IDS=id) + fields, player, timeout])
                            thread.setDaemon(True)
                            thread.start()
                            threads.append(thread)
                    players['players'].append(player)
            for thread in threads:
                thread.join()
        if async:
            if onAsyncReports:
                if isinstance(onAsyncReports, list):
                    for delegate in onAsyncReports[0:-1]:
                        delegate(deepcopy(players))
                    onAsyncReports[-1](players)
                else:
                    onAsyncReports(players)
            else:
                if appToken in self._StatisticsConsole__onAsyncReports:
                    for delegate in self._StatisticsConsole__onAsyncReports[appToken][0:-1]:
                        delegate(deepcopy(players))
                    self._StatisticsConsole__onAsyncReports[appToken][-1](players)
        return players

    #This is an analog "getStats" in xvm_statistics
    #appToken=<application_id>; IDs={2365719:54529, 4100782:51841, accountDBID:compactDescr, ...}
    def getStats(self, appToken, IDs, timeout=5.0):
        if appToken and IDs:
            return self.__prepareStatsRequest(appToken, False, IDs, None, timeout)

    def getStats_Async(self, appToken, IDs, onAsyncReports=None, timeout=5.0):
        if appToken and IDs:
            self.__prepareStatsRequest(appToken, True, IDs, onAsyncReports, timeout)
        elif onAsyncReports:
            if isinstance(onAsyncReports, list):
                for delegate in onAsyncReports:
                    delegate(None)
            else:
                onAsyncReports(None)
        elif appToken in self._StatisticsConsole__onAsyncReports:
            for delegate in self._StatisticsConsole__onAsyncReports[appToken]:
                delegate(None)

    def __prepareStatsFullRequest(self, appToken, async, IDs, onAsyncReports, timeout):
        if async:
            thread = threading.Thread(target=self.__sendStatsFullRequest, args=[appToken, async, IDs, onAsyncReports, timeout])
            thread.setDaemon(True)
            thread.start()
        else:
            return self.__sendStatsFullRequest(appToken, async, IDs, None, timeout)

    def __sendTanksQuery(self, query, stats, timeout):
        answer = None
        while not answer and timeout >= 0:
            answer = loadJsonUrl(query)
            if not answer:
                timeout -= self.__timeDelay
                sleep(self.__timeDelay)
        if answer:
            meta = answer.get('meta', {})
            if meta and meta['count'] > 0:
                accountDBID = answer['data'].keys()[0]
                for statistics in answer['data'][accountDBID]:
                    if statistics and 'all' in statistics:
                        statistics.update(statistics.pop('all'))
                        stats['vehicles'][statistics['tank_id']] = statistics

    def __sendStatsFullRequest(self, appToken, async, IDs, onAsyncReports, timeout):
        players = {'players': []}
        region = _userRegion(IDs[0])
        fields = API_USERSSTATS_FIELDS.format(FIELDS='client_language,last_battle_time,account_id,statistics.all,global_rating,clan_id,nickname')
        answer = loadJsonUrl(WG_USERSSTATS.format(TOKEN=appToken, REGION=region, IDS=','.join(map(str, IDs))) + fields)
        if answer:
            meta = answer.get('meta', {})
            stats = answer['data'] if meta and meta['count'] > 0 else {}
            fields = API_TANKS_FIELDS.format(FIELDS='all,tank_id,mark_of_mastery,in_garage')
            threads = []
            for accountDBID in stats.keys():
                player = stats[accountDBID]
                if player:
                    statistics = player.pop('statistics', None)
                    if statistics and 'all' in statistics:
                        player.update(statistics['all'])
                    player['vehicles'] = {}
                    ID = int(accountDBID)
                    if ID in IDs:
                        thread = threading.Thread(target=self.__sendTanksQuery, args=[WG_TANKS.format(TOKEN=appToken, REGION=region, ID=ID) + fields, player, timeout])
                        thread.setDaemon(True)
                        thread.start()
                        threads.append(thread)
                    players['players'].append(player)
            for thread in threads:
                thread.join()
            for player in players['players']:
                if player['vehicles']:
                    player['avg_level'] = g_Calculator.avgTIER(player['vehicles'])
        if async:
            if onAsyncReports:
                if isinstance(onAsyncReports, list):
                    for delegate in onAsyncReports[0:-1]:
                        delegate(deepcopy(players))
                    onAsyncReports[-1](players)
                else:
                    onAsyncReports(players)
            else:
                if appToken in self._StatisticsConsole__onAsyncReports:
                    for delegate in self._StatisticsConsole__onAsyncReports[appToken][0:-1]:
                        delegate(deepcopy(players))
                    self._StatisticsConsole__onAsyncReports[appToken][-1](players)
        return players

    #This is an analog "getStatsByID" from xvm_statistics with a request for multiple players
    #appToken=<application_id>; IDs=[2365719, 4100782, accountDBID, ...] or 2365719 only
    def getStatsFull(self, appToken, IDs, timeout=5.0):
        if appToken and IDs:
            if isinstance(IDs, int):
                IDs = [IDs]
            return self.__prepareStatsFullRequest(appToken, False, IDs, None, timeout)

    def getStatsFull_Async(self, appToken, IDs, onAsyncReports=None, timeout=5.0):
        if appToken and IDs:
            if isinstance(IDs, int):
                IDs = [IDs]
            self.__prepareStatsFullRequest(appToken, True, IDs, onAsyncReports, timeout)
        elif onAsyncReports:
            if isinstance(onAsyncReports, list):
                for delegate in onAsyncReports:
                    delegate(None)
            else:
                onAsyncReports(None)
        elif appToken in self._StatisticsConsole__onAsyncReports:
            for delegate in self._StatisticsConsole__onAsyncReports[appToken]:
                delegate(None)

# Vars .......................................................................

g_HomeRegion         = _HomeRegion()
g_WGConsole          = _WGConsole()
g_WGStatisticsEvents = _StatisticsEvents()

# Hooks ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

@g_overrideLib.registerEvent(PlayerAvatar, '_PlayerAvatar__startGUI')
def new__startGUI(self):
    g_HomeRegion.setAccountDBID(getAvatarDatabaseID())
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
    onStats = g_WGStatisticsEvents._onStats_BattleLoaded
    onStatsFull = g_WGStatisticsEvents._onStats_FullBattleLoaded
    if onStatsFull:
        if IDs:
            appTokens = g_WGStatisticsEvents._appTokens_FullBattleLoaded
            appTokens.mixAppTokens()
            if onStats:
                #Make a request only once
                def onStatsExt(statistic):
                    stats = deepcopy(statistic) if statistic else None
                    player = BigWorld.player()
                    if stats and 'players' in stats:
                        for user in stats['players']:
                            ID = user.get('account_id', 0)
                            if ID in IDs and 'vehicles' in user:
                                user['vehicles'] = user['vehicles'].get(IDs[ID], {})
                    if onStats:
                        for delegate in onStats[0:-1]:
                            delegate(deepcopy(stats))
                        onStats[-1](stats)
                    if onStatsFull:
                        for delegate in onStatsFull[0:-1]:
                            delegate(deepcopy(statistic))
                        onStatsFull[-1](statistic)

                g_WGConsole.getStatsFull_Async(appTokens.appToken, IDs.keys(), onStatsExt)
            else:
                g_WGConsole.getStatsFull_Async(appTokens.appToken, IDs.keys(), onStatsFull)
        else:
            for delegate in onStats:
                delegate(None)
            for delegate in onStatsFull:
                delegate(None)
    elif onStats:
        if IDs:
            appTokens = g_WGStatisticsEvents._appTokens_BattleLoaded
            appTokens.mixAppTokens()
            g_WGConsole.getStats_Async(appTokens.appToken, IDs, onStats)
        else:
            for delegate in onStats:
                delegate(None)

def addStatsAccountBecomePlayer():
    if isPlayerAccount():
        if getattr(BigWorld.player(), 'databaseID', None) is None:
            BigWorld.callback(0.2, addStatsAccountBecomePlayer)
        else: 
            g_HomeRegion.setAccountDBID(BigWorld.player().databaseID)
            if g_HomeRegion.accountDBID == 0:
                print '[%s] "wg_statistics": Invalid accountDBID, you must re-enter the game client!' % __author__
            else:
                onStats = g_WGStatisticsEvents._onStats_AccountBecomePlayer
                if onStats:
                    appTokens = g_WGStatisticsEvents._appTokens_AccountBecomePlayer
                    appTokens.mixAppTokens()
                    g_WGConsole.getStatsFull_Async(appTokens.appToken, g_HomeRegion.accountDBID, onStats)

g_playerEvents.onAccountBecomePlayer += addStatsAccountBecomePlayer

print '[%s] Loading mod: "wg_statistics" %s (http://www.koreanrandom.com)' % (__author__, __version__)
