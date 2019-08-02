# -*- coding: utf-8 -*-

__version__ = 'V1.0 P2.7 W1.5.1 02.08.2019'
__author__  = 'StranikS_Scan'

import BigWorld, GUI
from BattleReplay import g_replayCtrl
from Avatar import PlayerAvatar
from VehicleGunRotator import VehicleGunRotator
from vehicle_systems.tankStructure import TankPartNames
from helpers.time_utils import getTimeLeftFormat

import os, codecs
from datetime import datetime

from spg_dispersion_methods.hook import g_overrideLib
from spg_dispersion_methods.gui_text import _TextLabel

GUN_POSITION_MASK    = 'GunPos: %s'
MARKER_POSITION_MASK = 'MarkerPos: %s'
SERVER_POSITION_MASK = 'ServerPos: %s'
HITS_INFO_MASK       = 'ShotID: %d, HitDisAbsMarker: %.10f, HitDisAbsServer: %.10f'

CSV_VERSION  = '1.0'
LOG_HITS = None
HITS_HEADER = ('"ShotID"', '"timeLeft"', '"timeLeftSec"', '"GunPos_X"', '"GunPos_Y"', '"GunPos_Z"', '"MarkerPos_X"', '"MarkerPos_Y"', '"MarkerPos_Z"',
               '"ServerPos_X"', '"ServerPos_Y"', '"ServerPos_Z"', '"HitPos_X"', '"HitPos_Y"', '"HitPos_Z"',
               '"HitDevMarker_X"', '"HitDevMarker_Y"', '"HitDevMarker_Z"', '"HitDisAbsMarker"', 
               '"HitDevServer_X"', '"HitDevServer_Y"', '"HitDevServer_Z"', '"HitDisAbsServer"')

_STORAGE = {'gunPos': None,
            'markerPos': None, 
            'serverPos': None}

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

def printStrings(filename, value): 
    if filename is not None:
        with codecs.open(filename, 'a', 'utf-8-sig') as file:
            if isinstance(value, list) or isinstance(value, tuple):
                file.write(';'.join(value) + '\n')
            else:
                file.write(value + '\n')

def getTimeLeft():
    time = g_replayCtrl.getArenaLength() if g_replayCtrl.isPlaying else BigWorld.player().arena.periodEndTime - BigWorld.serverTime()
    return '00:'+getTimeLeftFormat(time), ('%.3f' % time).replace('.',',')

@g_overrideLib.overrideMethod(PlayerAvatar, 'enableServerAim')
def new_enableServerAim(base, self, *a, **k):
    base(self, True)

@g_overrideLib.registerEvent(PlayerAvatar, 'updateGunMarker', False, True)
def new_updateGunMarker(self, vehicleID, shotPos, shotVec, dispersionAngle, *a, **k): #GET SERVER INFO
    global _STORAGE
    _STORAGE['serverPos'] = serverPos = self.gunRotator._VehicleGunRotator__getGunMarkerPosition(shotPos, shotVec, (dispersionAngle, dispersionAngle))[0]
    self.textSPGServerPosition.text(SERVER_POSITION_MASK % str(serverPos))

@g_overrideLib.registerEvent(VehicleGunRotator, '_VehicleGunRotator__updateGunMarker')
def new_VehicleGunRotator__updateGunMarker(self, *a, **k): #POST SERVER INFO
    global _STORAGE
    player = BigWorld.player()
    if player.vehicle and player.vehicle.isStarted and player.vehicle.appearance:
        gunPos = player.vehicle.appearance.compoundModel.node(TankPartNames.GUN).position 
    else:
        gunPos = player.getOwnVehiclePosition()
        gunPos += player.vehicleTypeDescriptor.hull.turretPositions[0] + player.vehicleTypeDescriptor.turret.gunPosition
    _STORAGE['gunPos'] = gunPos
    player.textSPGGunPosition.text(GUN_POSITION_MASK % str(gunPos))
    #---
    shotPos, shotVec = self.getCurShotPosition()
    _STORAGE['markerPos'] = markerPos = self._VehicleGunRotator__getGunMarkerPosition(shotPos, shotVec, self._VehicleGunRotator__dispersionAngles)[0]
    player.textSPGMarkerPosition.text(MARKER_POSITION_MASK % str(markerPos))

