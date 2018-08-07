# -*- coding: utf-8 -*-

__version__ = 'V1.0.0 P2.7 W1.0.0 06.08.2018'
__author__  = 'StranikS_Scan'

import BigWorld, Event, BattleReplay
from Avatar import PlayerAvatar
from constants import ARENA_GUI_TYPE_LABEL, ARENA_BONUS_TYPE
from gui.shared.utils.functions import getArenaGeomentryName
from items.components.c11n_constants import SeasonType, SeasonTypeNames

import re 
import ResMgr, os, codecs, json
import unicodedata

# Consts and Vars ..........................................................................

CSV_VERSION = '1.0'

CONFIG_FILENAME = None
LOG_BATTLES = LOG_PLAYERS = LOG_EVENTS = False
LOG_BATTLES_FILENAME = None
LOG_PLAYERS_FILENAME = None
LOG_EVENTS_FILENAME = None

# Classes and functions ===========================================================

class _EventHook(object):
    def __init__(self):
        self.__handlers = []

    def __iadd__(self, handler):
        self.__handlers.append(handler)
        return self

    def __isub__(self, handler):
        if handler in self.__handlers:
            self.__handlers.remove(handler)
        return self

    def fire(self, *a, **k):
        for handler in self.__handlers:
            handler(*a, **k)

    def clearObjectHandlers(self, inObject):
        for handler in self.__handlers:
            if handler.im_self == inObject:
                self -= handler

class _OverrideLib(object):
    def __init__(self):
        self.registerEvent = self.__hookDecorator(self.__registerEvent) 
        self.overrideMethod = self.__hookDecorator(self.__overrideMethod)
        self.overrideClassMethod = self.__hookDecorator(self.__overrideClassMethod)
        self.overrideStaticMethod = self.__hookDecorator(self.__overrideStaticMethod)

    def __logTrace(self, func, debug):
        if debug:
            debug.write('Error in %s' % func.__name__)
            import traceback
            debug.write(traceback.format_exc()) #Test

    def __eventHandler(self, func, debug, prepend, e, m, *a, **k):
        try:
            if prepend:
                e.fire(*a, **k)
                r = m(*a, **k)
            else:
                r = m(*a, **k)
                e.fire(*a, **k)
            return r
        except:
            self.__logTrace(func, debug)

    def __overrideHandler(self, func, orig, debug, *a, **k):
        try: 
            return func(orig, *a, **k)
        except:
            self.__logTrace(func, debug)

    def __hookDecorator(self, func):
        def Decorator1(*a, **k):
            def Decorator2(handler):
                func(handler, *a, **k)
            return Decorator2
        return Decorator1

    def __override(self, cls, method, new_method):
        orig = getattr(cls, method)
        if type(orig) is property:
            setattr(cls, method, property(new_method))
        else:
            setattr(cls, method, new_method) 

    def __registerEvent(self, handler, cls, method, debug=None, prepend=False):
        evt = '__event_%i_%s' % (1 if prepend else 0, method)
        if hasattr(cls, evt):
            e = getattr(cls, evt)
        else:
            new_method = '__orig_%i_%s' % (1 if prepend else 0, method)
            setattr(cls, evt, _EventHook())
            setattr(cls, new_method, getattr(cls, method))
            e = getattr(cls, evt)
            m = getattr(cls, new_method)
            l = lambda *a, **k: self.__eventHandler(handler, debug, prepend, e, m, *a, **k)
            l.__name__ = method
            setattr(cls, method, l)
        e += handler

    def __overrideMethod(self, handler, cls, method, debug=None):
        orig = getattr(cls, method)
        new_method = lambda *a, **k: self.__overrideHandler(handler, orig, debug, *a, **k)
        new_method.__name__ = method
        self.__override(cls, method, new_method)

    def __overrideStaticMethod(self, handler, cls, method, debug=None):
        orig = getattr(cls, method)
        new_method = staticmethod(lambda *a, **k: self.__overrideHandler(handler, orig, debug, *a, **k))
        self.__override(cls, method, new_method)

    def __overrideClassMethod(self, handler, cls, method, debug=None):
        orig = getattr(cls, method)
        new_method = classmethod(lambda *a, **k: self.__overrideHandler(handler, orig, debug, *a, **k))
        self.__override(cls, method, new_method)

