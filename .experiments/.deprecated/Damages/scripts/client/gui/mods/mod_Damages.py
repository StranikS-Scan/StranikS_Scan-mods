# -*- coding: utf-8 -*-

__version__ = 'V1.6 P2.7 W0.9.15 26.05.2016'
__author__  = 'StranikS_Scan'

print '[%s] Loading mod: Damages %s (http://www.koreanrandom.com/forum/topic/27695-/#3)' % (__author__, __version__)

import BigWorld
import GUI
from Avatar import PlayerAvatar
from Vehicle import Vehicle
import constants
from items import vehicles
from VehicleEffects import DamageFromShotDecoder

import re
from datetime import datetime
import ResMgr, os, codecs, json
import unicodedata

# Consts ..........................................................................

CONFIG_FILENAME = None
LOG_FILENAME    = None

DAMAGE_FILTER = 0

SHOW_INFO  = True
REC_COUNT  = 10
PRINT_LOG  = True

GUI_TEXT_FONT  = 'Damages.font'
GUI_TEXT_XY    = (-1200, -800)
GUI_TEXT_COLOR = '00EDFFFF'
GUI_TEXT       = None

GLOBAL_STATISTICS = {}
TANKS_STATISTICS  = {}
PLAYER_SHOTS      = {}

# Classes and functions ===========================================================

def RemoveAccents(input_str):
    nkfd_form = unicodedata.normalize('NFKD', unicode(input_str))
    return u"".join([c for c in nkfd_form if not unicodedata.combining(c)])

def getRoot():
    root = ''
    values = ResMgr.openSection('../paths.xml')['Paths'].values()[0:2]
    for value in values:
        root = value.asString + '/scripts/client/gui/mods/'
        break
    return root

def getLogFileName(dirname, prefix=''):
    root = getRoot()
    if dirname:
        dirname = dirname.replace('\\', '/')
        if dirname[-1] != '/':
            dirname += '/'
    path = (root if not (':' in dirname) else '') + dirname
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except:
            path = root
    return path + prefix + datetime.now().strftime('%d%m%y_%H%M%S_%f')[:17] + '.log'

def getConfigFileName():
    filename = getRoot() + 'Damages.cfg'
    return filename if os.path.exists(filename) else None

class TextLabel(object):
    def __init__(self, x, y, color, font, count=1):
        self.__text = []
        self.__count = count
        self.__x = x
        self.__y = y
        self.__color = '\c%s;' % color
        self.__text_gui = GUI.Text('')
        self.__text_gui.visible = False
        self.__text_gui.colourFormatting = True
        self.__text_gui.multiline = True
        self.__text_gui.widthMode = self.__text_gui.heightMode = \
        self.__text_gui.verticalPositionMode = self.__text_gui.horizontalPositionMode = 'PIXEL'
        self.__text_gui.horizontalAnchor = 'LEFT'
        self.__text_gui.verticalAnchor = 'TOP'
        self.__text_gui.font = font

    def Add(self, text):
        self.__text.insert(0, text)
        self.__text = self.__text[:self.__count]
        self.__text_gui.text = self.__color + ''.join(self.__text)
    
    def Show(self):
        x0, y0 = GUI.screenResolution()
        GUI.addRoot(self.__text_gui)
        self.__text_gui.position = (round((x0 + self.__x) / 2), round((y0 + self.__y) / 2), 0.15)
        self.__text_gui.visible = True

    def Hide(self):
        if self.__text_gui.visible:
            self.__text_gui.visible = False
            GUI.delRoot(self.__text_gui)

    def Text(self, text=''):
        self.__text = [text]
        self.__text_gui.text = self.__color + self.__text[0]

def getTankType(typeTags):
    if 'mediumTank' in typeTags:
        return (1, 'MT')
    elif 'heavyTank' in typeTags:
        return (2, 'HT')
    elif 'AT-SPG' in typeTags:
        return (3, 'AT')
    elif 'SPG' in typeTags:
        return (4, 'SPG')
    else:
        return (0, 'LT')

def getShellTypeID(kind):
    if kind   == 'ARMOR_PIERCING_CR':
        return (1, 'APRC')
    elif kind == 'HOLLOW_CHARGE':
        return (2, 'HC')
    elif kind == 'HIGH_EXPLOSIVE':
        return (3, 'HE')
    else:
        return (0, 'AP') #ARMOR_PIERCING, ARMOR_PIERCING_HE  

