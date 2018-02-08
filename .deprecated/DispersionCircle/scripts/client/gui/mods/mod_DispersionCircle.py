# -*- coding: utf-8 -*-

__author__  = 'StranikS_Scan'
__version__ = 'V2.0 P2.7 W0.9.17 10.01.2017'

print '[%s] Loading mod: DispersionCircle %s (http://www.koreanrandom.com/forum/topic/27695-)' % (__author__, __version__)

import BigWorld, GUI
from Avatar import PlayerAvatar
from VehicleGunRotator import VehicleGunRotator
from constants import SERVER_TICK_LENGTH
from AvatarInputHandler import AvatarInputHandler
from AvatarInputHandler.AimingSystems.SniperAimingSystem import SniperAimingSystem
from AvatarInputHandler.DynamicCameras.ArcadeCamera import ArcadeCamera, _InputInertia
from AvatarInputHandler.DynamicCameras.SniperCamera import SniperCamera
from AvatarInputHandler.DynamicCameras.StrategicCamera import StrategicCamera

from AvatarInputHandler import gun_marker_ctrl
from gui.Scaleform.daapi.view.battle.shared.crosshair import gm_factory

from AvatarInputHandler.gun_marker_ctrl import _MARKER_TYPE, _MARKER_FLAG, _GunMarkerController, _makeWorldMatrix, _calcScale, \
_GunMarkersDPFactory, _SPGGunMarkerController, _DefaultGunMarkerController, _GunMarkersDecorator
from skeletons.account_helpers.settings_core import ISettingsCore

from AvatarInputHandler import mathUtils
import BattleReplay
from helpers import dependency, EffectsList
import ResMgr, os, codecs, json, re
import math, Math

# Consts ..........................................................................

REPLACE_ORIGINAL_CIRCLE = False
USE_SERVER_DISPERSION = False
DISPERSION_CIRCLE_SCALE = 1.0
HORIZONTAL_STABILIZER  = True
REMOVE_DINAMYC_EFFECTS = True
REMOVE_DAMAGE_EFFECTS  = True
CONFIG_FILENAME = None

# Classes and functions ===========================================================

def getRoot():
    root = ''
    values = ResMgr.openSection('../paths.xml')['Paths'].values()[0:2]
    for value in values:
        root = value.asString + '/scripts/client/gui/mods/'
        break
    return root

def getConfigFileName():
    filename = getRoot() + 'DispersionCircle.cfg'
    return filename if os.path.exists(filename) else None

CONFIG_FILENAME = getConfigFileName()

if CONFIG_FILENAME is not None:
    config = json.loads(re.compile('(/\*(.|\n)*?\*/)|((#|//).*?$)', re.I | re.M).sub('', codecs.open(CONFIG_FILENAME, 'r', 'utf-8-sig').read()))
    REPLACE_ORIGINAL_CIRCLE = config['System']['ReplaceOriginalCircle']
    USE_SERVER_DISPERSION   = config['System']['UseServerDispersion']
    DISPERSION_CIRCLE_SCALE = config['System']['DispersionCircleScale']
    HORIZONTAL_STABILIZER  = config['CameraTuner']['HorizontalStabilizer']
    REMOVE_DINAMYC_EFFECTS = config['CameraTuner']['Remove_DinamycEffects']
    REMOVE_DAMAGE_EFFECTS  = config['CameraTuner']['Remove_DamageEffects']

# -----------------------------------------------------------------------

def new_update(self, markerType, position, dir, size, relaxTime, collData):
    self._position = position

_GunMarkerController.update = new_update