BONUS_TYPE_NAMES = {getattr(ARENA_BONUS_TYPE, k):k for k in dir(ARENA_BONUS_TYPE) if not k.startswith('_') and isinstance(getattr(ARENA_BONUS_TYPE, k), int)}

def getRootPath():
    return ResMgr.openSection('../paths.xml')['Paths'].values()[0].asString.replace('res_mods', 'mods') + '/'

def getLogPath(dirname):
    rootPath = getRootPath()
    if dirname:
        dirname = dirname.replace('\\', '/')
        if dirname[-1] != '/':
            dirname += '/'
    path = (rootPath if not (':' in dirname) else '') + dirname
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except:
            path = rootPath
    return path

def getConfigFileName():
    filename = getRootPath() + 'configs/SimpleLogger/SimpleLogger.cfg'
    return filename if os.path.exists(filename) else None

def removeAccents(value): 
    return u"".join([c for c in unicodedata.normalize('NFKD', unicode(value)) if not unicodedata.combining(c)])

def tankTypeAbb(tag):
    return 'MT' if 'mediumTank' == tag else 'HT' if 'heavyTank'== tag else 'AT' if 'AT-SPG' == tag else 'SPG' if 'SPG' == tag else 'LT'

def printStrings(filename, value): 
    if filename is not None:
        with codecs.open(filename, 'a', 'utf-8-sig') as file:
            if isinstance(value, list) or isinstance(value, tuple):
                file.write(';'.join(value) + '\n')
            else:
                file.write(value + '\n')

# CSV -----------------------------------------------------------------

BATTLES_HEADER = ('"arenaUniqueID"','"arenaGuiType"','"arenaTypeID"','"arenaBonusType"','"arenaKind"','"battleLevel"') + \
                 ('"allyTanksCount"','"enemyTanksCount','"allyTeamHP"','"enemyTeamHP"','"allyTanksAvgLevel"','"enemyTanksAvgLevel"') 
PLAYERS_HEADER = ('"arenaUniqueID"','"accountDBID"','"userName"','"isEnemy"','"vehicleTypeTag"','"vehicleTypeNFKD"','"level"','"hp"') + \
                 ('"xvm_battles"','"xvm_wins"','"xvm_experience"','"xvm_damage"','"xvm_frags"','"xvm_spot"','"xvm_capture"','"xmv_defense"','"xvm_accuracy"','"xvm_survived"','"xvm_wn8"','"xvm_wgr"','"xvm_wtr"') + \
                 ('',)
EVENTS_HEADER = ('"arenaUniqueID"','') 

# Hooks ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

def onBattleLoaded(statistic):
    if LOG_BATTLES:
        player = BigWorld.player()
        battleInfo = ('%d' % player.arenaUniqueID,
                      '"%s(%d)"' % (ARENA_GUI_TYPE_LABEL.LABELS[player.arenaGuiType], player.arenaGuiType),
                      '"%s(%d)"' % (getArenaGeomentryName(player.arenaTypeID), player.arenaTypeID),
                      '"%s(%d)"' % (BONUS_TYPE_NAMES[player.arenaBonusType], player.arenaBonusType),
                      '"%s(%d)"' % (SeasonTypeNames[SeasonType.fromArenaKind(player.arenaExtraData['arenaKind'])], player.arenaExtraData['arenaKind']),
                      '%d' % player.arenaExtraData['battleLevel'],
                      #--------------
                      '%d' % statistic.allyTanksCount,
                      '%d' % statistic.enemyTanksCount,
                      '%d' % statistic.allyTeamHP,
                      '%d' % statistic.enemyTeamHP,
                      ('%.3f' % (sum([value['level'] for value in statistic.base.itervalues() if not value['isEnemy']]) / float(statistic.allyTanksCount))).replace('.',','),
                      ('%.3f' % (sum([value['level'] for value in statistic.base.itervalues() if value['isEnemy']]) / float(statistic.enemyTanksCount))).replace('.',','))
        printStrings(LOG_BATTLES_FILENAME, battleInfo)

