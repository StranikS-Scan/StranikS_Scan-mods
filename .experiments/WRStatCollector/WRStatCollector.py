# -*- coding: utf-8 -*-

__author__  = 'StranikS_Scan'
__version__ = 'V1.1 P2.7 11.08.2019'

import os, codecs
from datetime import datetime
from urllib2 import urlopen
from threading import Thread
from json import loads, dumps

#-----------------------------------------------------------------------------------

SITE_URL = 'http://wotreplays.ru/site/{REQ}'
REPLAYS_IDS_RANGE = [12325124-200, 12325124] #http://wotreplays.ru/site/12325124 and 200 replays uploaded before it

URL_TIMEOUT   = 3
THREADS_COUNT = 8    #if WG_API_STATS is True then maximum 10 due to server limitations otherwise can be more
CACHE_SIZE    = 100  #Number of records accumulated in memory before writing to a file

CSV_VERSION  = '1.1' #Do not change!
LOG_FILENAME = 'Log/Log_ver_{CSV}_{UNQ}.csv' #{CSV} - csv version; {UNQ} - unique file ID

WG_API_STATS   = True #Download player stat from WG-server
APPLICATION_ID = 'eJwzSrI0TEs0MrS0MEpONTM3NLU0SzRLTjRKMkg0MTBKTgQAjI0IsA=='.decode('base64').decode('zlib')
WG_API_USERS   = 'https://api.worldoftanks.ru/wot/account/info/?application_id={TOKEN}&{REQ}'

#===================================================================================

def getUniqueID():
    now = datetime.now()
    return now.strftime('%d%m%y') + '_' + now.strftime('%H%M%S%f')[:9] #030819_113960123

class _Collector(object):
    cached = property(lambda self: len(self.__replays.keys()))

    def __init__(self, filename, headers):
        self.__replays = {}
        self.__headers = headers
        self.__file = filename
        self.__dir = os.path.dirname(os.path.abspath(self.__file))
        if not os.path.exists(self.__dir):
            os.makedirs(self.__dir)
        if not os.path.exists(self.__file):
            with codecs.open(self.__file, 'a', 'utf-8-sig') as f:
                f.write(';'.join(('"%s"' % head for head in headers))+'\n')

    def destroy(self):
        self.__replays = self.__headers = None

    def append(self, rID, stat={}):
        self.__replays[rID] = stat
    
    def save(self):
        if self.__replays:
            data = []
            for rID in self.__replays:
                stat = self.__replays[rID]
                line = []
                for head in self.__headers:
                    value = stat.get(head)
                    if isinstance(value, bool):
                        value = '1' if value else '0'
                    elif isinstance(value, int):
                        value = '%d' % value
                    elif isinstance(value, float):
                        value = ('%.10f' % value).replace('.', ',')
                    elif isinstance(value, str) or isinstance(value, unicode):
                        value = '"%s"' % value
                    else:
                        value = ''
                    line.append(value)
                data.append(';'.join(line))
            if data:
                with codecs.open(self.__file, 'a', 'utf-8') as f:
                    f.write('\n'.join(data)+'\n')
            self.__replays.clear()

