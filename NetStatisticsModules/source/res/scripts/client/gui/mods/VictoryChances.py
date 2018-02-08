# -*- coding: utf-8 -*-

__author__  = 'StranikS_Scan'
__version__ = 'V2.0 P2.7 W0.9.22 06.02.2018'

import BigWorld
from Event import Event
from constants import SHELL_TYPES
from Avatar import PlayerAvatar
from Vehicle import Vehicle
from vehicle_systems.CompoundAppearance import CompoundAppearance
from items import vehicles

# Consts .....................................................................

class UPDATE_REASONE():
    VEHICLE_ADDED  = 0
    VEHICLE_DEATH  = 1
    HEALTH_CHANGED = 2

# Static functions ***********************************************************

# Classes ====================================================================

class _StatisticEvents(object):
    def __init__(self):
        self.OnBattleLoaded    = Event()
        self.OnVehiclesChanged = Event()
        self.OnCountChanged    = Event()
        self.OnHealthChanged   = Event()
        self.OnChanceChanged   = Event()

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
        self.base = {}
        self.__allyTanksCount        = None
        self.__getAllyTanksCount     = lambda withDead=False: sum([1 for value in self.base.itervalues() if not value['isEnemy'] and (withDead or value['isAlive'])])
        self.__enemyTanksCount       = None
        self.__getEnemyTanksCount    = lambda withDead=False: sum([1 for value in self.base.itervalues() if value['isEnemy'] and (withDead or value['isAlive'])])
        self.__allyTeamHP            = None
        self.__getAllyTeamHP         = lambda withDead=False: sum([value['hp'] for value in self.base.itervalues() if not value['isEnemy'] and (withDead or value['isAlive'])])
        self.__enemyTeamHP           = None
        self.__getEnemyTeamHP        = lambda withDead=False: sum([value['hp'] for value in self.base.itervalues() if value['isEnemy'] and (withDead or value['isAlive'])])
        self.__allyTeamOneDamage     = None
        self.__getAllyTeamOneDamage  = lambda withDead=False: sum([value['gun']['currentDamage'] for value in self.base.itervalues() if not value['isEnemy'] and (withDead or value['isAlive'])])
        self.__enemyTeamOneDamage    = None
        self.__getEnemyTeamOneDamage = lambda withDead=False: sum([value['gun']['currentDamage'] for value in self.base.itervalues() if value['isEnemy'] and (withDead or value['isAlive'])])
        self.__allyTeamDPM           = None
        self.__getAllyTeamDPM        = lambda withDead=False: sum([value['gun']['currentDpm'] for value in self.base.itervalues() if not value['isEnemy'] and (withDead or value['isAlive'])])
        self.__enemyTeamDPM          = None
        self.__getEnemyTeamDPM       = lambda withDead=False: sum([value['gun']['currentDpm'] for value in self.base.itervalues() if value['isEnemy'] and (withDead or value['isAlive'])])
        self.__allyTeamForces        = None
        self.__getAllyTeamForces     = lambda withDead=False: sum([value['force'] for value in self.base.itervalues() if not value['isEnemy'] and (withDead or value['isAlive'])])
        self.__enemyTeamForces       = None
        self.__getEnemyTeamForces    = lambda withDead=False: sum([value['force'] for value in self.base.itervalues() if value['isEnemy'] and (withDead or value['isAlive'])])
        self.__allyChance            = None
        self.__enemyChance           = None 

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
                value['contribution'] = 100 * value['force'] / allForces if value['isAlive'] else 0
            self.__allyChance  = 100 * self.__allyTeamForces  / allForces
            self.__enemyChance = 100 * self.__enemyTeamForces / allForces
            #Events -----------------------------------------------------------
            g_StatisticEvents.OnVehiclesChanged(statistic=self, reasone=reasone, vID=vID)
            if reasone <= UPDATE_REASONE.VEHICLE_DEATH:
                g_StatisticEvents.OnCountChanged(count=(self.__allyTanksCount, self.__enemyTanksCount))
            g_StatisticEvents.OnHealthChanged(health=(self.__allyTeamHP, self.__enemyTeamHP))
            g_StatisticEvents.OnChanceChanged(chances=(self.__allyChance, self.__enemyChance), forces=(self.__allyTeamForces, self.__enemyTeamForces))

# Vars .......................................................................

g_TanksStatistic  = _TanksStatistic()
g_StatisticEvents = _StatisticEvents()

# Hooks ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

def new_onHealthChanged(self, newHealth, attackerID, attackReasonID):
    old_onHealthChanged(self, newHealth, attackerID, attackReasonID)
    if self.id in g_TanksStatistic.base:
        tank = g_TanksStatistic.base[self.id]
        if tank['hp'] != self.health:
            reasone = UPDATE_REASONE.HEALTH_CHANGED
            tank['hp'] = self.health if self.health > 0 else 0
            if tank['hp'] == 0:
                tank['isAlive'] = False
                reasone = UPDATE_REASONE.VEHICLE_DEATH
            g_TanksStatistic.update(reasone, self.id)

