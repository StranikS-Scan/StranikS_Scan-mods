# -*- coding: utf-8 -*-

__version__ = 'V1.1 P2.7 W1.5.1 04.08.2019'
__author__  = 'StranikS_Scan'

import BigWorld, GUI
from BattleReplay import g_replayCtrl
from Avatar import PlayerAvatar
from VehicleGunRotator import VehicleGunRotator
from vehicle_systems.tankStructure import TankPartNames
from helpers.time_utils import getTimeLeftFormat
from copy import deepcopy

from spg_dispersion_methods.hook import g_overrideLib
from spg_dispersion_methods.gui_text import _TextLabel, g_guiTexts
from spg_dispersion_methods.log import _CSVLog, g_Logs

CSV_VERSION  = '1.1'

DISTANCE_MASK         = 'Distance: %s'
GUN_POSITION_MASK     = 'GunPos: %s'
MARKER_POSITION_MASK  = 'MarkerPos: %s'
SERVER_POSITION_MASK  = 'ServerPos: %s'
DIS_ANGLE_MASK        = 'DisAngle: %s'
DIS_ANGLE_SERVER_MASK = 'DisAngleServer: %s'
HITS_INFO_MASK        = 'ShotID: %s, HitDisAbsMarker: %s, HitDisAbsServer: %s'
STATE_STORED_MASK     = 'SightState: %s'

g_sightState = {'distance': None,
                'gunPos': None,
                'markerPos': None, 
                'serverPos': None,
                'disAngle': None,
                'disAngleServer': None}
g_sightStateStored = None

def getTimeLeft():
    time = g_replayCtrl.getArenaLength() if g_replayCtrl.isPlaying else BigWorld.player().arena.periodEndTime - BigWorld.serverTime()
    return '00:' + getTimeLeftFormat(time), ('%.3f' % time).replace('.',',')

@g_overrideLib.overrideMethod(PlayerAvatar, 'enableServerAim')
def new_enableServerAim(base, self, *a, **k):
    base(self, True)

@g_overrideLib.registerEvent(PlayerAvatar, 'shoot', False, True)
def shoot(self, isRepeat=False):
    global g_sightStateStored
    if not g_sightStateStored or not isRepeat:
        g_sightStateStored = deepcopy(g_sightState)
        g_guiTexts['spgStateStored'].text(STATE_STORED_MASK % 'FIXED')

@g_overrideLib.registerEvent(PlayerAvatar, 'updateGunMarker', False, True)
def new_updateGunMarker(self, vehicleID, shotPos, shotVec, dispersionAngle, *a, **k): #GET SERVER INFO
    global g_sightState
    g_sightState['disAngleServer'] = dispersionAngle
    g_guiTexts['spgDisAngleServer'].text(DIS_ANGLE_SERVER_MASK % dispersionAngle)
    g_sightState['serverPos'] = serverPos = self.gunRotator._VehicleGunRotator__getGunMarkerPosition(shotPos, shotVec, (dispersionAngle, dispersionAngle))[0]
    g_guiTexts['spgServerPosition'].text(SERVER_POSITION_MASK % str(serverPos))

@g_overrideLib.registerEvent(VehicleGunRotator, '_VehicleGunRotator__updateGunMarker')
def new_VehicleGunRotator__updateGunMarker(self, *a, **k): #POST SERVER INFO
    global g_sightState
    player = BigWorld.player()
    if player.vehicle and player.vehicle.isStarted and player.vehicle.appearance:
        gunPos = player.vehicle.appearance.compoundModel.node(TankPartNames.GUN).position 
    else:
        gunPos = player.getOwnVehiclePosition()
        gunPos += player.vehicleTypeDescriptor.hull.turretPositions[0] + player.vehicleTypeDescriptor.turret.gunPosition
    g_sightState['gunPos'] = gunPos
    g_guiTexts['spgGunPosition'].text(GUN_POSITION_MASK % str(gunPos))
    #---
    shotPos, shotVec = self.getCurShotPosition()
    g_sightState['markerPos'] = markerPos = self._VehicleGunRotator__getGunMarkerPosition(shotPos, shotVec, self._VehicleGunRotator__dispersionAngles)[0]
    g_guiTexts['spgMarkerPosition'].text(MARKER_POSITION_MASK % str(markerPos))
    #---
    g_sightState['distance'] = distance = gunPos.distTo(markerPos)
    g_guiTexts['spgDistance'].text(DISTANCE_MASK % distance)
    #---
    g_sightState['disAngle'] = dispersionAngle = self._VehicleGunRotator__dispersionAngles[0]
    g_guiTexts['spgDisAngle'].text(DIS_ANGLE_MASK % dispersionAngle)

