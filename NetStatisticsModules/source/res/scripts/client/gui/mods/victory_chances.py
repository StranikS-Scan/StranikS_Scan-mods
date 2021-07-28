# -*- coding: utf-8 -*-

__author__  = 'StranikS_Scan'
__version__ = 'V2.6 P2.7 W1.13.0 28.07.2021'

import BigWorld
from Event import Event
from constants import SHELL_TYPES
from Avatar import PlayerAvatar
from Vehicle import Vehicle
from vehicle_systems.CompoundAppearance import CompoundAppearance
from items import vehicles
from gui.shared.gui_items.Vehicle import getVehicleClassTag

from methods.hook import g_overrideLib

# Consts .....................................................................

class UPDATE_REASONE():
    VEHICLE_ADDED  = 0
    VEHICLE_DEATH  = 1
    HEALTH_CHANGED = 2

# Static functions ***********************************************************

# Classes ====================================================================

class _StatisticEvents(object):
    def __init__(self):
        self.onBattleLoaded    = Event()
        self.onVehiclesChanged = Event()
        self.onCountChanged    = Event()
        self.onHealthChanged   = Event()
        self.onChanceChanged   = Event()

class _TanksStatistic(object):
    allyChance         = property(lambda self: self.__allyChance)
    enemyChance        = property(lambda self: self.__enemyChance)
    allyTanksCount     = property(lambda self: self.__allyTanksCount)
    enemyTanksCount    = property(lambda self: self.__enemyTanksCount)
    allyTeamHP         = property(lambda self: self.__allyTeamHP)
    enemyTeamHP        = property(lambda self: self.__enemyTeamHP)
    allyTeamOneDamage  = property(lambda self: self.__allyTeamOneDamage)
    enemyTeamOneDamage = property(lambda self: self.__enemyTeamOneDamage)
    allyTeamDPM        = property(lambda self: self.__allyTeamDPM)
    enemyTeamDPM       = property(lambda self: self.__enemyTeamDPM)
    allyTeamForces     = property(lambda self: self.__allyTeamForces)
    enemyTeamForces    = property(lambda self: self.__enemyTeamForces)

    def __init__(self):
        self.__getAllyTanksCount     = lambda withDead=False: sum([1 for value in self.base.itervalues() if not value['isEnemy'] and (withDead or value['isAlive'])])
        self.__getEnemyTanksCount    = lambda withDead=False: sum([1 for value in self.base.itervalues() if value['isEnemy'] and (withDead or value['isAlive'])])
        self.__getAllyTeamHP         = lambda withDead=False: sum([value['hp'] for value in self.base.itervalues() if not value['isEnemy'] and (withDead or value['isAlive'])])
        self.__getEnemyTeamHP        = lambda withDead=False: sum([value['hp'] for value in self.base.itervalues() if value['isEnemy'] and (withDead or value['isAlive'])])
        self.__getAllyTeamOneDamage  = lambda withDead=False: sum([value['gun']['currentDamage'] for value in self.base.itervalues() if not value['isEnemy'] and (withDead or value['isAlive'])])
        self.__getEnemyTeamOneDamage = lambda withDead=False: sum([value['gun']['currentDamage'] for value in self.base.itervalues() if value['isEnemy'] and (withDead or value['isAlive'])])
        self.__getAllyTeamDPM        = lambda withDead=False: sum([value['gun']['currentDpm'] for value in self.base.itervalues() if not value['isEnemy'] and (withDead or value['isAlive'])])
        self.__getEnemyTeamDPM       = lambda withDead=False: sum([value['gun']['currentDpm'] for value in self.base.itervalues() if value['isEnemy'] and (withDead or value['isAlive'])])
        self.__getAllyTeamForces     = lambda withDead=False: sum([value['force'] for value in self.base.itervalues() if not value['isEnemy'] and (withDead or value['isAlive'])])
        self.__getEnemyTeamForces    = lambda withDead=False: sum([value['force'] for value in self.base.itervalues() if value['isEnemy'] and (withDead or value['isAlive'])])
        self.init()

    def init(self):
        self.base = {}
        self.__allyTanksCount     = \
        self.__enemyTanksCount    = \
        self.__allyTeamHP         = \
        self.__enemyTeamHP        = \
        self.__allyTeamOneDamage  = \
        self.__enemyTeamOneDamage = \
        self.__allyTeamDPM        = \
        self.__enemyTeamDPM       = \
        self.__allyTeamForces     = \
        self.__enemyTeamForces    = \
        self.__allyChance         = \
        self.__enemyChance        = \
        self.__allyChance         = \
        self.__enemyChance        = None

    def update(self, reasone, vID):    
        if self.base:
            #Recalc -----------------------------------------------------------
            if reasone <= UPDATE_REASONE.HEALTH_CHANGED:
                self.__allyTeamHP         = self.__getAllyTeamHP()
                self.__enemyTeamHP        = self.__getEnemyTeamHP()
            if reasone <= UPDATE_REASONE.VEHICLE_DEATH:
                self.__allyTanksCount     = self.__getAllyTanksCount()
                self.__enemyTanksCount    = self.__getEnemyTanksCount()
                self.__allyTeamOneDamage  = self.__getAllyTeamOneDamage()
                self.__enemyTeamOneDamage = self.__getEnemyTeamOneDamage()
                self.__allyTeamDPM        = self.__getAllyTeamDPM()
                self.__enemyTeamDPM       = self.__getEnemyTeamDPM()
            for value in self.base.itervalues():
                if value['isAlive']: 
                    if value['isEnemy']:
                        value['Th'] = value['hp'] / self.__allyTeamDPM if self.__allyTeamDPM > 0 else 999999.9 #Minimum life time, min
                        value['Te'] = self.__allyTeamHP / value['gun']['currentDpm'] #Minimum time to destroy all enemies, min
                    else:
                        value['Th'] = value['hp'] / self.__enemyTeamDPM if self.__enemyTeamDPM > 0 else 999999.9
                        value['Te'] = self.__enemyTeamHP / value['gun']['currentDpm']
                    value['force']  = value['Th'] / value['Te'] if value['Te'] > 0 else 999999.9 #Part of the enemys, which can be unequivocally destroyed
                else:
                    value['Th']    = 0
                    value['Te']    = 999999.9
                    value['force'] = 0
            self.__allyTeamForces  = self.__getAllyTeamForces()
            self.__enemyTeamForces = self.__getEnemyTeamForces()
            allForces = self.__allyTeamForces + self.__enemyTeamForces
            for value in self.base.itervalues():
                value['contribution'] = 100 * value['force'] / allForces if allForces != 0 and value['isAlive'] else 0
            self.__allyChance  = 100 * self.__allyTeamForces  / allForces if allForces != 0 else 0
            self.__enemyChance = 100 * self.__enemyTeamForces / allForces if allForces != 0 else 0
            #Events -----------------------------------------------------------
            g_StatisticEvents.onVehiclesChanged(self, reasone, vID)
            if reasone <= UPDATE_REASONE.VEHICLE_DEATH:
                g_StatisticEvents.onCountChanged(self.__allyTanksCount, self.__enemyTanksCount)
            g_StatisticEvents.onHealthChanged(self.__allyTeamHP, self.__enemyTeamHP)
            g_StatisticEvents.onChanceChanged(self.__allyChance, self.__enemyChance, self.__allyTeamForces, self.__enemyTeamForces)