class new_DefaultGunMarkerController(_GunMarkerController):
    settingsCore = dependency.descriptor(ISettingsCore)

    def __init__(self, gunMakerType, dataProvider, enabledFlag=_MARKER_FLAG.UNDEFINED):
        super(new_DefaultGunMarkerController, self).__init__(gunMakerType, dataProvider, enabledFlag=enabledFlag)
        self.__replSwitchTime = 0.0
        self.__curSize = 0.0
        self.__screenRatio = 0.0

    def enable(self):
        super(new_DefaultGunMarkerController, self).enable()
        self.__updateScreenRatio()
        replayCtrl = BattleReplay.g_replayCtrl
        if replayCtrl.isPlaying and replayCtrl.isClientReady:
            self.__replSwitchTime = 0.2

    def update(self, markerType, pos, dir, sizeVector, relaxTime, collData):
        super(new_DefaultGunMarkerController, self).update(markerType, pos, dir, sizeVector, relaxTime, collData)
        positionMatrix = Math.Matrix()
        positionMatrix.setTranslate(pos)
        self._updateMatrixProvider(positionMatrix, relaxTime)
        size = sizeVector[0] #!!!
        replayCtrl = BattleReplay.g_replayCtrl
        if replayCtrl.isPlaying and replayCtrl.isClientReady:
            s = replayCtrl.getArcadeGunMarkerSize()
            if s != -1.0:
                size = s
        elif replayCtrl.isRecording:
            if replayCtrl.isServerAim and self._gunMarkerType == _MARKER_TYPE.SERVER:
                replayCtrl.setArcadeGunMarkerSize(size)
            elif self._gunMarkerType == _MARKER_TYPE.CLIENT:
                replayCtrl.setArcadeGunMarkerSize(size)
        worldMatrix = _makeWorldMatrix(positionMatrix)
        self.__curSize = _calcScale(worldMatrix, size) * self.__screenRatio * DISPERSION_CIRCLE_SCALE / 2.3 #!!!
        if self.__replSwitchTime > 0.0:
            self.__replSwitchTime -= relaxTime
            self._dataProvider.updateSize(self.__curSize, 0.0)
        else:
            self._dataProvider.updateSize(self.__curSize, relaxTime)

    def onRecreateDevice(self):
        self.__updateScreenRatio()

    def __updateScreenRatio(self):
        self.__screenRatio = GUI.screenResolution()[0] * 0.5

if not REPLACE_ORIGINAL_CIRCLE:
    gun_marker_ctrl.useClientGunMarker = lambda : True
    gun_marker_ctrl.useServerGunMarker = lambda : True
    gun_marker_ctrl.useDefaultGunMarkers = lambda : False
    gm_factory._FACTORIES_COLLECTION = (gm_factory._DevControlMarkersFactory, gm_factory._OptionalMarkersFactory, gm_factory._EquipmentMarkersFactory)

def new_setPosition(self, position, markerType=_MARKER_TYPE.CLIENT):
    if not REPLACE_ORIGINAL_CIRCLE:
        if markerType == _MARKER_TYPE.CLIENT:
            self._GunMarkersDecorator__clientMarker.setPosition(position)
        if USE_SERVER_DISPERSION:
            if markerType == _MARKER_TYPE.SERVER:
                self._GunMarkersDecorator__serverMarker.setPosition(position)
        elif markerType == _MARKER_TYPE.CLIENT:
            self._GunMarkersDecorator__serverMarker.setPosition(position)
    else:
        if USE_SERVER_DISPERSION:
            if markerType == _MARKER_TYPE.SERVER:
                self._GunMarkersDecorator__clientMarker.setPosition(position)
        elif markerType == _MARKER_TYPE.CLIENT:
            self._GunMarkersDecorator__clientMarker.setPosition(position)
        if markerType == _MARKER_TYPE.SERVER:
            self._GunMarkersDecorator__serverMarker.setPosition(position)

_GunMarkersDecorator.setPosition = new_setPosition