def onXVMBattleLoaded(statistic):
    if LOG_PLAYERS:
        statistic = {x['_id']:x for x in statistic['players']} if statistic and statistic.has_key('players') else {}
        for vType in g_TanksStatistic.base.values():
            playerInfo = ['%d' % BigWorld.player().arenaUniqueID,
                          '%d' % vType['accountDBID'] if vType['accountDBID'] else '',
                          '"%s"' % vType['userName'],
                          '%d' % vType['isEnemy'],
                          '"%s"' % tankTypeAbb(vType['type']['tag']),
                          '"%s"' % vType['name'],
                          '%d' % vType['level'],
                          '%d' % vType['hp']]
            playerStat = []
            pStat = statistic.get(vType['accountDBID'])
            if pStat:
                playerStat = ['%d' % pStat['b'] if pStat['b'] else '',
                              '%d' % pStat['w'] if pStat['w'] else '',
                              '%d' % pStat['xp'] if pStat['xp'] else '',
                              '%d' % pStat['dmg'] if pStat['dmg'] else '',
                              '%d' % pStat['frg'] if pStat['frg'] else '',
                              '%d' % pStat['spo'] if pStat['spo'] else '',
                              '%d' % pStat['cap'] if pStat['cap'] else '',
                              '%d' % pStat['def'] if pStat['def'] else '',
                              ('%.2f' % pStat['hip']).replace('.',',') if pStat['hip'] else '',
                              '%d' % pStat['srv'] if pStat['srv'] else '',
                              '%d' % pStat['wn8'] if pStat['wn8'] else '',
                              '%d' % pStat['wgr'] if pStat['wgr'] else '',
                              '%d' % pStat['wtr'] if pStat['wtr'] else '']
            printStrings(LOG_PLAYERS_FILENAME, playerInfo + playerStat)

try:
    from gui.mods.xvm_statistics import g_XVMStatisticsEvents
    from gui.mods.victory_chances import g_StatisticEvents, g_TanksStatistic
except:
    print '[%s] Loading mod: Not found "mod.NetStatisticsModules", loading stoped!' % __author__
else:
    g_overrideLib = _OverrideLib() 
    g_XVMStatisticsEvents.OnStatsBattleLoaded += onXVMBattleLoaded
    g_StatisticEvents.OnBattleLoaded += onBattleLoaded

    CONFIG_FILENAME = getConfigFileName()
    if CONFIG_FILENAME is not None:
        #Config ------------------------------------------
        config = json.loads(re.compile('(/\*(.|\n)*?\*/)|((#|//).*?$)', re.I | re.M).sub('', codecs.open(CONFIG_FILENAME, 'r', 'utf-8-sig').read()))
        logPath = getLogPath(config['System']['Dir'])
        LOG_BATTLES_FILENAME = logPath + '/sl_battles_ver_%s.csv' % CSV_VERSION
        LOG_PLAYERS_FILENAME = logPath + '/sl_players_ver_%s.csv' % CSV_VERSION
        LOG_EVENTS_FILENAME = logPath + '/sl_events_ver_%s.csv' % CSV_VERSION
        LOG_BATTLES = config['System']['Log']['Battles']
        LOG_PLAYERS = config['System']['Log']['Players']
        LOG_EVENTS = config['System']['Log']['Events']
        if LOG_BATTLES and not os.path.exists(LOG_BATTLES_FILENAME):
            printStrings(LOG_BATTLES_FILENAME, BATTLES_HEADER)
        if LOG_PLAYERS and not os.path.exists(LOG_PLAYERS_FILENAME):
            printStrings(LOG_PLAYERS_FILENAME, PLAYERS_HEADER)
        if LOG_EVENTS and not os.path.exists(LOG_EVENTS_FILENAME):
            printStrings(LOG_EVENTS_FILENAME, EVENTS_HEADER)

    print '[%s] Loading mod: "SimpleLogger" %s (http://www.koreanrandom.com)' % (__author__, __version__)