def printStrings(value): 
    if LOG_FILENAME is not None and PRINT_LOG:
        with codecs.open(LOG_FILENAME, 'a', 'utf-8-sig') as file:
            if isinstance(value, list) or isinstance(value, tuple):
                file.writelines(value)
            else:
                file.write(value)

def printStartInfo():
    def getStat(stat):
        return '%s\t%s\t%6.2f HP\t%5.1f mm\t%s\t%s dmg\t%s (%s)\n' % ('E' if stat['isEnemy'] else 'A', \
               stat['type']['name'], stat['hp'], stat['gun']['caliber'], stat['gun']['shell'][stat['gun']['mainShell']]['typeName'], \
               ('|'.join(['%s-%6.1f' % (stat['gun']['shell'][sID]['typeName'], stat['gun']['shell'][sID]['damage']) for sID in stat['gun']['shell']])).ljust(20), \
               stat['name'], stat['UserName'])

    if LOG_FILENAME is not None and PRINT_LOG:
        with codecs.open(LOG_FILENAME, 'a', 'utf-8-sig') as file:
            vIDSort = list(TANKS_STATISTICS.keys())
            for vID in [vID for vID in vIDSort if TANKS_STATISTICS[vID]['isAlive'] and not TANKS_STATISTICS[vID]['isEnemy']]:
                file.write(getStat(TANKS_STATISTICS[vID]))
            file.write('\n')
            for vID in [vID for vID in vIDSort if TANKS_STATISTICS[vID]['isAlive'] and TANKS_STATISTICS[vID]['isEnemy']]:
                file.write(getStat(TANKS_STATISTICS[vID]))
            file.write('\n')

# Hooks ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

def new_showDamageFromShot(self, attackerID, points, effectsIndex, damageFactor):
    global PLAYER_SHOTS
    try:
        effectsDescr = vehicles.g_cache.shotEffects[effectsIndex]
        maxHitEffectCode, _ = DamageFromShotDecoder.decodeHitPoints(points, self.typeDescriptor)
        if not attackerID in PLAYER_SHOTS:
            PLAYER_SHOTS[attackerID] = []
        if DamageFromShotDecoder.hasDamaged(maxHitEffectCode): #С уроном
            for index in TANKS_STATISTICS[attackerID]['gun']['shell']:
                if 'effectsIndex' in TANKS_STATISTICS[attackerID]['gun']['shell'][index]:
                    if TANKS_STATISTICS[attackerID]['gun']['shell'][index]['effectsIndex'] == effectsIndex:
                        PLAYER_SHOTS[attackerID].append(index) #Тип снаряда определен
                        return
        PLAYER_SHOTS[attackerID] = [] #Без урона
    finally:
        if old_showDamageFromShot is not None:
            old_showDamageFromShot(self, attackerID, points, effectsIndex, damageFactor)
    return        