@g_overrideLib.registerEvent(PlayerAvatar, 'explodeProjectile')
def new_explodeProjectile(self, shotID, effectsIndex, effectMaterialIndex, endPoint, velocityDir, *a, **k):
    devMarker = endPoint - _STORAGE['markerPos']
    disAbsMarker = devMarker.length
    isServer = _STORAGE['serverPos'] != None
    if isServer:
        devServer = endPoint - _STORAGE['serverPos']
        disAbsServer = devMarker.length
    else:
        disAbsServer = None
    self.textSPGHitsInfo.add(HITS_INFO_MASK % (shotID, disAbsMarker, disAbsServer))
    timeLeft, timeLeftSec = getTimeLeft()
    HitInfo = ('%d' % shotID,
               timeLeft, 
               timeLeftSec,
               '%.10f' % _STORAGE['gunPos'][0],
               '%.10f' % _STORAGE['gunPos'][1],
               '%.10f' % _STORAGE['gunPos'][2],
               '%.10f' % _STORAGE['markerPos'][0],
               '%.10f' % _STORAGE['markerPos'][1],
               '%.10f' % _STORAGE['markerPos'][2],
               '%.10f' % _STORAGE['serverPos'][0] if isServer else '',
               '%.10f' % _STORAGE['serverPos'][1] if isServer else '',
               '%.10f' % _STORAGE['serverPos'][2] if isServer else '',
               '%.10f' % endPoint[0],
               '%.10f' % endPoint[1],
               '%.10f' % endPoint[2],
               '%.10f' % devMarker[0],
               '%.10f' % devMarker[1],
               '%.10f' % devMarker[2],
               '%.10f' % disAbsMarker,
               '%.10f' % devMarker[0] if isServer else '',
               '%.10f' % devMarker[1] if isServer else '',
               '%.10f' % devMarker[2] if isServer else '',
               '%.10f' % disAbsServer if isServer else '')
    printStrings(LOG_HITS, HitInfo)

@g_overrideLib.registerEvent(PlayerAvatar, '_PlayerAvatar__startGUI')
def new__startGUI(self):
    global LOG_HITS
    BigWorld.player().enableServerAim(True)
    #---
    logPath = getLogPath('logs\SPGDispersion')
    LOG_HITS = logPath + 'hits_ver_%s_%s.csv' % (CSV_VERSION, datetime.now().strftime('%d%m%y%H%M%S%f')[:15])
    if not os.path.exists(LOG_HITS):
        printStrings(LOG_HITS, HITS_HEADER)
    #---
    self.textSPGGunPosition = _TextLabel(-1000, -500, '00EDFFFF', 'default_small.font')
    self.textSPGGunPosition.text(GUN_POSITION_MASK % 'None')
    self.textSPGGunPosition.show()
    #---
    self.textSPGMarkerPosition = _TextLabel(-1000, -400, 'FB7D09FF', 'default_small.font')
    self.textSPGMarkerPosition.text(MARKER_POSITION_MASK % 'None')
    self.textSPGMarkerPosition.show()
    #---
    self.textSPGServerPosition = _TextLabel(-1000, -300, 'FB7D09FF', 'default_small.font')
    self.textSPGServerPosition.text(SERVER_POSITION_MASK % 'None')
    self.textSPGServerPosition.show()
    #---
    self.textSPGHitsInfo = _TextLabel(200, -500, '00EDFFFF', 'default_small.font', 15)
    self.textSPGHitsInfo.text('')
    self.textSPGHitsInfo.show()

@g_overrideLib.registerEvent(PlayerAvatar, 'onBecomeNonPlayer', False, True)
def new_onBecomeNonPlayer(self):
    self.textSPGGunPosition.destroy()
    self.textSPGGunPosition = None
    #---
    self.textSPGMarkerPosition.destroy()
    self.textSPGMarkerPosition = None
    #---
    self.textSPGServerPosition.destroy()
    self.textSPGServerPosition = None
    #---
    self.textSPGHitsInfo.destroy()
    self.textSPGHitsInfo = None

print '[%s] Loading mod: "spg_dispersion" %s (http://www.koreanrandom.com)' % (__author__, __version__)