def new_update2(self, markerType, position, dir, size, relaxTime, collData):
    if not REPLACE_ORIGINAL_CIRCLE:
        if markerType == _MARKER_TYPE.CLIENT:
            self._GunMarkersDecorator__clientState = (position, relaxTime, collData)
            if self._GunMarkersDecorator__gunMarkersFlags & _MARKER_FLAG.CLIENT_MODE_ENABLED:
                self._GunMarkersDecorator__clientMarker.update(markerType, position, dir, size, relaxTime, collData)
        if USE_SERVER_DISPERSION:
            if markerType == _MARKER_TYPE.SERVER:
                self._GunMarkersDecorator__serverState = (position, relaxTime, collData)
                if self._GunMarkersDecorator__gunMarkersFlags & _MARKER_FLAG.SERVER_MODE_ENABLED:
                    self._GunMarkersDecorator__serverMarker.update(markerType, position, dir, size, relaxTime, collData)
        elif markerType == _MARKER_TYPE.CLIENT:
            self._GunMarkersDecorator__serverState = (position, relaxTime, collData)
            if self._GunMarkersDecorator__gunMarkersFlags & _MARKER_FLAG.SERVER_MODE_ENABLED:
                self._GunMarkersDecorator__serverMarker.update(markerType, position, dir, size, relaxTime, collData)
    else:
        if USE_SERVER_DISPERSION:
            if markerType == _MARKER_TYPE.SERVER:
                self._GunMarkersDecorator__clientState = (position, relaxTime, collData)
                if self._GunMarkersDecorator__gunMarkersFlags & _MARKER_FLAG.CLIENT_MODE_ENABLED:
                    self._GunMarkersDecorator__clientMarker.update(markerType, position, dir, size, relaxTime, collData)
        elif markerType == _MARKER_TYPE.CLIENT:
            self._GunMarkersDecorator__clientState = (position, relaxTime, collData)
            if self._GunMarkersDecorator__gunMarkersFlags & _MARKER_FLAG.CLIENT_MODE_ENABLED:
                self._GunMarkersDecorator__clientMarker.update(markerType, position, dir, size, relaxTime, collData)
        if markerType == _MARKER_TYPE.SERVER:
            self._GunMarkersDecorator__serverState = (position, relaxTime, collData)
            if self._GunMarkersDecorator__gunMarkersFlags & _MARKER_FLAG.SERVER_MODE_ENABLED:
                self._GunMarkersDecorator__serverMarker.update(markerType, position, dir, size, relaxTime, collData)

_GunMarkersDecorator.update = new_update2

def new_createGunMarker(isStrategic):
    factory = _GunMarkersDPFactory()
    if isStrategic:
        clientMarker = _SPGGunMarkerController(_MARKER_TYPE.CLIENT, factory.getClientSPGProvider())
        serverMarker = _SPGGunMarkerController(_MARKER_TYPE.SERVER, factory.getServerSPGProvider())
    else:
        clientMarker = _DefaultGunMarkerController(_MARKER_TYPE.CLIENT, factory.getClientProvider()) if not REPLACE_ORIGINAL_CIRCLE else \
                       new_DefaultGunMarkerController(_MARKER_TYPE.CLIENT, factory.getClientProvider())
        serverMarker = new_DefaultGunMarkerController(_MARKER_TYPE.SERVER, factory.getServerProvider())
    return _GunMarkersDecorator(clientMarker, serverMarker)

gun_marker_ctrl.createGunMarker = new_createGunMarker

# -----------------------------------------------------------------------

def new_ArcadeCamera__init__(self, dataSec, defaultOffset=None):
    old_ArcadeCamera__init__(self, dataSec, defaultOffset)
    self._ArcadeCamera__dynamicCfg['accelerationSensitivity']     = 0.0
    self._ArcadeCamera__dynamicCfg['frontImpulseToPitchRatio']    = 0.0
    self._ArcadeCamera__dynamicCfg['sideImpulseToRollRatio']      = 0.0
    self._ArcadeCamera__dynamicCfg['sideImpulseToYawRatio']       = 0.0
    self._ArcadeCamera__dynamicCfg['accelerationThreshold']       = 0.0
    self._ArcadeCamera__dynamicCfg['accelerationMax']             = 0.0
    self._ArcadeCamera__dynamicCfg['maxShotImpulseDistance']      = 0.0
    self._ArcadeCamera__dynamicCfg['maxExplosionImpulseDistance'] = 0.0
    self._ArcadeCamera__dynamicCfg['zoomExposure']                = 0.0
    for x in self._ArcadeCamera__dynamicCfg['impulseSensitivities']:
        self._ArcadeCamera__dynamicCfg['impulseSensitivities'][x] = 0.0
    for x in self._ArcadeCamera__dynamicCfg['impulseLimits']:
        self._ArcadeCamera__dynamicCfg['impulseLimits'][x] = (0.0, 0.0)
    for x in self._ArcadeCamera__dynamicCfg['noiseSensitivities']:
        self._ArcadeCamera__dynamicCfg['noiseSensitivities'][x] = 0.0
    for x in self._ArcadeCamera__dynamicCfg['noiseLimits']:
        self._ArcadeCamera__dynamicCfg['noiseLimits'][x] = (0.0, 0.0)