# Vars .......................................................................

g_TanksStatistic  = _TanksStatistic()
g_StatisticEvents = _StatisticEvents()

# Hooks ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

@g_overrideLib.registerEvent(Vehicle, 'onHealthChanged')
def new_onHealthChanged(self, *a, **k):
    if self.id in g_TanksStatistic.base:
        tank = g_TanksStatistic.base[self.id]
        if tank['hp'] != self.health:
            reasone = UPDATE_REASONE.HEALTH_CHANGED
            tank['hp'] = self.health if self.health > 0 else 0
            if tank['hp'] == 0:
                tank['isAlive'] = False
                reasone = UPDATE_REASONE.VEHICLE_DEATH
            g_TanksStatistic.update(reasone, self.id)

@g_overrideLib.registerEvent(PlayerAvatar, 'vehicle_onAppearanceReady')
def new_vehicle_onAppearanceReady(self, vehicle):
    if vehicle.id in g_TanksStatistic.base:
        entity = BigWorld.entity(vehicle.id)
        if entity:
            tank = g_TanksStatistic.base[vehicle.id]
            if tank['hp'] != entity.health:
                reasone = UPDATE_REASONE.HEALTH_CHANGED
                tank['hp'] = vehicle.health if vehicle.health > 0 else 0
                if tank['hp'] == 0 and not tank['isAlive']:
                    tank['isAlive'] = False
                    reasone = UPDATE_REASONE.VEHICLE_DEATH
                g_TanksStatistic.update(reasone, vehicle.id)