def new_onHealthChanged(self, newHealth, attackerID, attackReasonID):
    global TANKS_STATISTICS
    try:
        if self.id in TANKS_STATISTICS and TANKS_STATISTICS[self.id]['isAlive']:
            if 0 < TANKS_STATISTICS[self.id]['hp'] > newHealth:
                userHealth = newHealth if newHealth >= 0 else 0
                if constants.ATTACK_REASONS[attackReasonID] == 'shot':
                    isBoom = True if newHealth < 0 else False
                    if DAMAGE_FILTER == 0 or (BigWorld.player().playerVehicleID==attackerID and DAMAGE_FILTER in [1,2]) or \
                                             (BigWorld.player().playerVehicleID==self.id and DAMAGE_FILTER in [1,3]):
                        info = ''
                        if attackerID in TANKS_STATISTICS:
                            if attackerID in PLAYER_SHOTS and PLAYER_SHOTS[attackerID]:
                                shellType = TANKS_STATISTICS[attackerID]['gun']['shell'][PLAYER_SHOTS[attackerID][-1]]['typeName']
                                PLAYER_SHOTS[attackerID] = []
                            else:
                                shellType = 'UNK'
                            damage = TANKS_STATISTICS[self.id]['hp'] - userHealth
                            damage_percent = 100.0 * damage / TANKS_STATISTICS[attackerID]['gun']['mainDamage']
                            info = '%s   %s %d dmg %.1f%% %s (%s)\n%s   %s%d->%d HP %s (%s)' % ('E' if TANKS_STATISTICS[attackerID]['isEnemy'] else 'A', shellType, damage, damage_percent, RemoveAccents(TANKS_STATISTICS[attackerID]['name']), TANKS_STATISTICS[attackerID]['UserName'], \
                               'E' if TANKS_STATISTICS[self.id]['isEnemy'] else 'A', 'BOOM! ' if isBoom else '', TANKS_STATISTICS[self.id]['hp'], userHealth, RemoveAccents(TANKS_STATISTICS[self.id]['name']), TANKS_STATISTICS[self.id]['UserName'])
                        info += '\n\n'
                        if SHOW_INFO:
                            GUI_TEXT.Add(info)
                        if userHealth > 0:
                            info = ('------------------------- %s -------------------------\n' % datetime.now().strftime('%d.%m.%y %H:%M:%S')) + '\nReason: HealthChanged\n\n' + info
                        else:
                            info = ('------------------------- %s -------------------------\n' % datetime.now().strftime('%d.%m.%y %H:%M:%S')) + '\nReason: VehicleKilled\n\n' + info
                        printStrings(info)
                TANKS_STATISTICS[self.id]['hp'] = userHealth
                if TANKS_STATISTICS[self.id]['hp'] == 0:
                    TANKS_STATISTICS[self.id]['isAlive'] = False
    finally:
        if old_onHealthChanged is not None:
            old_onHealthChanged(self, newHealth, attackerID, attackReasonID)

def new_vehicle_onEnterWorld(self, vehicle):
    if old_vehicle_onEnterWorld is not None:
        old_vehicle_onEnterWorld(self, vehicle)
    global TANKS_STATISTICS
    entity = BigWorld.entity(vehicle.id)
    if entity is not None and vehicle.id in TANKS_STATISTICS:
        if TANKS_STATISTICS[vehicle.id]['hp'] != entity.health:
            TANKS_STATISTICS[vehicle.id]['hp'] = entity.health
        if TANKS_STATISTICS[vehicle.id]['hp'] == 0:
            TANKS_STATISTICS[vehicle.id]['isAlive'] = False

def new__startGUI(self):
    if old__startGUI is not None:
        old__startGUI(self)

    global CONFIG_FILENAME, LOG_FILENAME, DAMAGE_FILTER, \
           SHOW_INFO, REC_COUNT, PRINT_LOG, GUI_TEXT_FONT, GUI_TEXT_XY, GUI_TEXT_COLOR, \
           GLOBAL_STATISTICS, TANKS_STATISTICS, PLAYER_SHOTS

    CONFIG_FILENAME = getConfigFileName()
    if CONFIG_FILENAME is not None:
        config         = json.loads(re.compile('(/\*(.|\n)*?\*/)|((#|//).*?$)', re.I | re.M).sub('', codecs.open(CONFIG_FILENAME, 'r', 'utf-8-sig').read()))
        DAMAGE_FILTER  = config['System']['DamageStatistics']['Filter']
        SHOW_INFO      = config['System']['DamageStatistics']['ShowDamageList']
        REC_COUNT      = config['System']['DamageStatistics']['RecordsCount']
        GUI_TEXT_XY    = (config['System']['DamageStatistics']['GUIFormat']['Position'][0], config['System']['DamageStatistics']['GUIFormat']['Position'][1])
        GUI_TEXT_COLOR = config['System']['DamageStatistics']['GUIFormat']['Color']
        PRINT_LOG      = config['System']['DamageStatistics']['PrintLog']
        LOG_FILENAME   = getLogFileName(config['System']['DamageStatistics']['LogFormat']['Dir'], config['System']['DamageStatistics']['LogFormat']['Prefix']) 
    GLOBAL_STATISTICS.clear()
    TANKS_STATISTICS.clear()
    PLAYER_SHOTS.clear()
    for vID in BigWorld.player().arena.vehicles: #Кэшируем статистику
        vehicleType = BigWorld.player().arena.vehicles[vID]['vehicleType']
        TANKS_STATISTICS[vID] = {}
        TANKS_STATISTICS[vID]['UserName']      = BigWorld.player().arena.vehicles[vID]['name']
        TANKS_STATISTICS[vID]['name']          = vehicleType.type.shortUserString.replace(' ','')
        TANKS_STATISTICS[vID]['type']          = {}
        TANKS_STATISTICS[vID]['type']['id'], \
        TANKS_STATISTICS[vID]['type']['name']  = getTankType(vehicleType.type.tags)
        TANKS_STATISTICS[vID]['isEnemy']       = (BigWorld.player().arena.vehicles[vID]['team'] != BigWorld.player().team)
        TANKS_STATISTICS[vID]['isAlive']       = True