def new_SniperCamera__init__(self, dataSec, defaultOffset=None, binoculars=None):
    old_SniperCamera__init__(self, dataSec, defaultOffset, binoculars)
    self._SniperCamera__dynamicCfg['accelerationSensitivity']     = Math.Vector3(0.0, 0.0, 0.0)
    self._SniperCamera__dynamicCfg['accelerationThreshold']       = 0.0
    self._SniperCamera__dynamicCfg['accelerationMax']             = 0.0
    self._SniperCamera__dynamicCfg['maxShotImpulseDistance']      = 0.0
    self._SniperCamera__dynamicCfg['maxExplosionImpulseDistance'] = 0.0
    self._SniperCamera__dynamicCfg['impulsePartToRoll']           = 0.0
    self._SniperCamera__dynamicCfg['pivotShift']                  = Math.Vector3(0, -0.5, 0)
    for x in self._SniperCamera__dynamicCfg['impulseSensitivities']:
        self._SniperCamera__dynamicCfg['impulseSensitivities'][x] = 0.0
    for x in self._SniperCamera__dynamicCfg['impulseLimits']:
        self._SniperCamera__dynamicCfg['impulseLimits'][x] = (0.0, 0.0)
    for x in self._SniperCamera__dynamicCfg['noiseSensitivities']:
        self._SniperCamera__dynamicCfg['noiseSensitivities'][x] = 0.0
    for x in self._SniperCamera__dynamicCfg['noiseLimits']:
        self._SniperCamera__dynamicCfg['noiseLimits'][x] = (0.0, 0.0)

def new_StrategicCamera__init__(self, dataSec):
    old_StrategicCamera__init__(self, dataSec)
    for x in self._StrategicCamera__dynamicCfg['impulseSensitivities']:
        self._StrategicCamera__dynamicCfg['impulseSensitivities'][x] = 0.0
    for x in self._StrategicCamera__dynamicCfg['impulseLimits']:
        self._StrategicCamera__dynamicCfg['impulseLimits'][x] = (0.0, 0.0)
    for x in self._StrategicCamera__dynamicCfg['noiseSensitivities']:
        self._StrategicCamera__dynamicCfg['noiseSensitivities'][x] = 0.0
    for x in self._StrategicCamera__dynamicCfg['noiseLimits']:
        self._StrategicCamera__dynamicCfg['noiseLimits'][x] = (0.0, 0.0)

def new_EnableHorizontalStabilizerRuntime(self, enable):
    yawConstraint = math.pi * 2.1 if HORIZONTAL_STABILIZER else 0.0
    self._SniperAimingSystem__yprDeviationConstraints.x = yawConstraint

def new_SmothCamera_InputInertia_glide(self, posDelta):
    self._InputInertia__deltaEasing.reset(posDelta, Math.Vector3(0.0), 0.001)

def new_SmothCamera_InputInertia_glideFov(self, newRelativeFocusDist):
    minMult, maxMult = self._InputInertia__minMaxZoomMultiplier
    endMult = mathUtils.lerp(minMult, maxMult, newRelativeFocusDist)
    self._InputInertia__zoomMultiplierEasing.reset(self._InputInertia__zoomMultiplierEasing.value, endMult, 0.001)

def new_PyOscillator(mass, stiffness, drag, constraints):
    return old_PyOscillator(1e-05, (1e-05, 1e-05, 1e-05), (1e-05, 1e-05, 1e-05), (0.0, 0.0, 0.0))