@g_overrideLib.registerEvent(PlayerAvatar, 'explodeProjectile')
def new_explodeProjectile(self, shotID, effectsIndex, effectMaterialIndex, endPoint, velocityDir, *a, **k):
    global g_sightStateStored
    if self.isOnArena:
        devMarker = endPoint - g_sightStateStored['markerPos'] if g_sightStateStored else None
        disAbsMarker = devMarker.length if devMarker else None 
        devServer = endPoint - g_sightStateStored['serverPos'] if g_sightStateStored and g_sightStateStored['serverPos'] else None
        disAbsServer = devServer.length if devServer else None
        g_guiTexts['spgHitsInfo'].add(HITS_INFO_MASK % (shotID, disAbsMarker, disAbsServer))
        #---
        timeLeft, timeLeftSec = getTimeLeft()
        hitsLog = g_Logs['Hits']
        hitsLog.addValues([shotID,
                           timeLeft,
                           timeLeftSec])
        hitsLog.addValues(g_sightStateStored['gunPos'] if g_sightStateStored and g_sightStateStored['gunPos'] else 3*[''])
        hitsLog.addValues(g_sightStateStored['markerPos'] if g_sightStateStored and g_sightStateStored['markerPos'] else 3*[''])
        hitsLog.addValues(g_sightStateStored['serverPos'] if g_sightStateStored and g_sightStateStored['serverPos'] else 3*[''])
        hitsLog.addValues([g_sightStateStored['distance'] if g_sightStateStored else '',
                           g_sightStateStored['disAngle'] if g_sightStateStored else '',
                           g_sightStateStored['disAngleServer'] if g_sightStateStored else '',
                           endPoint])
        hitsLog.addValues(devMarker if devMarker else 3*[''])
        hitsLog.addValues(disAbsMarker)
        hitsLog.addValues(devServer if devServer else 3*[''])
        hitsLog.addValues(disAbsServer)
        hitsLog.writeStoreValues()
        if g_sightStateStored:
            g_sightStateStored = None
            g_guiTexts['spgStateStored'].text(STATE_STORED_MASK % '')

@g_overrideLib.registerEvent(PlayerAvatar, '_PlayerAvatar__startGUI')
def new__startGUI(self):
    BigWorld.player().enableServerAim(True)
    #---
    g_Logs['Hits'] = hitsLog = _CSVLog('hits_ver_%csv_%date%time.csv', 'logs/SPGDispersion', CSV_VERSION)
    hitsLog.floatMask = '%.10f'
    hitsLog.vectorToXYZ = True
    hitsLog.addHeaders(['ShotID', 
                        'timeLeft', 
                        'timeLeftSec',
                        'GunPos_X', 'GunPos_Y', 'GunPos_Z',
                        'MarkerPos_X', 'MarkerPos_Y', 'MarkerPos_Z',
                        'ServerPos_X', 'ServerPos_Y', 'ServerPos_Z',
                        'Distance',
                        'DisAngle',
                        'DisAngleServer',
                        'HitPos_X', 'HitPos_Y', 'HitPos_Z',
                        'HitDevMarker_X', 'HitDevMarker_Y', 'HitDevMarker_Z', 
                        'HitDisAbsMarker', 
                        'HitDevServer_X', 'HitDevServer_Y', 'HitDevServer_Z',
                        'HitDisAbsServer'])
    hitsLog.writeStoreHeaders()
    #---
    g_guiTexts['spgDistance'] = spgDistance = _TextLabel(-1000, -500, '00EDFFFF', 'default_small.font')
    spgDistance.text(DISTANCE_MASK % 'None')
    spgDistance.show()
    g_guiTexts['spgDisAngle'] = spgDisAngle = _TextLabel(-1000, -400, 'FFEB14FF', 'default_small.font')
    spgDisAngle.text(DIS_ANGLE_MASK % 'None')
    spgDisAngle.show()
    g_guiTexts['spgDisAngleServer'] = spgDisAngleServer = _TextLabel(-1000, -300, 'FFEB14FF', 'default_small.font')
    spgDisAngleServer.text(DIS_ANGLE_SERVER_MASK % 'None')
    spgDisAngleServer.show()
    g_guiTexts['spgGunPosition'] = spgGunPosition = _TextLabel(-1000, -200, '00EDFFFF', 'default_small.font')
    spgGunPosition.text(GUN_POSITION_MASK % 'None')
    spgGunPosition.show()
    g_guiTexts['spgMarkerPosition'] = spgMarkerPosition = _TextLabel(-1000, -100, 'FFEB14FF', 'default_small.font')
    spgMarkerPosition.text(MARKER_POSITION_MASK % 'None')
    spgMarkerPosition.show()
    g_guiTexts['spgServerPosition'] = spgServerPosition = _TextLabel(-1000, 0, 'FFEB14FF', 'default_small.font')
    spgServerPosition.text(SERVER_POSITION_MASK % 'None')
    spgServerPosition.show()
    g_guiTexts['spgHitsInfo'] = spgHitsInfo = _TextLabel(200, -500, '00EDFFFF', 'default_small.font', 15)
    spgHitsInfo.text('')
    spgHitsInfo.show()
    #---
    g_guiTexts['spgStateStored'] = spgStateStored = _TextLabel(0, -600, '00EDFFFF', 'default_small.font')
    spgStateStored.text(STATE_STORED_MASK % '')
    spgStateStored.show()

@g_overrideLib.registerEvent(PlayerAvatar, 'onBecomeNonPlayer', False, True)
def new_onBecomeNonPlayer(self):
    for log in g_Logs:
        g_Logs[log].destroy()
    g_Logs.clear()
    for text in g_guiTexts:
        g_guiTexts[text].destroy()
    g_guiTexts.clear()

print '[%s] Loading mod: "spg_dispersion" %s (http://www.koreanrandom.com)' % (__author__, __version__)