#       TANKS_STATISTICS[vID]['balanceWeight'] = float(vehicleType.balanceWeight)
        TANKS_STATISTICS[vID]['hp']            = int(vehicleType.maxHealth)
        #Оборудование
        TANKS_STATISTICS[vID]['gun']           = {} #Орудие 
        TANKS_STATISTICS[vID]['gun']['shell'] = {0: {'typeName': 'AP',   'damage': 0}, \
                                                 1: {'typeName': 'APRC', 'damage': 0}, \
                                                 2: {'typeName': 'HC',   'damage': 0}, \
                                                 3: {'typeName': 'HE',   'damage': 0}} #Снаряды
        for shellID in vehicleType.gun['shots']:
            index, _ = getShellTypeID(shellID['shell']['kind'])
            TANKS_STATISTICS[vID]['gun']['caliber'] = float(shellID['shell']['caliber'])
            damage = float(shellID['shell']['damage'][0])
            if damage > TANKS_STATISTICS[vID]['gun']['shell'][index]['damage']:
                TANKS_STATISTICS[vID]['gun']['shell'][index]['damage'] = damage
            TANKS_STATISTICS[vID]['gun']['shell'][index]['effectsIndex'] = shellID['shell']['effectsIndex']
        if TANKS_STATISTICS[vID]['type']['id'] == 4: #САУ
            shellID = 3 #ОФ
        else: #Остальные
            if TANKS_STATISTICS[vID]['gun']['shell'][0]['damage'] != 0:
                shellID = 0 #ББ
            elif TANKS_STATISTICS[vID]['gun']['shell'][1]['damage'] != 0:
                shellID = 1 #ПК для тех у кого нет ББ
            else:
                shellID = 3 #иначе ОФ
        TANKS_STATISTICS[vID]['gun']['mainShell']  = shellID #Базовый снаряд танка        
        TANKS_STATISTICS[vID]['gun']['mainDamage'] = TANKS_STATISTICS[vID]['gun']['shell'][TANKS_STATISTICS[vID]['gun']['mainShell']]['damage'] #Урон базовым снарядом
    printStrings(('------------------------- %s -------------------------\n' % datetime.now().strftime('%d.%m.%y %H:%M:%S'), \
                  '\nReason: BattleLoading\n\n'))    
    printStartInfo()
    if SHOW_INFO:
        global GUI_TEXT
        GUI_TEXT = TextLabel(GUI_TEXT_XY[0], GUI_TEXT_XY[1], GUI_TEXT_COLOR, GUI_TEXT_FONT, REC_COUNT)
        GUI_TEXT.Show()

def new__destroyGUI(self):
    if old__destroyGUI is not None:
        old__destroyGUI(self)
    if SHOW_INFO:
        global GUI_TEXT
        GUI_TEXT.Hide()
        GUI_TEXT = None

old_showDamageFromShot = Vehicle.showDamageFromShot
Vehicle.showDamageFromShot = new_showDamageFromShot

old_onHealthChanged = Vehicle.onHealthChanged
Vehicle.onHealthChanged = new_onHealthChanged

old_vehicle_onEnterWorld = PlayerAvatar.vehicle_onEnterWorld
PlayerAvatar.vehicle_onEnterWorld = new_vehicle_onEnterWorld

old__startGUI = PlayerAvatar._PlayerAvatar__startGUI
PlayerAvatar._PlayerAvatar__startGUI = new__startGUI

old__destroyGUI = PlayerAvatar._PlayerAvatar__destroyGUI
PlayerAvatar._PlayerAvatar__destroyGUI = new__destroyGUI