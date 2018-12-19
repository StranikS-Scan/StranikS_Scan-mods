# -*- coding: utf-8 -*-

__author__  = 'StranikS_Scan'
__version__ = 'V1.1 P2.7 W1.2.0 07.12.2018'

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

from rating_calculation import g_Calculator

# Consts .....................................................................

#Registered token on the WG-servers for the NSM
API_TOKEN = '76f79f28cc829699fe6225c90b7bda28'

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
WG_IDBYNICK = WG_SERVER + API_USERS.format(TOKEN=API_TOKEN, REQ='search={NICK}')
API_IDBYNICK_FIELDS = '&fields={FIELDS}'
API_IDBYNICK_LIMIT  = '&limit={LIMIT}' #0-100

#Finding player accountDBIDs by their names, example:
#---> https://api.worldoftanks.ru/wot/account/list/?application_id=76f79f28cc829699fe6225c90b7bda28&search=StranikS_Scan,spoter&type=exact
#{"status":"ok","meta":{"count":2},"data":[{"nickname":"spoter","account_id":34483},{"nickname":"StranikS_Scan","account_id":2365719}]}
WG_IDSBYNICKS = WG_SERVER + API_USERS.format(TOKEN=API_TOKEN, REQ='search={NICKS}&type=exact')
API_IDSBYNICKS_FIELDS = '&fields={FIELDS}'

#Get total statistics of one or more players by their accountDBID, example:
#----> https://api.worldoftanks.ru/wot/account/info/?application_id=76f79f28cc829699fe6225c90b7bda28&account_id=2365719,34483
#{"status":"ok","meta":{"count":2},"data":{"34483": {"client_language":"ru",...}, "2365719": {"client_language":"ru",...}}}
WG_USERSSTATS = WG_SERVER + API_USERSINFO.format(TOKEN=API_TOKEN, REQ='account_id={IDS}')
API_USERSSTATS_EXTRA  = '&extra={EXTRA}'
API_USERSSTATS_FIELDS = '&fields={FIELDS}'

#Get main statistics for each player's tank of one or more players by their accountDBID, example:
#----> https://api.worldoftanks.ru/wot/account/tanks/?application_id=76f79f28cc829699fe6225c90b7bda28&account_id=2365719,34483
#{"status":"ok","meta":{"count":2},"data":{"34483":[{"statistics":{"wins":748,"battles":1357},"mark_of_mastery":4,"tank_id":53249},...], 
#                                          "2365719":[{"statistics":{"wins":686,"battles":1259},"mark_of_mastery":4,"tank_id":54289},...]}}
WG_USERSTANKS = WG_SERVER + API_USERSTANKS.format(TOKEN=API_TOKEN, REQ='account_id={IDS}')
API_USERSTANKS_FIELDS = '&fields={FIELDS}'

#Get detailed statistics for each player's tank by accountDBID, example:
#---> https://api.worldoftanks.ru/wot/tanks/stats/?application_id=76f79f28cc829699fe6225c90b7bda28&account_id=2365719
#{"status":"ok","meta":{"count":1},"data":{"2365719":[{"tank_id":769,"account_id":2365719,"max_xp":576,"max_frags":1,
#                                                      "frags":null,"mark_of_mastery":0,"in_garage":null,"clan":{"spotted":17,...},"all":{"spotted":17,...},...}]}}
WG_TANKS = WG_SERVER + API_TANKS.format(TOKEN=API_TOKEN, REQ='account_id={ID}')
API_TANKS_TANKIDS = '&tank_id={IDS}'
API_TANKS_EXTRA   = '&extra={EXTRA}'
API_TANKS_FIELDS  = '&fields={FIELDS}'

