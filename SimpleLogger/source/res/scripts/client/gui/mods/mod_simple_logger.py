# -*- coding: utf-8 -*-

__version__ = 'V1.0.6 P2.7 W1.2.0 14.11.2018'
__author__  = 'StranikS_Scan'

import BigWorld, Event, BattleReplay
from Avatar import PlayerAvatar
from Vehicle import Vehicle
from items import vehicles
from constants import ARENA_GUI_TYPE_LABEL, ARENA_BONUS_TYPE, VEHICLE_HIT_EFFECT
from gui.shared.utils.functions import getArenaGeomentryName
from items.components.c11n_constants import SeasonType, SeasonTypeNames
from VehicleEffects import DamageFromShotDecoder

import re
import os, codecs, json
import unicodedata
from datetime import datetime

# Consts and Vars ..........................................................................

CSV_VERSION = '1.2'

CONFIG_FILENAME = None
LOG_BATTLES = LOG_PLAYERS = LOG_EVENTS = False
LOG_BATTLES_FILENAME = None
LOG_PLAYERS_FILENAME = None
LOG_EVENTS_FILENAME = None

# Classes and functions ===========================================================

def getLogPath(dirname):
    if dirname:
        dirname = dirname.replace('\\', '/')
        if dirname[-1] != '/':
            dirname += '/'
    path = ('./mods/' if ':' not in dirname else '') + dirname
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except:
            path = './mods/'
    return path

def getConfigFileName():
    filename = './mods/configs/SimpleLogger/SimpleLogger.cfg'
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

BONUS_TYPE_NAMES = {getattr(ARENA_BONUS_TYPE, k):k for k in dir(ARENA_BONUS_TYPE)[::-1] if not k.startswith('_') and isinstance(getattr(ARENA_BONUS_TYPE, k), int)}
VEHICLE_HIT_EFFECT_NAMES = {getattr(VEHICLE_HIT_EFFECT, k):k for k in dir(VEHICLE_HIT_EFFECT)[::-1] if not k.startswith('_') and isinstance(getattr(VEHICLE_HIT_EFFECT, k), int)}

# CSV -----------------------------------------------------------------

BATTLES_HEADER = ('"arenaUniqueID"','"dateTime"','"serverName"','"playerDBID"', '"userName"', '"vehicleTypeTag"', '"vehicleTypeNFKD"', '"vehicleLevel"', '"arenaGuiType"','"arenaTypeID"','"arenaBonusType"','"arenaKind"','"battleLevel"') + \
                 ('"allyTanksCount"','"enemyTanksCount"','"allyTeamHP"','"enemyTeamHP"','"allyTanksAvgLevel"','"enemyTanksAvgLevel"')
PLAYERS_HEADER = ('"arenaUniqueID"','"accountDBID"','"userName"','"isEnemy"','"vehicleTypeTag"','"vehicleTypeNFKD"','"level"','"hp"') + \
                 ('"xvm_battles"','"xvm_wins"','"xvm_experience"','"xvm_damage"','"xvm_frags"','"xvm_spot"','"xvm_capture"','"xmv_defense"','"xvm_accuracy"','"xvm_survived"','"xvm_wn8"','"xvm_wgr"','"xvm_wtr"') 
EVENTS_HEADER =  ('"arenaUniqueID"','"remainingTime"','"event"','"userDBID"','"attakerDBID"','"data"')

# Hooks ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

from gui.mods.hook_methods import g_overrideLib

@g_overrideLib.registerEvent(PlayerAvatar, 'showTracer')
def new_showTracer(self, shooterID, shotID, isRicochet, effectsIndex, *a, **k):
    if LOG_EVENTS:
        shellName = ''
        for shot in self.arena.vehicles[shooterID]['vehicleType'].gun.shots:
            if effectsIndex == shot.shell.effectsIndex:
                shellName = shot.shell.name
        g_replayCtrl = BattleReplay.g_replayCtrl
        eventInfo = ('%s' % self.arenaUniqueID,
                     ('%.3f' % (g_replayCtrl.getArenaLength() if g_replayCtrl.isPlaying else \
                                self.arena.periodEndTime - BigWorld.serverTime())).replace('.',','),
                     '"PlayerAvatar.showTracer"',
                     '%s' % self.arena.vehicles[shooterID]['accountDBID'],
                     '',
                     json.dumps({'isRicochet':isRicochet, 'effectsIndex':effectsIndex, 'shellName':shellName}))
        printStrings(LOG_EVENTS_FILENAME, eventInfo)