@g_overrideLib.registerEvent(PlayerAvatar, '_PlayerAvatar__onArenaVehicleKilled', True, True)
def new_onArenaVehicleKilled(self, targetID, *a, **k):
    if targetID in g_TanksStatistic.base:
        tank = g_TanksStatistic.base[targetID]
        if tank['isAlive']:
            tank['isAlive'] = False
            tank['hp'] = 0
            g_TanksStatistic.update(UPDATE_REASONE.VEHICLE_DEATH, targetID)

def addVehicleInfo(vID, vInfo):
    if vID not in g_TanksStatistic.base:
        #Main info -----------------------------------------------------------
        vType = vInfo['vehicleType']
        g_TanksStatistic.base[vID] = tank = {}
        tank['accountDBID'] = vInfo['accountDBID']
        tank['userName'] = vInfo['name']
        tank['tank_id'] = vType.type.compactDescr
        tank['name'] = vType.type.shortUserString.replace(' ','')
        tank['type'] = {}
        tank['type']['tag'] = getVehicleClassTag(vType.type.tags)
        tank['isEnemy'] = vInfo['team'] != BigWorld.player().team
        tank['isAlive'] = vInfo['isAlive']
        tank['level'] = vType.level
        tank['hp'] = tank['hpMax'] = vType.maxHealth
        #Gun -----------------------------------------------------------------
        tank['gun'] = {}
        tank['gun']['reload'] = float(vType.gun.reloadTime)
        if vType.gun.clip[0] > 1:
            tank['gun']['ammer'] = {}
            tank['gun']['ammer']['reload']      = tank['gun']['reload']
            tank['gun']['ammer']['capacity']    = vType.gun.clip[0]
            tank['gun']['ammer']['shellReload'] = float(vType.gun.clip[1])
            #Equivalent time: 5 shell x 2 sec, ammer 30 sec -> 2+30/5 = 8 sec
            tank['gun']['reload'] = tank['gun']['ammer']['shellReload'] + tank['gun']['ammer']['reload'] / tank['gun']['ammer']['capacity'] 
        tank['gun']['shell'] = {'AP':   {'damage': 0, 'dpm': 0},
                                'APRC': {'damage': 0, 'dpm': 0},
                                'HC':   {'damage': 0, 'dpm': 0},
                                'HE':   {'damage': 0, 'dpm': 0}}
        #Shells -------------------------
        for shot in vType.gun.shots:
            tag = 'APRC' if shot.shell.kind == SHELL_TYPES.ARMOR_PIERCING_CR else \
                  'HC'   if shot.shell.kind == SHELL_TYPES.HOLLOW_CHARGE     else \
                  'HE'   if shot.shell.kind == SHELL_TYPES.HIGH_EXPLOSIVE    else 'AP'
            tank['gun']['caliber'] = shot.shell.caliber
            damage = float(shot.shell.damage[0])
            if damage > tank['gun']['shell'][tag]['damage']:
                tank['gun']['shell'][tag]['damage'] = damage * (0.5 if tag == 'HE' else 1.0)
                tank['gun']['shell'][tag]['dpm'] = damage * 60 / tank['gun']['reload']
        #Current -------------------------------------------------------------
        if 'SPG' == tank['type']['tag']:
            shell = 'HE'
        else:
            shell = 'AP'   if tank['gun']['shell']['AP']['damage'] > 0   else \
                    'APRC' if tank['gun']['shell']['APRC']['damage'] > 0 else \
                    'HC'   if tank['gun']['shell']['HC']['damage'] > 0   else 'HE'
        tank['gun']['currentShell']  = shell
        tank['gun']['currentDamage'] = tank['gun']['shell'][shell]['damage']
        tank['gun']['currentDpm']    = tank['gun']['shell'][shell]['dpm']
        #Update -------------------------------------------------------------
        g_TanksStatistic.update(UPDATE_REASONE.VEHICLE_ADDED, vID)

@g_overrideLib.overrideMethod(CompoundAppearance, 'prerequisites')
def new_CompoundAppearance_prerequisites(base, self, typeDescriptor, vID, *a, **k):
    result = base(self, typeDescriptor, vID, *a, **k)
    try:
        addVehicleInfo(vID, BigWorld.player().arena.vehicles.get(vID))
    finally:
        return result

@g_overrideLib.registerEvent(PlayerAvatar, '_PlayerAvatar__startGUI')
def new__startGUI(self):
    g_TanksStatistic.init()
    for vID in self.arena.vehicles:
        addVehicleInfo(vID, self.arena.vehicles.get(vID))
    g_StatisticEvents.onBattleLoaded(g_TanksStatistic)

print '[%s] Loading mod: "victory_chances" %s (http://www.koreanrandom.com)' % (__author__, __version__)