#Get online WOT-server statistics, example:
#---> https://api.worldoftanks.eu/wgn/servers/info/?application_id=76f79f28cc829699fe6225c90b7bda28&game=wot
#{"status":"ok","data":{"wot":[{"players_online":46579,"server":"EU2"},{"players_online":74296,"server":"EU1"}]}}
WG_ONLINE = WG_SERVER + API_SERVERS.format(TOKEN=API_TOKEN)

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
class _WGConsole(object):
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
        if answer:
            meta = answer.get('meta', {})
            answer = answer['data'] if not meta or meta['count'] > 0 else {}
        if async:
            if onAsyncReport:
                onAsyncReport(answer)
            else:
                self.OnAsyncReports(answer)
        return answer

    def getOnlineUsersCount(self, region=''):
        if not region:
            region = g_HomeRegion.homeRegion
        return self.__prepareRequest(False, WG_ONLINE.format(REGION=region))

    #nicknames = ['Straik','MeeGo'] or 'Straik' only; region='RU'; fields=['nickname','account_id']
    def getIDbyNick(self, nicknames, region='', fields=[]):
        if nicknames:
            if not region:
                region = g_HomeRegion.homeRegion
            fields = API_IDSBYNICKS_FIELDS.format(FIELDS=','.join(fields)) if fields else ''
            return self.__prepareRequest(False, WG_IDSBYNICKS.format(REGION=region, NICKS=','.join(nicknames)) + fields) if isinstance(nicknames, list) else \
                   self.__prepareRequest(False, WG_IDBYNICK.format(REGION=region, NICK=nicknames) + fields)

    def getIDbyNick_Async(self, nicknames, region='', fields=[], onAsyncReport=None):
        if nicknames:
            if not region:
                region = g_HomeRegion.homeRegion
            fields = API_IDSBYNICKS_FIELDS.format(FIELDS=','.join(fields)) if fields else ''
            return self.__prepareRequest(True, WG_IDSBYNICKS.format(REGION=region, NICKS=','.join(nicknames)) + fields, onAsyncReport) if isinstance(nicknames, list) else \
                   self.__prepareRequest(True, WG_IDBYNICK.format(REGION=region, NICK=nicknames) + fields, onAsyncReport)
        elif onAsyncReport:
            onAsyncReport(None)
        else:
            self.OnAsyncReports(None)

    #accountDBIDs=[2365719,34483] or 2365719 only; fields=['client_language','last_battle_time']
    def getStatsByID(self, accountDBIDs, fields=[], extra=[]):
        if accountDBIDs:
            if isinstance(accountDBIDs, list):
                region = _userRegion(accountDBIDs[0])
                accountDBIDs = ','.join(accountDBIDs)
            else:
                region = _userRegion(accountDBIDs)
            extra = API_USERSSTATS_EXTRA.format(EXTRA=','.join(extra)) if extra else ''
            fields = API_USERSSTATS_FIELDS.format(FIELDS=','.join(fields)) if fields else ''
            return self.__prepareRequest(False, WG_USERSSTATS.format(REGION=region, IDS=accountDBIDs) + extra + fields)

    def getStatsByID_Async(self, accountDBIDs, fields=[], extra=[], onAsyncReport=None):
        if accountDBIDs:
            if isinstance(accountDBIDs, list):
                region = _userRegion(accountDBIDs[0])
                accountDBIDs = ','.join(map(str, accountDBIDs))
            else:
                region = _userRegion(accountDBIDs)
            extra = API_USERSSTATS_EXTRA.format(EXTRA=','.join(extra)) if extra else ''
            fields = API_USERSSTATS_FIELDS.format(FIELDS=','.join(fields)) if fields else ''
            return self.__prepareRequest(True, WG_USERSSTATS.format(REGION=region, IDS=accountDBIDs) + extra + fields, onAsyncReport)
        elif onAsyncReport:
            onAsyncReport(None)
        else:
            self.OnAsyncReports(None)

    #accountDBIDs=[2365719,34483] or 2365719 only; fields=['statistics.wins','tank_id']
    def getTanksCompact(self, accountDBIDs, fields=[]):
        if accountDBIDs:
            if isinstance(accountDBIDs, list):
                region = _userRegion(accountDBIDs[0])
                accountDBIDs = ','.join(map(str, accountDBIDs))
            else:
                region = _userRegion(accountDBIDs)
            fields = API_USERSTANKS_FIELDS.format(FIELDS=','.join(fields)) if fields else ''
            return self.__prepareRequest(False, WG_USERSTANKS.format(REGION=region, IDS=accountDBIDs) + fields)

    def getTanksCompact_Async(self, accountDBIDs, fields=[], onAsyncReport=None):
        if accountDBIDs:
            if isinstance(accountDBIDs, list):
                region = _userRegion(accountDBIDs[0])
                accountDBIDs = ','.join(map(str, accountDBIDs))
            else:
                region = _userRegion(accountDBIDs)
            fields = API_USERSTANKS_FIELDS.format(FIELDS=','.join(fields)) if fields else ''
            return self.__prepareRequest(True, WG_USERSTANKS.format(REGION=region, IDS=accountDBIDs) + fields, onAsyncReport)
        elif onAsyncReport:
            onAsyncReport(None)
        else:
            self.OnAsyncReports(None)

    #accountDBID=2365719; fields=['all','tank_id']; tankIDs=[113,769]
    def getTanksFull(self, accountDBID, fields=[], tankIDs=[], extra=[]):
        if accountDBID:
            extra = API_TANKS_EXTRA.format(EXTRA=','.join(extra)) if extra else ''
            tankIDs = API_TANKS_TANKIDS.format(IDS=','.join(map(str, tankIDs))) if tankIDs else ''
            fields = API_TANKS_FIELDS.format(FIELDS=','.join(fields)) if fields else ''
            return self.__prepareRequest(False, WG_TANKS.format(REGION=_userRegion(accountDBID), ID=accountDBID) + extra + tankIDs + fields)

    def getTanksFull_Async(self, accountDBID, fields=[], tankIDs=[], extra=[], onAsyncReport=None):
        if accountDBID:
            extra = API_TANKS_EXTRA.format(EXTRA=','.join(extra)) if extra else ''
            tankIDs = API_TANKS_TANKIDS.format(IDS=','.join(map(str, tankIDs))) if tankIDs else ''
            fields = API_TANKS_FIELDS.format(FIELDS=','.join(fields)) if fields else ''
            return self.__prepareRequest(True, WG_TANKS.format(REGION=_userRegion(accountDBID), ID=accountDBID) + extra + tankIDs + fields, onAsyncReport)
        elif onAsyncReport:
            onAsyncReport(None)
        else:
            self.OnAsyncReports(None)

    def __prepareStatsRequest(self, async, IDs, onAsyncReport, timeout):
        if async:
            thread = threading.Thread(target=self.__sendStatsRequest, args=[async, IDs, onAsyncReport, timeout])
            thread.setDaemon(True)
            thread.start()
        else:
            return self.__sendStatsRequest(async, IDs, None, timeout)

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

    def __sendStatsRequest(self, async, IDs, onAsyncReport, timeout):
        players = {'players': []}
        region = _userRegion(IDs.keys()[0])
        fields = API_USERSSTATS_FIELDS.format(FIELDS='client_language,last_battle_time,account_id,statistics.all,global_rating,clan_id,nickname')
        answer = loadJsonUrl(WG_USERSSTATS.format(REGION=region, IDS=','.join(map(str, IDs.keys()))) + fields)
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
                            thread = threading.Thread(target=self.__sendTankQuery, args=[WG_TANKS.format(REGION=region, ID=ID) + \
                                                      API_TANKS_TANKIDS.format(IDS=id) + fields, player, timeout])
                            thread.setDaemon(True)
                            thread.start()
                            threads.append(thread)
                    players['players'].append(player)
            for thread in threads:
                thread.join()
        if async:
            if onAsyncReport:
                onAsyncReport(players)
            else:
                self.OnAsyncReports(players)
        return players

    #This is an analog "getStats" in xvm_statistics
    #IDs={2365719:54529, 4100782:51841, accountDBID:compactDescr, ...}
    def getStats(self, IDs, timeout=5.0):
        if IDs:
            return self.__prepareStatsRequest(False, IDs, None, timeout)

    def getStats_Async(self, IDs, onAsyncReport=None, timeout=5.0):
        if IDs:
            self.__prepareStatsRequest(True, IDs, onAsyncReport, timeout)
        elif onAsyncReport:
            onAsyncReport(None)
        else:
            self.OnAsyncReports(None)

    def __prepareStatsFullRequest(self, async, IDs, onAsyncReport, timeout):
        if async:
            thread = threading.Thread(target=self.__sendStatsFullRequest, args=[async, IDs, onAsyncReport, timeout])
            thread.setDaemon(True)
            thread.start()
        else:
            return self.__sendStatsFullRequest(async, IDs, None, timeout)

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

    def __sendStatsFullRequest(self, async, IDs, onAsyncReport, timeout):
        players = {'players': []}
        region = _userRegion(IDs[0])
        fields = API_USERSSTATS_FIELDS.format(FIELDS='client_language,last_battle_time,account_id,statistics.all,global_rating,clan_id,nickname')
        answer = loadJsonUrl(WG_USERSSTATS.format(REGION=region, IDS=','.join(map(str, IDs))) + fields)
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
                        thread = threading.Thread(target=self.__sendTanksQuery, args=[WG_TANKS.format(REGION=region, ID=ID) + fields, player, timeout])
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
            if onAsyncReport:
                onAsyncReport(players)
            else:
                self.OnAsyncReports(players)
        return players

    #This is an analog "getStatsByID" from xvm_statistics with a request for multiple players
    #IDs=[2365719, 4100782, accountDBID, ...] or 2365719 only
    def getStatsFull(self, IDs, timeout=5.0):
        if IDs:
            if isinstance(IDs, int):
                IDs = [IDs]
            return self.__prepareStatsFullRequest(False, IDs, None, timeout)

    def getStatsFull_Async(self, IDs, onAsyncReport=None, timeout=5.0):
        if IDs:
            if isinstance(IDs, int):
                IDs = [IDs]
            self.__prepareStatsFullRequest(True, IDs, onAsyncReport, timeout)
        elif onAsyncReport:
            onAsyncReport(None)
        else:
            self.OnAsyncReports(None)