class _Replays(object):
    HEAD_REPLAY_ID    = 'ReplayID'
    HEAD_CLIENT_VER   = 'ClientVersion'
    HEAD_DATETIME     = 'DateTime'
    HEAD_BATTLE_TYPE  = 'BattleType'
    HEAD_MAP_NAME     = 'MapName'
    HEAD_MAP_RESP     = 'MapResp'
    HEAD_PLAYER_ID    = 'PlayerID'
    HEAD_PLAYER_NAME  = 'PlayerName'
    HEAD_PLAYER_TANK  = 'PlayerTank'
    HEAD_RESULT       = 'Result'
    HEAD_PREMIUM      = 'isPremium'
    HEAD_PLATOON      = 'isPlatoon'
    HEAD_PLAYER_SHOTS = 'PlayerShots'
    HEAD_PLAYER_FRAGS = 'PlayerFrags'
    HEAD_PLAYER_DAMAGEDEALT = 'PlayerDamageDealt'
    HEAD_PLAYER_SPOTS   = 'PlayerSpots'
    HEAD_PLAYER_BASECAP = 'PlayerBaseCap'
    HEAD_PLAYER_BASEDEF = 'PlayerBaseDef'
    HEAD_PLAYER_MILEAGE = 'PlayerMileage'
    HEAD_API_PLAYER_BATTLES = 'API_PlayerBattles'
    HEAD_API_PLAYER_WINS    = 'API_PlayerWins'
    HEAD_REPLAY_URL = 'ReplayUrl'

    def __init__(self, collector):
        self.__collector = collector
        self.__threads = []
        
    def destroy(self):
        self.__collector.destroy()
        self.__collector = self.__threads = None

    def run(self, site, replaysIDs):
        idMin, idMax = replaysIDs
        while idMin <= idMax:
            thread = Thread(target=self.__parseReplay, args=[idMin])
            thread.setDaemon(True)
            thread.start()
            self.__threads.append(thread)
            idMin += 1
            if len(self.__threads) >= THREADS_COUNT:
                self.__threads[0].join()
                self.__threads.pop(0)
            if self.__collector.cached >= CACHE_SIZE:
                for thread in self.__threads:
                    thread.join()
                self.__threads = []
                self.__collector.save()
        for thread in self.__threads:
            thread.join()
        self.__threads = []
        self.__collector.save()

    def __parseReplay(self, rID):
        request = SITE_URL.format(REQ=rID)
        text = self.__getHtml(request)
        if text:
            res, stat = self.__parseHtml(text)
            if not res:
                print '%d not standard or corrupted!' % rID 
            if stat:
                stat[self.HEAD_REPLAY_ID] = rID
                stat[self.HEAD_REPLAY_URL] = request
                #---
                if WG_API_STATS and self.HEAD_PLAYER_ID in stat:
                    text = self.__getHtml(WG_API_USERS.format(TOKEN=APPLICATION_ID, REQ='account_id=%s&fields=statistics.all' % stat[self.HEAD_PLAYER_ID]))
                    if text:
                        res, wg_stat = self.__parseWGUserStat(text)
                        if res:
                            stat.update(wg_stat)
                #---
                self.__collector.append(rID, stat)
        else:
            print '%d not found!' % rID

    def __getHtml(self, request):
        try:
            response = urlopen(url=request, timeout=URL_TIMEOUT)
            if response.code == 200:
                return response.read()
        except:
            pass

    def __parseHtml(self, text):
        stat = {}                                                             #http://wotreplays.ru/site/12323660
        try:
            text = text.split('replay-stats__hat replay-stats__hat--', 1)[1]  #690  lose">...
            stat[self.HEAD_RESULT], text = text.split('">', 1)
            text = text.split('/static/img/wot/dynamic/Maps/', 1)[1]          #822  08_ruinberg.png" alt="Руинберг"/>...
            stat[self.HEAD_MAP_NAME], text = text.split('.png', 1)
            text = text.split('replay-stats__timestamp">', 1)[1]              #833  10.08.2019 07:21</div>...
            stat[self.HEAD_DATETIME], text = text.split('</div>', 1)
            text = text.split('replay-stats__earnings_table--', 1)[1]         #837  premium">...
            isPremium, text = text.split('">', 1)
            stat[self.HEAD_PREMIUM] = 'non' not in isPremium
            text = text.split('worldoftanks.ru/ru/community/accounts/', 1)[1] #895  35528821-N_U_B_O_R_A_K/"...
            playerID, text = text.split('-', 1)
            playerID = int(playerID)
            stat[self.HEAD_PLAYER_ID] = playerID
            text = text.split('replay__info clearfix', 1)[1]                  #1819 ">\n  <li>\n  <span class="b-label">Версия:</span>\n 1.6.0 </li>...
            text = text.split('</span>', 1)[1]
            clientVer, text = text.split('</li>', 1)
            stat[self.HEAD_CLIENT_VER] = '[%s]' % clientVer.strip()
            text = text.split('b-replay__img_wrap', 1)[1]                     #1824 ">...
            text = text.split('</span>', 1)[1]                                #1827 I  </span>
            mapResp, text = text.split('</span>', 1)
            stat[self.HEAD_MAP_RESP] = mapResp.strip()
            text = text.split('</span>', 1)[1]                                #1830 Случайный бой   </li>...
            battleType, text = text.split('</li>', 1)
            stat[self.HEAD_BATTLE_TYPE] = unicode(battleType.strip(), 'utf-8')
            text = text.split('var roster =', 1)[1]                           #1866 [{"green":{"nation":"usa",... 
            for pair in loads(text.split(';', 1)[0]):
                if pair['green']['global_id'] == playerID:
                    player = pair['green']
                    stat[self.HEAD_PLAYER_NAME] = str(player['name'])
                    stat[self.HEAD_PLAYER_TANK] = str(player['vehicleType'])
                    stat[self.HEAD_PLATOON] = int(player['platoon'])
                    stat[self.HEAD_PLAYER_SHOTS] = int(player['vehicleShots'])
                    stat[self.HEAD_PLAYER_FRAGS] = int(player['frags'])
                    stat[self.HEAD_PLAYER_DAMAGEDEALT] = int(player['damageDealt'])
                    stat[self.HEAD_PLAYER_SPOTS] = int(player['vehicleSpotted'])
                    stat[self.HEAD_PLAYER_BASECAP] = int(player['vehicleBaseCapture'])
                    stat[self.HEAD_PLAYER_BASEDEF] = int(player['vehicleBaseDef'])
                    stat[self.HEAD_PLAYER_MILEAGE] = float(player['vehicleMileage'])
                    break
        except:
            return False, stat
        return True, stat

    def __parseWGUserStat(self, text):
        stat = {}
        try:
            info = loads(text) #{u'status': u'ok', u'meta': {u'count': 1}, u'data': {u'35528821': {u'statistics': {u'all': {u'spotted': 23543, u'battles_on_stunning_vehicles': 1310, ...}}}}}
            if 'data' in info:
                info = info['data'].values()[0]['statistics']['all']
                stat[self.HEAD_API_PLAYER_BATTLES] = int(info['battles'])
                stat[self.HEAD_API_PLAYER_WINS] = int(info['wins'])
        except:
            return False, stat
        return True, stat