def new_vehicle_onEnterWorld(self, vehicle):
    old_vehicle_onEnterWorld(self, vehicle)
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

def new_onArenaVehicleKilled(self, targetID, attackerID, equipmentID, reason):
    try:
        if targetID in g_TanksStatistic.base:
            tank = g_TanksStatistic.base[targetID]
            if tank['isAlive']:
                tank['isAlive'] = False
                tank['hp'] = 0
                g_TanksStatistic.update(UPDATE_REASONE.VEHICLE_DEATH, targetID)
    finally:
        old_onArenaVehicleKilled(self, targetID, attackerID, equipmentID, reason)

def addVehicleInfo(vID, vInfo):
    if vID not in g_TanksStatistic.base:
        #Main info -----------------------------------------------------------
        vType = vInfo['vehicleType']
        g_TanksStatistic.base[vID] = tank = {}
        tank['name'] = vType.type.shortUserString.replace(' ','')
        tank['type'] = {}
        tank['type']['tag'] = set(vehicles.VEHICLE_CLASS_TAGS & vType.type.tags).pop()
        tank['isEnemy'] = vInfo['team'] != BigWorld.player().team
        tank['isAlive'] = vInfo['isAlive']
        tank['level'] = vType.level
        tank['hp'] = vType.maxHealth
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
                  'HC'   if shot.shell.kind == SHELL_TYPES.HOLLOW_CHARGE else \
                  'HE'   if shot.shell.kind == SHELL_TYPES.HIGH_EXPLOSIVE else 'AP'
            tank['gun']['caliber'] = shot.shell.caliber
            damage = float(shot.shell.damage[0])
            if damage > tank['gun']['shell'][tag]['damage']:
                tank['gun']['shell'][tag]['damage'] = damage * (0.5 if tag == 'HE' else 1.0)
                tank['gun']['shell'][tag]['dpm'] = damage * 60 / tank['gun']['reload']
        #Current -------------------------------------------------------------
        if 'SPG' == tank['type']['tag']:
            shell = 'HE'
        else:
            shell = 'AP' if tank['gun']['shell']['AP']['damage'] > 0 else \
                    'APRC' if tank['gun']['shell']['APRC']['damage'] > 0 else \
                    'HC' if tank['gun']['shell']['HC']['damage'] > 0 else 'HE'
        tank['gun']['currentShell']  = shell
        tank['gun']['currentDamage'] = tank['gun']['shell'][shell]['damage']
        tank['gun']['currentDpm']    = tank['gun']['shell'][shell]['dpm']
        #Update -------------------------------------------------------------
        g_TanksStatistic.update(UPDATE_REASONE.VEHICLE_ADDED, vID)

def new_CompoundAppearance_prerequisites(self, typeDescriptor, vID, health, isCrewActive, isTurretDetached, outfitCD):
    result = old_CompoundAppearance_prerequisites(self, typeDescriptor, vID, health, isCrewActive, isTurretDetached, outfitCD)
    try:
        addVehicleInfo(vID, BigWorld.player().arena.vehicles.get(vID))
    finally:
        return result

def new__startGUI(self):
    old__startGUI(self)
    for vID in self.arena.vehicles:
        addVehicleInfo(vID, self.arena.vehicles.get(vID))
    g_StatisticEvents.OnBattleLoaded(statistic=g_TanksStatistic)

def new__destroyGUI(self):
    old__destroyGUI(self)
    global g_TanksStatistic
    g_TanksStatistic = _TanksStatistic()

old_onHealthChanged = Vehicle.onHealthChanged
Vehicle.onHealthChanged = new_onHealthChanged

old_vehicle_onEnterWorld = PlayerAvatar.vehicle_onEnterWorld
PlayerAvatar.vehicle_onEnterWorld = new_vehicle_onEnterWorld

old_onArenaVehicleKilled = PlayerAvatar._PlayerAvatar__onArenaVehicleKilled
PlayerAvatar._PlayerAvatar__onArenaVehicleKilled = new_onArenaVehicleKilled

old_CompoundAppearance_prerequisites = CompoundAppearance.prerequisites
CompoundAppearance.prerequisites = new_CompoundAppearance_prerequisites

old__startGUI = PlayerAvatar._PlayerAvatar__startGUI
PlayerAvatar._PlayerAvatar__startGUI = new__startGUI

old__destroyGUI = PlayerAvatar._PlayerAvatar__destroyGUI
PlayerAvatar._PlayerAvatar__destroyGUI = new__destroyGUI

print '[%s] Loading mod: VictoryChances %s (http://www.koreanrandom.com)' % (__author__, __version__)