class _WGStatisticsEvents(object):
    def __init__(self):
        self.OnStatsAccountBecomePlayer = Event()
        self.OnStatsBattleLoaded        = Event()
        self.OnStatsFullBattleLoaded    = Event()

# Vars .......................................................................

g_HomeRegion         = _HomeRegion()
g_WGConsole          = _WGConsole()
g_WGStatisticsEvents = _WGStatisticsEvents()

# Hooks ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

from hook_methods import g_overrideLib

@g_overrideLib.registerEvent(PlayerAvatar, '_PlayerAvatar__startGUI')
def new__startGUI(self):
    g_HomeRegion.setAccountDBID(getAvatarDatabaseID())
    if g_WGStatisticsEvents.OnStatsFullBattleLoaded._delegates:
        IDs = []
        for vID, vData in self.arena.vehicles.iteritems():
            IDs.append(vData['accountDBID'])
        if IDs:
            g_WGConsole.getStatsFull_Async(IDs, g_WGStatisticsEvents.OnStatsFullBattleLoaded)
        else:
            g_WGStatisticsEvents.OnStatsFullBattleLoaded(None)
    elif g_WGStatisticsEvents.OnStatsBattleLoaded._delegates:
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
            g_WGConsole.getStats_Async(IDs, g_WGStatisticsEvents.OnStatsBattleLoaded)
        else:
            g_WGStatisticsEvents.OnStatsBattleLoaded(None)

def addStatsAccountBecomePlayer():
    if isPlayerAccount():
        if getattr(BigWorld.player(), 'databaseID', None) is None:
            BigWorld.callback(0.2, addStatsAccountBecomePlayer)
        else: 
            g_HomeRegion.setAccountDBID(BigWorld.player().databaseID)
            if g_HomeRegion.accountDBID == 0:
                print '[%s] "wg_statistics": Invalid accountDBID, you must re-enter the game client!' % __author__
            elif g_WGStatisticsEvents.OnStatsAccountBecomePlayer._delegates:
                g_WGConsole.getStatsByID_Async(g_HomeRegion.accountDBID, [], [], g_WGStatisticsEvents.OnStatsAccountBecomePlayer)

g_playerEvents.onAccountBecomePlayer += addStatsAccountBecomePlayer

print '[%s] Loading mod: "wg_statistics" %s (http://www.koreanrandom.com)' % (__author__, __version__)