print '%d replays: %d...%d' % (REPLAYS_IDS_RANGE[1] - REPLAYS_IDS_RANGE[0] + 1, REPLAYS_IDS_RANGE[0], REPLAYS_IDS_RANGE[1])
Replays = _Replays(_Collector(LOG_FILENAME.format(CSV=CSV_VERSION, UNQ=getUniqueID()),
                              [_Replays.HEAD_REPLAY_ID,
                               _Replays.HEAD_CLIENT_VER,
                               _Replays.HEAD_DATETIME,
                               _Replays.HEAD_BATTLE_TYPE,
                               _Replays.HEAD_MAP_NAME,
                               _Replays.HEAD_MAP_RESP,
                               _Replays.HEAD_PLAYER_ID,
                               _Replays.HEAD_PLAYER_NAME,
                               _Replays.HEAD_PLAYER_TANK,
                               _Replays.HEAD_RESULT,
                               _Replays.HEAD_PREMIUM,
                               _Replays.HEAD_PLATOON,
                               _Replays.HEAD_PLAYER_SHOTS,
                               _Replays.HEAD_PLAYER_FRAGS,
                               _Replays.HEAD_PLAYER_DAMAGEDEALT,
                               _Replays.HEAD_PLAYER_SPOTS,
                               _Replays.HEAD_PLAYER_BASECAP,
                               _Replays.HEAD_PLAYER_BASEDEF,
                               _Replays.HEAD_PLAYER_MILEAGE,
                               _Replays.HEAD_API_PLAYER_BATTLES,
                               _Replays.HEAD_API_PLAYER_WINS,
                               _Replays.HEAD_REPLAY_URL]))
Replays.run(SITE_URL, REPLAYS_IDS_RANGE)
Replays.destroy()
print 'Completed!'