def new_PyNoiseOscillator(mass, stiffness, drag):
    return old_PyNoiseOscillator(1e-05, (1e-05, 1e-05, 1e-05), (1e-05, 1e-05, 1e-05))

def new_PyRandomNoiseOscillatorFlat(mass, stiffness, drag):
    return old_PyRandomNoiseOscillatorFlat(1e-05, 1e-05, 1e-05)

def new_PyRandomNoiseOscillatorSpherical(mass, stiffness, drag, scaleCoeff):
    return old_PyRandomNoiseOscillatorSpherical(1e-05, 1e-05, 1e-05, (0.0, 0.0, 0.0))

def new_null_effect(self, model, list, args):
    pass

# -----------------------------------------------------------------------

if USE_SERVER_DISPERSION:

    def new_setShotPosition(self, vehicleID, shotPos, shotVec, dispersionAngle):
        if self._VehicleGunRotator__clientMode and self._VehicleGunRotator__showServerMarker:
            old_setShotPosition(self, vehicleID, shotPos, shotVec, dispersionAngle)
        else:
            dispersionAngles = {}
            dispersionAngles[0] = dispersionAngles[1] = dispersionAngle
            markerPos, markerDir, markerSize, idealMarkerSize, collData = self._VehicleGunRotator__getGunMarkerPosition(shotPos, shotVec, self._VehicleGunRotator__dispersionAngles)
            self._VehicleGunRotator__avatar.inputHandler.updateGunMarker2(markerPos, markerDir, (markerSize, idealMarkerSize), SERVER_TICK_LENGTH, collData)
    
    old_setShotPosition = VehicleGunRotator.setShotPosition
    VehicleGunRotator.setShotPosition = new_setShotPosition

def new_enableServerAim(self, enable):
    old_enableServerAim(self, USE_SERVER_DISPERSION)

old_enableServerAim = PlayerAvatar.enableServerAim
PlayerAvatar.enableServerAim = new_enableServerAim

VehicleGunRotator.applySettings = lambda self, diff: None

def new__startGUI(self):
    old__startGUI(self)
    BigWorld.player().enableServerAim(USE_SERVER_DISPERSION)

old__startGUI = PlayerAvatar._PlayerAvatar__startGUI
PlayerAvatar._PlayerAvatar__startGUI = new__startGUI
        
SniperAimingSystem.enableHorizontalStabilizerRuntime = new_EnableHorizontalStabilizerRuntime

if REMOVE_DAMAGE_EFFECTS:
    EffectsList._FlashBangEffectDesc.create = new_null_effect
    EffectsList._ShockWaveEffectDesc.create = new_null_effect

if REMOVE_DINAMYC_EFFECTS:
    old_ArcadeCamera__init__ = ArcadeCamera.__init__
    ArcadeCamera.__init__ = new_ArcadeCamera__init__
    old_SniperCamera__init__ = SniperCamera.__init__
    SniperCamera.__init__ = new_SniperCamera__init__
    old_StrategicCamera__init__ = StrategicCamera.__init__
    StrategicCamera.__init__ = new_StrategicCamera__init__

    _InputInertia.glide = new_SmothCamera_InputInertia_glide
    _InputInertia.glideFov = new_SmothCamera_InputInertia_glideFov

    old_PyOscillator = Math.PyOscillator
    Math.PyOscillator = new_PyOscillator
    old_PyNoiseOscillator = Math.PyNoiseOscillator
    Math.PyNoiseOscillator = new_PyNoiseOscillator
    old_PyRandomNoiseOscillatorFlat = Math.PyRandomNoiseOscillatorFlat
    Math.PyRandomNoiseOscillatorFlat = new_PyRandomNoiseOscillatorFlat
    old_PyRandomNoiseOscillatorSpherical = Math.PyRandomNoiseOscillatorSpherical
    Math.PyRandomNoiseOscillatorSpherical = new_PyRandomNoiseOscillatorSpherical