@g_overrideLib.registerEvent(Vehicle, 'showDamageFromShot')
def new_showDamageFromShot(self, attackerID, points, effectsIndex, damageFactor, *a, **k):
    if LOG_EVENTS:
        player = BigWorld.player()
        shellName = ''
        for shot in player.arena.vehicles[attackerID]['vehicleType'].gun.shots:
            if effectsIndex == shot.shell.effectsIndex:
                shellName = shot.shell.name
        g_replayCtrl = BattleReplay.g_replayCtrl
        effectsDescr = vehicles.g_cache.shotEffects[effectsIndex]
        maxHitEffectCode, decodedPoints, maxDamagedComponent = DamageFromShotDecoder.decodeHitPoints(points, self.appearance.collisions)
        hasPiercedHit = DamageFromShotDecoder.hasDamaged(maxHitEffectCode)
        eventInfo = ('%s' % player.arenaUniqueID,
                     ('%.3f' % (g_replayCtrl.getArenaLength() if g_replayCtrl.isPlaying else \
                                player.arena.periodEndTime - BigWorld.serverTime())).replace('.',','),
                     '"Vehicle.showDamageFromShot"',
                     '%s' % player.arena.vehicles[self.id]['accountDBID'],
                     '%s' % player.arena.vehicles[attackerID]['accountDBID'],
                     json.dumps({'effectsIndex':effectsIndex, 'shellName':shellName, 'damageFactor':damageFactor, \
                                 'maxHitEffectCode':VEHICLE_HIT_EFFECT_NAMES.get(maxHitEffectCode), 'maxDamagedComponent':maxDamagedComponent, \
                                 'hasPiercedHit':hasPiercedHit}))
        printStrings(LOG_EVENTS_FILENAME, eventInfo)

@g_overrideLib.registerEvent(Vehicle, 'showDamageFromExplosion')
def new_showDamageFromExplosion(self, attackerID, center, effectsIndex, damageFactor, *a, **k):
    if LOG_EVENTS:
        player = BigWorld.player()
        shellName = ''
        for shot in player.arena.vehicles[attackerID]['vehicleType'].gun.shots:
            if effectsIndex == shot.shell.effectsIndex:
                shellName = shot.shell.name
        g_replayCtrl = BattleReplay.g_replayCtrl
        eventInfo = ('%s' % player.arenaUniqueID,
                     ('%.3f' % (g_replayCtrl.getArenaLength() if g_replayCtrl.isPlaying else \
                                player.arena.periodEndTime - BigWorld.serverTime())).replace('.',','),
                     '"Vehicle.showDamageFromExplosion"',
                     '%s' % player.arena.vehicles[self.id]['accountDBID'],
                     '%s' % player.arena.vehicles[attackerID]['accountDBID'],
                     json.dumps({'effectsIndex':effectsIndex, 'shellName':shellName, 'damageFactor':damageFactor}))
        printStrings(LOG_EVENTS_FILENAME, eventInfo)

def onBattleLoaded(statistic):
    if LOG_BATTLES:
        player = BigWorld.player()
        araneInfo = None
        g_replayCtrl = BattleReplay.g_replayCtrl
        if g_replayCtrl.isPlaying or g_replayCtrl.isRecording:
            arenaInfo = g_replayCtrl._BattleReplay__replayCtrl.getArenaInfoStr()
            if arenaInfo and isinstance(arenaInfo, str):
                try:
                    arenaInfo = json.loads(arenaInfo)
                except:
                    pass
        if arenaInfo:
            dateTime = arenaInfo.get('dateTime','')
            serverName = arenaInfo.get('serverName','')
        else:
            now = datetime.now()
            dateTime = '%02d.%02d.%04d %02d:%02d:%02d' % (now.day, now.month, now.year, now.hour, now.minute, now.second)
            serverName = g_replayCtrl.connectionMgr.serverUserName
        vType = statistic.base[player.playerVehicleID]
        battleInfo = ('%s' % player.arenaUniqueID,
                      dateTime,
                      '"%s"' % serverName,
                      '%s' % vType['accountDBID'],
                      '"%s"' % vType['userName'],
                      '"%s"' % tankTypeAbb(vType['type']['tag']),
                      '"%s"' % vType['name'],
                      '%d' % vType['level'],
                      '"%d(%s)"' % (player.arenaGuiType, ARENA_GUI_TYPE_LABEL.LABELS.get(player.arenaGuiType)),
                      '"%d(%s)"' % (player.arenaTypeID, getArenaGeomentryName(player.arenaTypeID)),
                      '"%d(%s)"' % (player.arenaBonusType, BONUS_TYPE_NAMES.get(player.arenaBonusType)),
                      '"%d(%s)"' % (player.arenaExtraData['arenaKind'], SeasonTypeNames[SeasonType.fromArenaKind(player.arenaExtraData['arenaKind'])]),
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
            playerInfo = ['%s' % BigWorld.player().arenaUniqueID,
                          '%s' % vType['accountDBID'],
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
    g_XVMStatisticsEvents.OnStatsBattleLoaded += onXVMBattleLoaded
    g_StatisticEvents.OnBattleLoaded += onBattleLoaded

    CONFIG_FILENAME = getConfigFileName()
    if CONFIG_FILENAME is not None:
        #Config ------------------------------------------
        config = json.loads(re.compile('(/\*(.|\n)*?\*/)|((#|//).*?$)', re.I | re.M).sub('', codecs.open(CONFIG_FILENAME, 'r', 'utf-8-sig').read()))
        logPath = getLogPath(config['System']['Dir'] + ('/log_' + datetime.now().strftime('%d%m%y_%H%M%S_%f')[:17] if config['System']['UniquePostfix'] else ''))
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