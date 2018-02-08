# -*- coding: utf-8 -*-

__version__ = 'V2.7 P2.7 W0.9.15 28.05.2016'
__author__  = 'StranikS_Scan'

print '[%s] Loading mod: Meter Instruments %s (http://www.koreanrandom.com/forum/topic/27695-/#1)' % (__author__, __version__)

import BigWorld
import GUI
import Keys
import BattleReplay
from gui import InputHandler
from gui.app_loader import g_appLoader
from gui.shared.utils.HangarSpace import g_hangarSpace
from gui import SystemMessages
from gui.battle_control import g_sessionProvider
from PlayerEvents import g_playerEvents
from Avatar import PlayerAvatar
from AvatarInputHandler import AimingSystems
from AvatarInputHandler.control_modes import ArcadeControlMode, SniperControlMode, PostMortemControlMode
from AvatarInputHandler.DynamicCameras.ArcadeCamera import MinMax, ArcadeCamera, _InputInertia
from AvatarInputHandler.DynamicCameras.SniperCamera import SniperCamera
from AvatarInputHandler.DynamicCameras.StrategicCamera import StrategicCamera
from AvatarInputHandler.AimingSystems.SniperAimingSystem import SniperAimingSystem
from AvatarInputHandler import Oscillator
from BattleReplay import g_replayCtrl
from VehicleGunRotator import VehicleGunRotator
from vehicle_systems.tankStructure import TankPartNames
import Vehicle as MVehicle
from functools import partial
from datetime import datetime
import re
import math, Math
from Math import Vector3
import helpers
import ResMgr, os, codecs, json

# Files ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

def getRoot():
    root = ''
    values = ResMgr.openSection('../paths.xml')['Paths'].values()[0:2]
    for value in values:
        root = value.asString + '/scripts/client/gui/mods/'
        break
    return root

def getConfigFileName():
    return getRoot() + 'Meter.cfg'

def getDumpFileName():
    root = getRoot()
    dirname = CONFIG['Dump']['Dir']
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
    return path + CONFIG['Dump']['Prefix'] + '%s.log'

def getDumpFormatterFileName():
    root = getRoot()
    filename = CONFIG['Dump']['Formatter']
    if filename:
        filename = filename.replace('\\', '/')
    return (root if not (':' in filename) else '') + filename   

def getLogFileName():
    root = getRoot()      
    dirname = CONFIG['Log']['Dir']
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
    return path + CONFIG['Log']['Prefix'] + datetime.now().strftime('%d%m%y_%H%M%S_%f')[:17] + '.log'

def getLogFormatterFileName():
    root = getRoot()
    filename = CONFIG['Log']['Formatter']
    if filename:
        filename = filename.replace('\\', '/')
    return (root if not (':' in filename) else '') + filename

# Config *************************************************************

CONFIG = {}
ConfigFileName = getConfigFileName()
if os.path.isfile(ConfigFileName):
    CONFIG = json.loads(re.compile('(/\*(.|\n)*?\*/)|((#|//).*?$)', re.I | re.M).sub('', codecs.open(ConfigFileName, 'r', 'utf-8-sig').read()))

# Static consts -------------------------------------------------------

if CONFIG:
    TEXT_COLOR_DEF = CONFIG['System']['TextColorDefault'] #Цвет текстовых меток по умолчанию
    DIGITS_COUNT   = CONFIG['System']['DigitsCount']      #Точность округления (10-12 предел для клиента)
    DIGITS_LEN     = CONFIG['System']['DigitsLength']     #Отображаемая длина вещественной части чисел
    DIGITS_PLACE   = CONFIG['System']['DigitsPlace']      #Группировать цифры в разряды, кол-во цифр в разряде
    UPDATE_DELAY   = CONFIG['System']['UpdateDelay']      #Интервал обновления (помним, что 1 сек в реплее при 1/x16, это 0.0625 сек)
else:
    TEXT_COLOR_DEF = "0000FFFF"
    print '\'Meter\': file \'Meter.cfg\' not found! Mod not started.'

# Dynamic consts ......................................................

GUI_TEXTLABLES          = {}   #Текстовые метки
GUI_SHELLICON_PLAYER    = None #Картинка снаряда
GUI_SHELLICON_OTHER     = None
GUI_DEVICESICONS_PLAYER = []   #Картинки модулей
GUI_DEVICESICONS_OTHER  = []
PLAYER_SHOTS            = {}   #Выстрелы игрока
PLAYER_SHOTS_COUNT      = 0    #Кол-во выстрелов, сделанных игроком
TARGET_CALLBACK         = None
CollisionSkins          = {}

# Classes '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

class TextLabel(object):
    '''
    Класс для вывода числовых и строковых значений как текстовых меток
    caption - префикс, text - текст, postfix - постфикс, visible - состояние,
    x, y - координаты относительно центра экрана, color - цвет текста
    '''
    def __init__(self, caption='', text='', postfix='', visible=True, x=0, y=0, color=TEXT_COLOR_DEF, font='Meter.font'):
        self.__x = x
        self.__y = y
        self.__caption = caption
        self.__value = self.__text = text
        self.__postfix = postfix
        self.__color = '\c' + (color if len(color) == 8 else TEXT_COLOR_DEF) + ';'
        self.__text_gui = GUI.Text(self.__color + self.__caption + self.__text + self.__postfix)
        self.__text_gui.visible = False
        self.__text_gui.colourFormatting = True
        self.__text_gui.widthMode = self.__text_gui.heightMode = \
        self.__text_gui.verticalPositionMode = self.__text_gui.horizontalPositionMode = 'PIXEL'
        self.__text_gui.horizontalAnchor = 'LEFT'
        self.__text_gui.font = font
        if visible:
            self.Enable()

    def Enable(self):
        '''
        Включить метку
        '''
        x0, y0 = GUI.screenResolution()
        GUI.addRoot(self.__text_gui)
        self.__text_gui.position = (round(x0 / 2 + self.__x), round(y0 / 2 + self.__y), 0.15)
        self.__text_gui.visible = True

    def Disable(self):
        '''
        Выключить метку
        '''
        if self.__text_gui.visible:
            self.__text_gui.visible = False
            GUI.delRoot(self.__text_gui)

    def Color(self, value):
        '''
        Задать цвет текста
        '''
        self.__color = '\c'+value+';'
        self.__text_gui.text = self.__color + self.__caption + self.__text + self.__postfix

    def Value(self, value, dig=20, leng=0, sep=' '):
        '''
        Отобразить вещественное число
        '''
        if value != self.__value:
            self.__value = float(value)
            self.__text = FloatToString(self.__value, dig, leng, sep)
            self.__text_gui.text = self.__color + self.__caption + self.__text + self.__postfix

    def ValueMatrix(self, matrix, dig=20, leng=0, sep=' '):
        '''
        Отобразить матрицу/массив/кортеж вещественных чисел
        '''
        if matrix != self.__value:
            self.__value = matrix
            self.__text = FloatMatrixToString(self.__value, dig, leng, sep)
            self.__text_gui.text = self.__color + self.__caption + self.__text + self.__postfix

    def Text(self, text):
        '''
        Отобразить текстовую строку
        '''
        self.__value = self.__text = str(text)
        self.__text_gui.text = self.__color + self.__caption + self.__text + self.__postfix

    def Visible(self):
        '''
        Видимость метки
        '''
        return self.__text_gui.visible

    def Position(self, x, y):
        '''
        Задать координаты метки относительно центра экрана
        '''
        self.__x = x
        self.__y = y
        x0, y0 = GUI.screenResolution()
        self.__text_gui.position = (round(x0 / 2 + self.__x), round(y0 / 2 + self.__y), 0.15)

class Image(object):
    '''
    Класс для вывода картинок в интерфейсе игрока
    width, height - ширина и высота в пик., file - файл с картинкой,
    x, y - координаты относительно центра экрана
    '''
    def __init__(self, width, height, file='', x=0, y=0, visible=False):
        self.__x = x
        self.__y = y
        self.__icon_gui = GUI.Simple(file)
        self.__icon_gui.materialFX = 'BLEND'
        self.__icon_gui.widthMode = self.__icon_gui.heightMode = \
        self.__icon_gui.verticalPositionMode = self.__icon_gui.horizontalPositionMode = 'PIXEL'
        self.__icon_gui.horizontalAnchor = 'LEFT'
        self.__icon_gui.size = (width, height)
        if visible:
            self.Enable()

    def Enable(self):
        '''
        Показать картинку
        '''
        x0, y0 = GUI.screenResolution()
        GUI.addRoot(self.__icon_gui)
        self.__icon_gui.position = (round(x0 / 2 + self.__x), round(y0 / 2 + self.__y), 0.15)
        self.__icon_gui.visible = True

    def Disable(self):
        '''
        Скрыть картинку
        '''
        if self.__icon_gui.visible:
            self.__icon_gui.visible = False
            GUI.delRoot(self.__icon_gui)

    def Visible(self):
        '''
        Видимость картинки
        '''
        return self.__icon_gui.visible
            
    def FileName(self, filename):
        '''
        Загрузка картинки из файла
        '''
        if self.__icon_gui.textureName != filename:
            self.__icon_gui.textureName = filename

    def Position(self, x, y):
        '''
        Задать координаты картинки относительно центра экрана
        '''
        self.__x = x
        self.__y = y
        x0, y0 = GUI.screenResolution()
        self.__icon_gui.position = (round(x0 / 2 + self.__x), round(y0 / 2 + self.__y), 0.15)

class DumpToFile(object):
    def __init__(self):
        self.BattleCache   = {} #Кэш всех параметров, вывод которых указан в cfg-файле
        self.DigitsCount   = int(CONFIG['Dump']['DigitsCount'])
        self.SaveToFileKey = getBKeys(CONFIG['Dump']['SaveToFile'])
        self.DumpFileName  = getDumpFileName()
        self.DumpFormatterFileName = getDumpFormatterFileName()
        if os.path.isfile(self.DumpFormatterFileName):
            InputHandler.g_instance.onKeyDown += self.handleKeyDumpEvent
            self.DumpFormatter = re.compile('(/\*(.|\n)*?\*/(.|\n)*?(\n|$))|((#|//).*?(\n|$))', re.I | re.M).sub('', open(self.DumpFormatterFileName, 'r').read())
            self.initCache()
        else:
            self.DumpFormatter = ''
            print '\'Meter Instruments\': file \'%s\' not found! Dumping will not work.' % self.DumpFormatterFileName

    def initCache(self):
        self.BattleCache = parseFormatter(self.DumpFormatter)
        self.LastBattleCacheHash = hash(frozenset(self.BattleCache.items()))

    def dumpCache(self, filename):
        try:
            textDump = self.DumpFormatter.format(**self.BattleCache)
            with open(filename, 'w') as file:
                file.write(textDump)
        except Exception as E:
            message = '\'Meter Instruments\': file \'%s\' contains an error!' % os.path.basename(self.DumpFormatterFileName)
            print message
            print str(E)
            showMessage(message, 'yellow')

    def handleKeyDumpEvent(self, event):
        if event.isKeyDown():
            if isBKeysDown(self.SaveToFileKey):
                filename = self.DumpFileName % datetime.now().strftime('%d%m%y_%H%M%S_%f')[:17]
                self.dumpCache(filename)
                showMessage('Dumped to file \'%s\'' % os.path.basename(filename), 'green', True)

class LogToFile(object):
    def __init__(self):
        self.Conditions    = {} #Условия записи в лог
        self.BattleCache   = {} #Кэш всех параметров, вывод которых указан в cfg-файле
        self.LastBattleCacheHash = hash(frozenset(self.BattleCache.items()))
        self.Enable        = CONFIG['Log']['DefaultState']
        self.EnableKey     = getBKeys(CONFIG['Log']['Switch'])
        self.NewLogFileKey = getBKeys(CONFIG['Log']['NewFile'])
        self.UpdateTime    = float(CONFIG['Log']['UpdateTime'])
        self.DigitsCount   = int(CONFIG['Log']['DigitsCount'])
        self.LogFileName   = getLogFileName()
        self.LogFormatterFileName  = getLogFormatterFileName()
        if os.path.isfile(self.LogFormatterFileName):
            InputHandler.g_instance.onKeyDown += self.handleKeyLogEvent
            self.LogFormatter = re.compile('(/\*(.|\n)*?\*/(.|\n)*?(\n|$))|((#|//).*?(\n|$))', re.I | re.M).sub('', open(self.LogFormatterFileName, 'r').read())
            self.initCache()
        else:
            self.LogFormatter = ''
            print '\'Meter Instruments\': file \'%s\' not found! Log will not work.' % self.LogFormatterFileName

    def initCache(self):
        self.Conditions = {key: None for key in CONFIG['Log']['Conditions']}
        self.BattleCache = parseFormatter(self.LogFormatter)
        for key in self.Conditions:
            if not key in self.BattleCache:
                self.BattleCache[key] = self.Conditions[key]
        self.LastBattleCacheHash = hash(frozenset(self.BattleCache.items()))

    def goNewFile(self):
        self.LogFileName = getLogFileName()
 
    def handleKeyLogEvent(self, event):
        if event.isKeyDown():
            if isBKeysDown(self.EnableKey):
                self.Enable = not self.Enable
                if self.Enable:
                    self.LastBattleCacheHash = hash(frozenset(self.BattleCache.items()))
                    showMessage('Log started in file \'%s\'' % os.path.basename(self.LogFileName), 'green', True)
                else:
                    showMessage('Log stoped', 'green', True)
            if isBKeysDown(self.NewLogFileKey):
                self.goNewFile()
                showMessage('Log redirected to file \'%s\'' % os.path.basename(self.LogFileName), 'green', True)

    def dumpLogUpdate(self):
        if self.Enable and hasattr(BigWorld, 'player') and hasattr(BigWorld.player(), 'isVehicleAlive') and BigWorld.player().isVehicleAlive:
            if hash(frozenset(self.BattleCache.items())) != self.LastBattleCacheHash:
                if '%SystemTime%' in self.BattleCache:
                    self.BattleCache['%SystemTime%'] = datetime.now().strftime('%d.%m.%y %H:%M:%S %f')[:21]
                self.LastBattleCacheHash = hash(frozenset(self.BattleCache.items()))
                needSave = False
                if self.Conditions:
                    for key in self.Conditions:
                        if key in self.BattleCache and self.Conditions[key] != self.BattleCache[key]:
                            needSave = True
                            self.Conditions[key] = self.BattleCache[key]
                else:
                    needSave = True
                if needSave:
                    try:
                        textLog = self.LogFormatter.format(**self.BattleCache)
                        with open(self.LogFileName, 'a') as file:
                            file.write(textLog)
                    except Exception as E:
                        self.Enable = False
                        message = '\'Meter Instruments\': file \'%s\' contains an error! Log disabled.' % os.path.basename(self.LogFormatterFileName)
                        print message
                        print str(E)
                        showMessage(message, 'yellow') 
        BigWorld.callback(self.UpdateTime, self.dumpLogUpdate)

# Functions ***********************************************************

def FloatToString(value, dig=20, leng=0, sep=' '):
    '''
    Форматирует любое число в строку:
    value - вещественное число, dig - точность округления, 
    leng - минимальная длина строки, дополняется нулями (0: откл),
    sep - разделитель разрядов ('': откл)
    '''
    avalue = ('%.' + str(dig) + 'f') % abs(round(value, dig))
    if '.' in avalue:
        Hi, Low = str(avalue).split('.')
        count = leng - len(Low)
        if count > 0:
            Low = Low + '0'*count
    else:
        Hi = avalue
        Low = ''
        count = leng - len(Hi)
        if count > 0:
            Hi = '0'*count + Hi     
    return ('-' if value < 0 else '') + \
           sep.join(Hi[i:i + DIGITS_PLACE] for i in range(0, len(Hi), DIGITS_PLACE)) + \
           ('.' + sep.join(Low[i:i + DIGITS_PLACE] for i in range(0, len(Low), DIGITS_PLACE)) if len(Low)>0 else '')

def FloatMatrixToString(matrix, dig=20, leng=0, sep=' ', style=0):
    '''
    Конвертирует матрицу (x,y,z) в строку:
    style - 0: [x, y, z], 1: (x, y, z), 2: x y z     
    '''
    text = ('[' if style==0 else '(' if style==1 else '') + FloatToString(matrix[0], dig, leng, sep)
    for element in matrix[1:]:
        text += (', ' if style in (0,1) else ' ') + FloatToString(element, dig, leng, sep)
    text += (']' if style==0 else ')' if style==1 else '')
    return text

def parseFormatter(text):
    result = {}
    for token in re.finditer( ur"{%.*?%}", text):
        if token.group():
            result[token.group()[1:-1]] = None
    return result    

def getBKeys(value):
    '''
    Парсит комбинации клавиш из строки
    '''
    result = []
    strings = [x.strip().upper() for x in value.split('+')]
    for key in strings:
        try:
            result.append(getattr(Keys, key))
        except:
            pass
    return tuple(result)  

def isBKeysDown(BKeys):
    '''
    Проверяет зажатие комбинации клавиш
    '''
    result = True
    if len(BKeys)>1:
        for key in BKeys:
            result = BigWorld.isKeyDown(key) and result
            if not result:
                break
    elif len(BKeys) == 1:
        if BKeys[0] in frozenset([Keys.KEY_LSHIFT, \
                                  Keys.KEY_LALT, \
                                  Keys.KEY_LCONTROL, \
                                  Keys.KEY_RSHIFT, \
                                  Keys.KEY_RALT, \
                                  Keys.KEY_RCONTROL]):
            result = BigWorld.isKeyDown(BKeys[0])
        else:
            result = BigWorld.isKeyDown(BKeys[0]) and \
                     not BigWorld.isKeyDown(Keys.KEY_LSHIFT) and \
                     not BigWorld.isKeyDown(Keys.KEY_LALT) and \
                     not BigWorld.isKeyDown(Keys.KEY_LCONTROL) and \
                     not BigWorld.isKeyDown(Keys.KEY_RSHIFT) and \
                     not BigWorld.isKeyDown(Keys.KEY_RALT) and \
                     not BigWorld.isKeyDown(Keys.KEY_RCONTROL)
    else:
        result = False
    return result

def showMessage(message, color, hangar=False):
    if message:
        battleWindow = g_appLoader.getDefBattleApp()
        if battleWindow is not None:
            if BigWorld.player() is not None:
                BigWorld.player().soundNotifications.play('chat_shortcut_common_fx')
            battleWindow.call('battle.VehicleMessagesPanel.ShowMessage', ['0', message, color])
        if hangar and g_hangarSpace is not None and g_hangarSpace.inited:
            message = '<textformat><font color="#E2D2A2" size="15"><b>Meter Instruments:</b></font><br><br><font color="#E2D2A2" size="14">%s</font></textformat>' % message
            SystemMessages.pushMessage(message, SystemMessages.SM_TYPE.GameGreeting)

def TargetUpdate(targetID):
    global GUI_TEXTLABLES, TARGET_CALLBACK
    if hasattr(BigWorld, 'player') and hasattr(BigWorld.player(), 'isVehicleAlive') and BigWorld.player().isVehicleAlive:
        Point = BigWorld.entity(targetID).position
        if Point is not None:        
            if GUI_TEXTLABLES.has_key('TargetPosition') and GUI_TEXTLABLES['TargetPosition'].Visible():
                GUI_TEXTLABLES['TargetPosition'].ValueMatrix(Point, DIGITS_COUNT, DIGITS_LEN)
            if '%TargetPosition%' in DUMP.BattleCache: DUMP.BattleCache['%TargetPosition%'] = FloatMatrixToString(Point, DUMP.DigitsCount, 0, '', 2)
            if '%TargetPosition%' in LOG.BattleCache: LOG.BattleCache['%TargetPosition%'] = FloatMatrixToString(Point, LOG.DigitsCount, 0, '', 2)
        distance = (BigWorld.entity(targetID).position - BigWorld.player().getOwnVehiclePosition()).length
        if GUI_TEXTLABLES.has_key('TankToTankDistance') and GUI_TEXTLABLES['TankToTankDistance'].Visible():
            GUI_TEXTLABLES['TankToTankDistance'].Value(distance, DIGITS_COUNT, DIGITS_LEN)
        if '%TankToTankDistance%' in DUMP.BattleCache: DUMP.BattleCache['%TankToTankDistance%'] = FloatToString(distance, DUMP.DigitsCount, 0, '')
        if '%TankToTankDistance%' in LOG.BattleCache: LOG.BattleCache['%TankToTankDistance%'] = FloatToString(distance, LOG.DigitsCount, 0, '')
        armorInfo = {}
        vehicle = BigWorld.entity(BigWorld.player().playerVehicleID)
        startPoint = vehicle.appearance.compoundModel.node(TankPartNames.GUN).position if (vehicle is not None) and vehicle.isStarted else None
        endPoint = BigWorld.player().inputHandler.getDesiredShotPoint()
        entity = BigWorld.entity(targetID)
        if startPoint is not None and endPoint is not None and entity is not None and entity.isStarted:
            shotDir = startPoint - endPoint
            shotDir.normalise()
            collisionResult = entity.collideSegment(startPoint, endPoint - shotDir * 1.0, False)
            if collisionResult is not None:
                armorInfo['Ricochet']    = False
                armorInfo['NormalArmor'] = collisionResult.armor
                armorInfo['NormalAngle'] = math.degrees(math.acos(collisionResult.hitAngleCos))
                armorInfo['Normalization'] = 0
                shellID   = BigWorld.player().vehicleTypeDescriptor.activeGunShotIndex
                shellType = BigWorld.player().vehicleTypeDescriptor.gun['shots'][shellID]['shell']['kind']
                shellCaliber = BigWorld.player().vehicleTypeDescriptor.gun['shots'][shellID]['shell']['caliber']
                if shellType == 'HOLLOW_CHARGE':
                    if armorInfo['NormalAngle'] >= 85:
                        armorInfo['Ricochet'] = True
                elif shellType in ['ARMOR_PIERCING', 'ARMOR_PIERCING_HE', 'ARMOR_PIERCING_CR']:
                    if armorInfo['NormalAngle'] >= 70 and shellCaliber < 3*armorInfo['NormalArmor']:
                        armorInfo['Ricochet'] = True
                    else:
                        if shellCaliber >= 2*armorInfo['NormalArmor']:
                            if armorInfo['NormalArmor'] > 0:
                                armorInfo['Normalization'] = min(armorInfo['NormalAngle'], (2 if shellType == 'ARMOR_PIERCING_CR' else 5) * 1.4 * shellCaliber / armorInfo['NormalArmor'])
                            else:
                                armorInfo['Normalization'] = armorInfo['NormalAngle']
                        else:
                            armorInfo['Normalization'] = min(armorInfo['NormalAngle'], (2 if shellType == 'ARMOR_PIERCING_CR' else 5))
                armorInfo['HitAngle'] = armorInfo['NormalAngle'] - armorInfo['Normalization']
                if armorInfo['HitAngle'] != 90:
                    armorInfo['ResultArmor'] = armorInfo['NormalArmor'] / math.cos(math.radians(armorInfo['HitAngle']))
        if GUI_TEXTLABLES.has_key('NormalArmor') and GUI_TEXTLABLES['NormalArmor'].Visible():
            if 'NormalArmor' in armorInfo: GUI_TEXTLABLES['NormalArmor'].Value(armorInfo['NormalArmor'], DIGITS_COUNT, DIGITS_LEN)
            else: GUI_TEXTLABLES['NormalArmor'].Text('-')
        if '%NormalArmor%' in DUMP.BattleCache:
            if 'NormalArmor' in armorInfo: DUMP.BattleCache['%NormalArmor%'] = FloatToString(armorInfo['NormalArmor'], DUMP.DigitsCount, 0, '')
            else: DUMP.BattleCache['%NormalArmor%'] = None
        if '%NormalArmor%' in LOG.BattleCache:
            if 'NormalArmor' in armorInfo: LOG.BattleCache['%NormalArmor%'] = FloatToString(armorInfo['NormalArmor'], LOG.DigitsCount, 0, '')
            else: LOG.BattleCache['%NormalArmor%'] = None
        if GUI_TEXTLABLES.has_key('NormalAngle') and GUI_TEXTLABLES['NormalAngle'].Visible():
            if 'NormalAngle' in armorInfo: GUI_TEXTLABLES['NormalAngle'].Value(armorInfo['NormalAngle'], DIGITS_COUNT, DIGITS_LEN)
            else: GUI_TEXTLABLES['NormalAngle'].Text('-')
        if '%NormalAngle%' in DUMP.BattleCache:
            if 'NormalAngle' in armorInfo: DUMP.BattleCache['%NormalAngle%'] = FloatToString(armorInfo['NormalAngle'], DUMP.DigitsCount, 0, '')
            else: DUMP.BattleCache['%NormalAngle%'] = None
        if '%NormalAngle%' in LOG.BattleCache:
            if 'NormalAngle' in armorInfo: LOG.BattleCache['%NormalAngle%'] = FloatToString(armorInfo['NormalAngle'], LOG.DigitsCount, 0, '')
            else: LOG.BattleCache['%NormalAngle%'] = None
        if GUI_TEXTLABLES.has_key('Normalization') and GUI_TEXTLABLES['Normalization'].Visible():
            if 'Normalization' in armorInfo: GUI_TEXTLABLES['Normalization'].Value(armorInfo['Normalization'], DIGITS_COUNT, DIGITS_LEN)
            else: GUI_TEXTLABLES['Normalization'].Text('-')
        if '%Normalization%' in DUMP.BattleCache:
            if 'Normalization' in armorInfo: DUMP.BattleCache['%Normalization%'] = FloatToString(armorInfo['Normalization'], DUMP.DigitsCount, 0, '')
            else: DUMP.BattleCache['%Normalization%'] = None
        if '%Normalization%' in LOG.BattleCache:
            if 'Normalization' in armorInfo: LOG.BattleCache['%Normalization%'] = FloatToString(armorInfo['Normalization'], LOG.DigitsCount, 0, '')
            else: LOG.BattleCache['%Normalization%'] = None
        if GUI_TEXTLABLES.has_key('HitAngle') and GUI_TEXTLABLES['HitAngle'].Visible():
            if 'HitAngle' in armorInfo: GUI_TEXTLABLES['HitAngle'].Value(armorInfo['HitAngle'], DIGITS_COUNT, DIGITS_LEN)
            else: GUI_TEXTLABLES['HitAngle'].Text('-')
        if '%HitAngle%' in DUMP.BattleCache:
            if 'HitAngle' in armorInfo: DUMP.BattleCache['%HitAngle%'] = FloatToString(armorInfo['HitAngle'], DUMP.DigitsCount, 0, '')
            else: DUMP.BattleCache['%HitAngle%'] = None
        if '%HitAngle%' in LOG.BattleCache:
            if 'HitAngle' in armorInfo: LOG.BattleCache['%HitAngle%'] = FloatToString(armorInfo['HitAngle'], LOG.DigitsCount, 0, '')
            else: LOG.BattleCache['%HitAngle%'] = None
        if GUI_TEXTLABLES.has_key('ResultArmor') and GUI_TEXTLABLES['ResultArmor'].Visible():
            if 'ResultArmor' in armorInfo:
                if armorInfo['Ricochet']: GUI_TEXTLABLES['ResultArmor'].Text('Ricochet!')
                else: GUI_TEXTLABLES['ResultArmor'].Value(armorInfo['ResultArmor'], DIGITS_COUNT, DIGITS_LEN)
            else: GUI_TEXTLABLES['ResultArmor'].Text('-')
        if '%ResultArmor%' in DUMP.BattleCache:
            if 'ResultArmor' in armorInfo:
                if armorInfo['Ricochet']: DUMP.BattleCache['%ResultArmor%'] = 'Ricochet!'
                else: DUMP.BattleCache['%ResultArmor%'] = FloatToString(armorInfo['ResultArmor'], DUMP.DigitsCount, 0, '')
            else: DUMP.BattleCache['%ResultArmor%'] = None
        if '%ResultArmor%' in LOG.BattleCache:
            if 'ResultArmor' in armorInfo:
                if armorInfo['Ricochet']: LOG.BattleCache['%ResultArmor%'] = 'Ricochet!'
                else: LOG.BattleCache['%ResultArmor%'] = FloatToString(armorInfo['ResultArmor'], LOG.DigitsCount, 0, '')
            else: LOG.BattleCache['%ResultArmor%'] = None
        TARGET_CALLBACK = BigWorld.callback(UPDATE_DELAY, partial(TargetUpdate, targetID))
            
def UniversalUpdate():
    global GUI_TEXTLABLES
    if hasattr(BigWorld, 'player') and hasattr(BigWorld.player(), 'isOnArena'):
        Point = BigWorld.camera().position
        if Point is not None:            
            if GUI_TEXTLABLES.has_key('CameraPosition') and GUI_TEXTLABLES['CameraPosition'].Visible():           
                GUI_TEXTLABLES['CameraPosition'].ValueMatrix(Point, DIGITS_COUNT, DIGITS_LEN)
            if '%CameraPosition%' in DUMP.BattleCache: DUMP.BattleCache['%CameraPosition%'] = FloatMatrixToString(Point, DUMP.DigitsCount, 0, '', 2)
            if '%CameraPosition%' in LOG.BattleCache: LOG.BattleCache['%CameraPosition%'] = FloatMatrixToString(Point, LOG.DigitsCount, 0, '', 2)
        if hasattr(BigWorld.player(), 'isVehicleAlive') and BigWorld.player().isVehicleAlive:
            vehicle = BigWorld.entity(BigWorld.player().playerVehicleID)
            startPoint = vehicle.appearance.compoundModel.node(TankPartNames.GUN).position if (vehicle is not None) and vehicle.isStarted else None
            stopPoint = BigWorld.player().inputHandler.getDesiredShotPoint()
            if startPoint is not None and stopPoint is not None:
                if GUI_TEXTLABLES.has_key('GunPosition') and GUI_TEXTLABLES['GunPosition'].Visible():
                    GUI_TEXTLABLES['GunPosition'].ValueMatrix(startPoint, DIGITS_COUNT, DIGITS_LEN)
                if '%GunPosition%' in DUMP.BattleCache: DUMP.BattleCache['%GunPosition%'] = FloatMatrixToString(startPoint, DUMP.DigitsCount, 0, '', 2)
                if '%GunPosition%' in LOG.BattleCache: LOG.BattleCache['%GunPosition%'] = FloatMatrixToString(startPoint, LOG.DigitsCount, 0, '', 2)
                distance = (BigWorld.player().getOwnVehiclePosition() - stopPoint).length
                if GUI_TEXTLABLES.has_key('TankToPointDistance') and GUI_TEXTLABLES['TankToPointDistance'].Visible():                    
                    GUI_TEXTLABLES['TankToPointDistance'].Value(distance, DIGITS_COUNT, DIGITS_LEN)
                if '%TankToPointDistance%' in DUMP.BattleCache: DUMP.BattleCache['%TankToPointDistance%'] = FloatToString(distance, DUMP.DigitsCount, 0, '')
                if '%TankToPointDistance%' in LOG.BattleCache: LOG.BattleCache['%TankToPointDistance%'] = FloatToString(distance, LOG.DigitsCount, 0, '')
                distance = (startPoint - stopPoint).length
                if GUI_TEXTLABLES.has_key('GunToPointDistance') and GUI_TEXTLABLES['GunToPointDistance'].Visible():
                    GUI_TEXTLABLES['GunToPointDistance'].Value(distance, DIGITS_COUNT, DIGITS_LEN)
                if '%GunToPointDistance%' in DUMP.BattleCache: DUMP.BattleCache['%GunToPointDistance%'] = FloatToString(distance, DUMP.DigitsCount, 0, '')
                if '%GunToPointDistance%' in LOG.BattleCache: LOG.BattleCache['%GunToPointDistance%'] = FloatToString(distance, LOG.DigitsCount, 0, '')
                startGunFirePoint = (Math.Matrix(vehicle.appearance.compoundModel.node('HP_gunFire'))).translation
                if GUI_TEXTLABLES.has_key('GunFirePosition') and GUI_TEXTLABLES['GunFirePosition'].Visible():
                    GUI_TEXTLABLES['GunFirePosition'].ValueMatrix(startGunFirePoint, DIGITS_COUNT, DIGITS_LEN)
                if '%GunFirePosition%' in DUMP.BattleCache: DUMP.BattleCache['%GunFirePosition%'] = FloatMatrixToString(startGunFirePoint, DUMP.DigitsCount, 0, '', 2)
                if '%GunFirePosition%' in LOG.BattleCache: LOG.BattleCache['%GunFirePosition%'] = FloatMatrixToString(startGunFirePoint, LOG.DigitsCount, 0, '', 2)
                if GUI_TEXTLABLES.has_key('PointPosition') and GUI_TEXTLABLES['PointPosition'].Visible():
                    GUI_TEXTLABLES['PointPosition'].ValueMatrix(stopPoint, DIGITS_COUNT, DIGITS_LEN)
                if '%PointPosition%' in DUMP.BattleCache: DUMP.BattleCache['%PointPosition%'] = FloatMatrixToString(stopPoint, DUMP.DigitsCount, 0, '', 2)
                if '%PointPosition%' in LOG.BattleCache: LOG.BattleCache['%PointPosition%'] = FloatMatrixToString(stopPoint, LOG.DigitsCount, 0, '', 2)
            Point = BigWorld.player().getOwnVehiclePosition()
            if Point is not None:
                if GUI_TEXTLABLES.has_key('PlayerPosition') and GUI_TEXTLABLES['PlayerPosition'].Visible():
                    GUI_TEXTLABLES['PlayerPosition'].ValueMatrix(Point, DIGITS_COUNT, DIGITS_LEN)
                if '%PlayerPosition%' in DUMP.BattleCache: DUMP.BattleCache['%PlayerPosition%'] = FloatMatrixToString(Point, DUMP.DigitsCount, 0, '', 2)
                if '%PlayerPosition%' in LOG.BattleCache: LOG.BattleCache['%PlayerPosition%'] = FloatMatrixToString(Point, LOG.DigitsCount, 0, '', 2)
            HullMat = Math.Matrix(BigWorld.player().getOwnVehicleStabilisedMatrix())
            if GUI_TEXTLABLES.has_key('HullYaw') and GUI_TEXTLABLES['HullYaw'].Visible():
                GUI_TEXTLABLES['HullYaw'].Value(math.degrees(HullMat.yaw), DIGITS_COUNT, DIGITS_LEN)
            if '%HullYaw%' in DUMP.BattleCache: DUMP.BattleCache['%HullYaw%'] = FloatToString(math.degrees(HullMat.yaw), DUMP.DigitsCount, 0, '')
            if '%HullYaw%' in LOG.BattleCache: LOG.BattleCache['%HullYaw%'] = FloatToString(math.degrees(HullMat.yaw), LOG.DigitsCount, 0, '')
            if GUI_TEXTLABLES.has_key('HullPitch') and GUI_TEXTLABLES['HullPitch'].Visible():
                GUI_TEXTLABLES['HullPitch'].Value(math.degrees(HullMat.pitch), DIGITS_COUNT, DIGITS_LEN)
            if '%HullPitch%' in DUMP.BattleCache: DUMP.BattleCache['%HullPitch%'] = FloatToString(math.degrees(HullMat.pitch), DUMP.DigitsCount, 0, '')
            if '%HullPitch%' in LOG.BattleCache: LOG.BattleCache['%HullPitch%'] = FloatToString(math.degrees(HullMat.pitch), LOG.DigitsCount, 0, '')
            if GUI_TEXTLABLES.has_key('HullRoll') and GUI_TEXTLABLES['HullRoll'].Visible():
                GUI_TEXTLABLES['HullRoll'].Value(math.degrees(HullMat.roll), DIGITS_COUNT, DIGITS_LEN)                
            if '%HullRoll%' in DUMP.BattleCache: DUMP.BattleCache['%HullRoll%'] = FloatToString(math.degrees(HullMat.roll), DUMP.DigitsCount, 0, '')
            if '%HullRoll%' in LOG.BattleCache: LOG.BattleCache['%HullRoll%'] = FloatToString(math.degrees(HullMat.roll), LOG.DigitsCount, 0, '')
        replayCtrl = BattleReplay.g_replayCtrl
        arena = BigWorld.player().arena
        remainingTime = replayCtrl.getArenaLength() if replayCtrl.isPlaying else arena.periodEndTime - BigWorld.serverTime()
        if GUI_TEXTLABLES.has_key('RemainingTime') and GUI_TEXTLABLES['RemainingTime'].Visible():
            GUI_TEXTLABLES['RemainingTime'].Value(remainingTime, DIGITS_COUNT, DIGITS_LEN)
        if '%RemainingTime%' in DUMP.BattleCache: DUMP.BattleCache['%RemainingTime%'] = FloatToString(remainingTime, DUMP.DigitsCount, 0, '')
        if '%RemainingTime%' in LOG.BattleCache: LOG.BattleCache['%RemainingTime%'] = FloatToString(remainingTime, LOG.DigitsCount, 0, '')
        currentTime = arena.periodLength - remainingTime
        if GUI_TEXTLABLES.has_key('CurrentTime') and GUI_TEXTLABLES['CurrentTime'].Visible():
            GUI_TEXTLABLES['CurrentTime'].Value(currentTime, DIGITS_COUNT, DIGITS_LEN)
        if '%CurrentTime%' in DUMP.BattleCache: DUMP.BattleCache['%CurrentTime%'] = FloatToString(currentTime, DUMP.DigitsCount, 0, '')
        if '%CurrentTime%' in LOG.BattleCache: LOG.BattleCache['%CurrentTime%'] = FloatToString(currentTime, LOG.DigitsCount, 0, '')
        ReplayTime = BattleReplay.g_replayCtrl.currentTime
        if GUI_TEXTLABLES.has_key('ReplayTime') and GUI_TEXTLABLES['ReplayTime'].Visible():
            GUI_TEXTLABLES['ReplayTime'].Value(ReplayTime, DIGITS_COUNT, DIGITS_LEN)
        if '%ReplayTime%' in DUMP.BattleCache: DUMP.BattleCache['%ReplayTime%'] = FloatToString(ReplayTime, DUMP.DigitsCount, 0, '')
        if '%ReplayTime%' in LOG.BattleCache: LOG.BattleCache['%ReplayTime%'] = FloatToString(ReplayTime, LOG.DigitsCount, 0, '')
        BigWorld.callback(UPDATE_DELAY, UniversalUpdate)   

def PlayerShellIconUpdate():
    if CONFIG['Shell']['Player']['Show'] and GUI_SHELLICON_PLAYER is not None:
        GUI_SHELLICON_PLAYER.FileName('objects/Meter/maps/icons/shell/%s.dds' % BigWorld.player().vehicleTypeDescriptor.gun['shots'][BigWorld.player().vehicleTypeDescriptor.activeGunShotIndex]['shell']['icon'][0][:-4])    

# Events ======================================================

def new_vehicle_onEnterWorld(self, vehicle):
    if old_vehicle_onEnterWorld is not None:
        old_vehicle_onEnterWorld(self, vehicle)
    global CollisionSkins
    if CollisionSkins.has_key(vehicle.id) and isinstance(vehicle, MVehicle.Vehicle) and vehicle.isStarted:
        if not CONFIG['CollisionSkins']['InSightOnly'] and vehicle.isAlive():
            compoundModel = vehicle.appearance.compoundModel
            for name, value in CollisionSkins[vehicle.id].iteritems():
                if not compoundModel.containsAttachment(value['fake_model']): 
                    compoundModel.node(name).attach(value['fake_model'])
                    value['model'].visible = True
            compoundModel.visible = False

def new_vehicle_onLeaveWorld(self, vehicle):
    global CollisionSkins
    try:
        if CollisionSkins.has_key(vehicle.id) and isinstance(vehicle, MVehicle.Vehicle) and vehicle.isStarted:
            compoundModel = vehicle.appearance.compoundModel
            compoundModel.visible = True
            for name, value in CollisionSkins[vehicle.id].iteritems():
                if compoundModel.containsAttachment(value['fake_model']):
                    value['model'].visible = False
                    compoundModel.node(name).detach(value['fake_model'])
    finally:
        if old_vehicle_onLeaveWorld is not None:
            old_vehicle_onLeaveWorld(self, vehicle)

def new_onArenaVehicleKilled(self, targetID, attackerID, equipmentID, reason):
    global CollisionSkins
    try:
        if targetID == BigWorld.player().playerVehicleID:
            if GUI_TEXTLABLES.has_key('TankToPointDistance') and GUI_TEXTLABLES['TankToPointDistance'].Visible(): GUI_TEXTLABLES['TankToPointDistance'].Disable()
            if GUI_TEXTLABLES.has_key('GunToPointDistance') and GUI_TEXTLABLES['GunToPointDistance'].Visible(): GUI_TEXTLABLES['GunToPointDistance'].Disable()        
            if GUI_TEXTLABLES.has_key('TankToTankDistance') and GUI_TEXTLABLES['TankToTankDistance'].Visible(): GUI_TEXTLABLES['TankToTankDistance'].Disable()
            #---------------------------------------------------
            if GUI_TEXTLABLES.has_key('PointPosition') and GUI_TEXTLABLES['PointPosition'].Visible(): GUI_TEXTLABLES['PointPosition'].Disable()
            if GUI_TEXTLABLES.has_key('GunPosition') and GUI_TEXTLABLES['GunPosition'].Visible(): GUI_TEXTLABLES['GunPosition'].Disable()
            if GUI_TEXTLABLES.has_key('GunFirePosition') and GUI_TEXTLABLES['GunFirePosition'].Visible(): GUI_TEXTLABLES['GunFirePosition'].Disable()
            if GUI_TEXTLABLES.has_key('PlayerPosition') and GUI_TEXTLABLES['PlayerPosition'].Visible(): GUI_TEXTLABLES['PlayerPosition'].Disable()
            #---------------------------------------------------
            if GUI_TEXTLABLES.has_key('NormalArmor') and GUI_TEXTLABLES['NormalArmor'].Visible(): GUI_TEXTLABLES['NormalArmor'].Disable()        
            if GUI_TEXTLABLES.has_key('NormalAngle') and GUI_TEXTLABLES['NormalAngle'].Visible(): GUI_TEXTLABLES['NormalAngle'].Disable()
            if GUI_TEXTLABLES.has_key('Normalization') and GUI_TEXTLABLES['Normalization'].Visible(): GUI_TEXTLABLES['Normalization'].Disable()
            if GUI_TEXTLABLES.has_key('HitAngle') and GUI_TEXTLABLES['HitAngle'].Visible(): GUI_TEXTLABLES['HitAngle'].Disable()
            if GUI_TEXTLABLES.has_key('ResultArmor') and GUI_TEXTLABLES['ResultArmor'].Visible(): GUI_TEXTLABLES['ResultArmor'].Disable()        
            #---------------------------------------------------
            if GUI_TEXTLABLES.has_key('TurretYaw') and GUI_TEXTLABLES['TurretYaw'].Visible(): GUI_TEXTLABLES['TurretYaw'].Disable()
            if GUI_TEXTLABLES.has_key('GunPitch') and GUI_TEXTLABLES['GunPitch'].Visible(): GUI_TEXTLABLES['GunPitch'].Disable()
            if GUI_TEXTLABLES.has_key('AbsTurretYaw') and GUI_TEXTLABLES['AbsTurretYaw'].Visible(): GUI_TEXTLABLES['AbsTurretYaw'].Disable()
            if GUI_TEXTLABLES.has_key('AbsGunPitch') and GUI_TEXTLABLES['AbsGunPitch'].Visible(): GUI_TEXTLABLES['AbsGunPitch'].Disable()
            if GUI_TEXTLABLES.has_key('HullYaw') and GUI_TEXTLABLES['HullYaw'].Visible(): GUI_TEXTLABLES['HullYaw'].Disable()
            if GUI_TEXTLABLES.has_key('HullPitch') and GUI_TEXTLABLES['HullPitch'].Visible(): GUI_TEXTLABLES['HullPitch'].Disable()
            if GUI_TEXTLABLES.has_key('HullRoll') and GUI_TEXTLABLES['HullRoll'].Visible(): GUI_TEXTLABLES['HullRoll'].Disable()
            #---------------------------------------------------
            if GUI_TEXTLABLES.has_key('TankDirectSpeed') and GUI_TEXTLABLES['TankDirectSpeed'].Visible(): GUI_TEXTLABLES['TankDirectSpeed'].Disable()
            if GUI_TEXTLABLES.has_key('TankRotateSpeed') and GUI_TEXTLABLES['TankRotateSpeed'].Visible(): GUI_TEXTLABLES['TankRotateSpeed'].Disable()
            #---------------------------------------------------
            if GUI_TEXTLABLES.has_key('GunToMarkerDistance') and GUI_TEXTLABLES['GunToMarkerDistance'].Visible(): GUI_TEXTLABLES['GunToMarkerDistance'].Disable()
            if GUI_TEXTLABLES.has_key('MarkerPosition') and GUI_TEXTLABLES['MarkerPosition'].Visible(): GUI_TEXTLABLES['MarkerPosition'].Disable()
            if GUI_TEXTLABLES.has_key('DispersionAngle') and GUI_TEXTLABLES['DispersionAngle'].Visible(): GUI_TEXTLABLES['DispersionAngle'].Disable()
            if GUI_TEXTLABLES.has_key('DispersionRadius') and GUI_TEXTLABLES['DispersionRadius'].Visible(): GUI_TEXTLABLES['DispersionRadius'].Disable()
        if CollisionSkins.has_key(targetID):
            vehicle = BigWorld.entity(targetID)
            if (vehicle is not None) and isinstance(vehicle, MVehicle.Vehicle) and vehicle.isStarted:
                compoundModel = vehicle.appearance.compoundModel
                compoundModel.visible = True
                for name, value in CollisionSkins[vehicle.id].iteritems():
                    if compoundModel.containsAttachment(value['fake_model']):
                        value['model'].visible = False
                        compoundModel.node(name).detach(value['fake_model'])
    finally:
        if old_onArenaVehicleKilled is not None:
            old_onArenaVehicleKilled(self, targetID, attackerID, equipmentID, reason)

def add_onCurrentShellChanged(_):
    BigWorld.callback(0.5, PlayerShellIconUpdate)

def new__startGUI(self):
    global GUI_TEXTLABLES, GUI_SHELLICON_PLAYER, GUI_SHELLICON_OTHER, \
           PLAYER_SHOTS, PLAYER_SHOTS_COUNT, CollisionSkins
    if old__startGUI is not None:
        old__startGUI(self)
    g_sessionProvider.getAmmoCtrl().onCurrentShellChanged += add_onCurrentShellChanged
    CF = CONFIG['TextLabels']
    #Дистанции
    if CF['TankToPointDistance']['Enable']: GUI_TEXTLABLES['TankToPointDistance'] = TextLabel(CF['TankToPointDistance']['Caption'], '', CF['TankToPointDistance']['Postfix'], True, CF['TankToPointDistance']['Position'][0], CF['TankToPointDistance']['Position'][1], CF['TankToPointDistance']['Color'])
    if CF['GunToPointDistance']['Enable']:  GUI_TEXTLABLES['GunToPointDistance']  = TextLabel(CF['GunToPointDistance']['Caption'],  '', CF['GunToPointDistance']['Postfix'],  True, CF['GunToPointDistance']['Position'][0],  CF['GunToPointDistance']['Position'][1],  CF['GunToPointDistance']['Color'])  
    if CF['TankToTankDistance']['Enable']:  GUI_TEXTLABLES['TankToTankDistance']  = TextLabel(CF['TankToTankDistance']['Caption'],  '', CF['TankToTankDistance']['Postfix'],  False, CF['TankToTankDistance']['Position'][0], CF['TankToTankDistance']['Position'][1],  CF['TankToTankDistance']['Color'])
    #Координаты
    if CF['CameraPosition']['Enable']: GUI_TEXTLABLES['CameraPosition']  = TextLabel(CF['CameraPosition']['Caption'], '',   CF['CameraPosition']['Postfix'], True,  CF['CameraPosition']['Position'][0], CF['CameraPosition']['Position'][1], CF['CameraPosition']['Color'])
    if CF['PointPosition']['Enable']:  GUI_TEXTLABLES['PointPosition']   = TextLabel(CF['PointPosition']['Caption'],  '',   CF['PointPosition']['Postfix'],  True,  CF['PointPosition']['Position'][0],  CF['PointPosition']['Position'][1],  CF['PointPosition']['Color'])
    if CF['GunPosition']['Enable']:    GUI_TEXTLABLES['GunPosition']     = TextLabel(CF['GunPosition']['Caption'],    '',   CF['GunPosition']['Postfix'],    True,  CF['GunPosition']['Position'][0],    CF['GunPosition']['Position'][1],    CF['GunPosition']['Color'])
    if CF['GunFirePosition']['Enable']: GUI_TEXTLABLES['GunFirePosition']  = TextLabel(CF['GunFirePosition']['Caption'], '',   CF['GunFirePosition']['Postfix'], True,  CF['GunFirePosition']['Position'][0], CF['GunFirePosition']['Position'][1], CF['GunFirePosition']['Color'])
    if CF['PlayerPosition']['Enable']: GUI_TEXTLABLES['PlayerPosition']  = TextLabel(CF['PlayerPosition']['Caption'], '',   CF['PlayerPosition']['Postfix'], True,  CF['PlayerPosition']['Position'][0], CF['PlayerPosition']['Position'][1], CF['PlayerPosition']['Color'])
    if CF['TargetPosition']['Enable']: GUI_TEXTLABLES['TargetPosition']  = TextLabel(CF['TargetPosition']['Caption'], '',   CF['TargetPosition']['Postfix'], False, CF['TargetPosition']['Position'][0], CF['TargetPosition']['Position'][1], CF['TargetPosition']['Color'])
    #Стрельба
    if CF['ShotCount']['Enable']:
        GUI_TEXTLABLES['ShotCount'] = TextLabel(CF['ShotCount']['Caption'], '0', CF['ShotCount']['Postfix'], True, CF['ShotCount']['Position'][0], CF['ShotCount']['Position'][1], CF['ShotCount']['Color'])    
    PLAYER_SHOTS_COUNT = 0
    if CF['HitPointPosition']['Enable']:
        GUI_TEXTLABLES['HitPointPosition'] = TextLabel(CF['HitPointPosition']['Caption'], '[]', CF['HitPointPosition']['Postfix'], True, CF['HitPointPosition']['Position'][0], CF['HitPointPosition']['Position'][1], CF['HitPointPosition']['Color'])
    if CF['TimeFlight']['Enable']:
        GUI_TEXTLABLES['TimeFlight'] = TextLabel(CF['TimeFlight']['Caption'], '-', CF['TimeFlight']['Postfix'], True, CF['TimeFlight']['Position'][0], CF['TimeFlight']['Position'][1], CF['TimeFlight']['Color'])
    PLAYER_SHOTS = {'ID': [], 'Info': {}}
    #Пробитие брони
    if CF['NormalArmor']['Enable']:   GUI_TEXTLABLES['NormalArmor']   = TextLabel(CF['NormalArmor']['Caption'],   '', CF['NormalArmor']['Postfix'],   False, CF['NormalArmor']['Position'][0],   CF['NormalArmor']['Position'][1],   CF['NormalArmor']['Color'])    
    if CF['NormalAngle']['Enable']:   GUI_TEXTLABLES['NormalAngle']   = TextLabel(CF['NormalAngle']['Caption'],   '', CF['NormalAngle']['Postfix'],   False, CF['NormalAngle']['Position'][0],   CF['NormalAngle']['Position'][1],   CF['NormalAngle']['Color'])
    if CF['Normalization']['Enable']: GUI_TEXTLABLES['Normalization'] = TextLabel(CF['Normalization']['Caption'], '', CF['Normalization']['Postfix'], False, CF['Normalization']['Position'][0], CF['Normalization']['Position'][1], CF['Normalization']['Color'])
    if CF['HitAngle']['Enable']:      GUI_TEXTLABLES['HitAngle']      = TextLabel(CF['HitAngle']['Caption'],      '', CF['HitAngle']['Postfix'],      False, CF['HitAngle']['Position'][0],      CF['HitAngle']['Position'][1],      CF['HitAngle']['Color'])
    if CF['ResultArmor']['Enable']:   GUI_TEXTLABLES['ResultArmor']   = TextLabel(CF['ResultArmor']['Caption'],   '', CF['ResultArmor']['Postfix'],   False, CF['ResultArmor']['Position'][0],   CF['ResultArmor']['Position'][1],   CF['ResultArmor']['Color'])
    #Характеристики
    if CF['TurretYaw']['Enable']:    GUI_TEXTLABLES['TurretYaw']    = TextLabel(CF['TurretYaw']['Caption'],    '0', CF['TurretYaw']['Postfix'],    True, CF['TurretYaw']['Position'][0], CF['TurretYaw']['Position'][1],    CF['TurretYaw']['Color'])
    if CF['GunPitch']['Enable']:     GUI_TEXTLABLES['GunPitch']     = TextLabel(CF['GunPitch']['Caption'],     '0', CF['GunPitch']['Postfix'],     True, CF['GunPitch']['Position'][0],  CF['GunPitch']['Position'][1],     CF['GunPitch']['Color'])
    if CF['AbsTurretYaw']['Enable']: GUI_TEXTLABLES['AbsTurretYaw'] = TextLabel(CF['AbsTurretYaw']['Caption'], '0', CF['AbsTurretYaw']['Postfix'], True, CF['TurretYaw']['Position'][0], CF['AbsTurretYaw']['Position'][1], CF['AbsTurretYaw']['Color'])
    if CF['AbsGunPitch']['Enable']:  GUI_TEXTLABLES['AbsGunPitch']  = TextLabel(CF['AbsGunPitch']['Caption'],  '0', CF['AbsGunPitch']['Postfix'],  True, CF['AbsGunPitch']['Position'][0],  CF['AbsGunPitch']['Position'][1],  CF['AbsGunPitch']['Color'])
    if CF['HullYaw']['Enable']:      GUI_TEXTLABLES['HullYaw']      = TextLabel(CF['HullYaw']['Caption'],      '0', CF['HullYaw']['Postfix'],      True, CF['HullYaw']['Position'][0],   CF['HullYaw']['Position'][1],      CF['HullYaw']['Color'])
    if CF['HullPitch']['Enable']:    GUI_TEXTLABLES['HullPitch']    = TextLabel(CF['HullPitch']['Caption'],    '0', CF['HullPitch']['Postfix'],    True, CF['HullPitch']['Position'][0], CF['HullPitch']['Position'][1],    CF['HullPitch']['Color'])
    if CF['HullRoll']['Enable']:     GUI_TEXTLABLES['HullRoll']     = TextLabel(CF['HullRoll']['Caption'],     '0', CF['HullRoll']['Postfix'],     True, CF['HullRoll']['Position'][0],  CF['HullRoll']['Position'][1],     CF['HullRoll']['Color'])
    if CF['TankDirectSpeed']['Enable']: GUI_TEXTLABLES['TankDirectSpeed'] = TextLabel(CF['TankDirectSpeed']['Caption'], '0', CF['TankDirectSpeed']['Postfix'], True, CF['TankDirectSpeed']['Position'][0], CF['TankDirectSpeed']['Position'][1], CF['TankDirectSpeed']['Color'])
    if CF['TankRotateSpeed']['Enable']: GUI_TEXTLABLES['TankRotateSpeed'] = TextLabel(CF['TankRotateSpeed']['Caption'], '0', CF['TankRotateSpeed']['Postfix'], True, CF['TankRotateSpeed']['Position'][0], CF['TankRotateSpeed']['Position'][1], CF['TankRotateSpeed']['Color'])
    #Прицел
    if CF['GunToMarkerDistance']['Enable']: GUI_TEXTLABLES['GunToMarkerDistance'] = TextLabel(CF['GunToMarkerDistance']['Caption'], '0', CF['GunToMarkerDistance']['Postfix'],  True, CF['GunToMarkerDistance']['Position'][0],  CF['GunToMarkerDistance']['Position'][1],  CF['GunToMarkerDistance']['Color'])
    if CF['MarkerPosition']['Enable']:   GUI_TEXTLABLES['MarkerPosition']   = TextLabel(CF['MarkerPosition']['Caption'],   '[]', CF['MarkerPosition']['Postfix'],   True, CF['MarkerPosition']['Position'][0],   CF['MarkerPosition']['Position'][1],   CF['MarkerPosition']['Color'])
    if CF['DispersionAngle']['Enable']:  GUI_TEXTLABLES['DispersionAngle']  = TextLabel(CF['DispersionAngle']['Caption'],  '0', CF['DispersionAngle']['Postfix'],  True, CF['DispersionAngle']['Position'][0],  CF['DispersionAngle']['Position'][1],  CF['DispersionAngle']['Color'])
    if CF['DispersionRadius']['Enable']: GUI_TEXTLABLES['DispersionRadius'] = TextLabel(CF['DispersionRadius']['Caption'], '0', CF['DispersionRadius']['Postfix'], True, CF['DispersionRadius']['Position'][0], CF['DispersionRadius']['Position'][1], CF['DispersionRadius']['Color'])
    #Системные
    if CF['CurrentTime']['Enable']:   GUI_TEXTLABLES['CurrentTime'] = TextLabel(CF['CurrentTime']['Caption'], '', CF['CurrentTime']['Postfix'], True, CF['CurrentTime']['Position'][0], CF['CurrentTime']['Position'][1], CF['CurrentTime']['Color'])
    if CF['RemainingTime']['Enable']: GUI_TEXTLABLES['RemainingTime'] = TextLabel(CF['RemainingTime']['Caption'], '', CF['RemainingTime']['Postfix'], True, CF['RemainingTime']['Position'][0], CF['RemainingTime']['Position'][1], CF['RemainingTime']['Color'])
    if CF['ReplayTime']['Enable']: GUI_TEXTLABLES['ReplayTime'] = TextLabel(CF['ReplayTime']['Caption'], '', CF['ReplayTime']['Postfix'], True, CF['ReplayTime']['Position'][0], CF['ReplayTime']['Position'][1], CF['ReplayTime']['Color'])
    #------------------
    BigWorld.callback(5.0, UniversalUpdate)
    #Иконки
    if CONFIG['Shell']['Player']['Show']:
        CF = CONFIG['Shell']['Player']
        GUI_SHELLICON_PLAYER = Image(CF['Width'], CF['Height'], '', CF['Position'][0], CF['Position'][1])
        GUI_SHELLICON_PLAYER.Enable()
    if  CONFIG['Shell']['Other']['Show']:
        CF = CONFIG['Shell']['Other']
        GUI_SHELLICON_OTHER = Image(CF['Width'], CF['Height'], '', CF['Position'][0], CF['Position'][1])
    if CONFIG['Devices']['Player']['Show']:
        CF = CONFIG['Devices']['Player']
        x, y = CF['Position']
        GUI_DEVICESICONS_PLAYER.append(Image(CF['Width'], CF['Height'], '', x, y))
        GUI_DEVICESICONS_PLAYER[0].FileName('objects/Meter/%s.dds' % BigWorld.player().vehicleTypeDescriptor.optionalDevices[0].icon[0][3:-4] \
                                            if BigWorld.player().vehicleTypeDescriptor.optionalDevices[0] is not None else \
                                            'objects/Meter/maps/icons/artefact/empty.dds')
        GUI_DEVICESICONS_PLAYER[0].Enable()
        x += CF['Width'] + 6
        GUI_DEVICESICONS_PLAYER.append(Image(CF['Width'], CF['Height'], '', x, y))
        GUI_DEVICESICONS_PLAYER[1].FileName('objects/Meter/%s.dds' % BigWorld.player().vehicleTypeDescriptor.optionalDevices[1].icon[0][3:-4] \
                                            if BigWorld.player().vehicleTypeDescriptor.optionalDevices[1] is not None else \
                                            'objects/Meter/maps/icons/artefact/empty.dds')
        GUI_DEVICESICONS_PLAYER[1].Enable()
        x += CF['Width'] + 6
        GUI_DEVICESICONS_PLAYER.append(Image(CF['Width'], CF['Height'], '', x, y))
        GUI_DEVICESICONS_PLAYER[2].FileName('objects/Meter/%s.dds' % BigWorld.player().vehicleTypeDescriptor.optionalDevices[2].icon[0][3:-4] \
                                            if BigWorld.player().vehicleTypeDescriptor.optionalDevices[2] is not None else \
                                            'objects/Meter/maps/icons/artefact/empty.dds')
        GUI_DEVICESICONS_PLAYER[2].Enable()
    if CONFIG['Devices']['Other']['Show']:
        CF = CONFIG['Devices']['Other']
        x, y = CF['Position']
        GUI_DEVICESICONS_OTHER.append(Image(CF['Width'], CF['Height'], '', x, y))
        x += CF['Width'] + 6
        GUI_DEVICESICONS_OTHER.append(Image(CF['Width'], CF['Height'], '', x, y))
        x += CF['Width'] + 6
        GUI_DEVICESICONS_OTHER.append(Image(CF['Width'], CF['Height'], '', x, y))
    #Лог
    LOG.initCache()
    if '%TankName%' in DUMP.BattleCache: DUMP.BattleCache['%TankName%'] = BigWorld.player().vehicleTypeDescriptor.type.shortUserString
    if '%TankName%' in LOG.BattleCache: LOG.BattleCache['%TankName%'] = BigWorld.player().vehicleTypeDescriptor.type.shortUserString
    #Коллинжи пробития
    if CONFIG['CollisionSkins']['Show']:
        vehicles = BigWorld.player().arena.vehicles
        for vID, desc in vehicles.items():
            if not CONFIG['CollisionSkins']['EnemyOnly'] or desc['team'] != vehicles[BigWorld.player().playerVehicleID]['team']:
                CollisionSkins[vID] = {TankPartNames.CHASSIS: {'model': None, 'fake_model': None, '_stateFunc': lambda a, b: a['vehicleType'].chassis['models'][b]},
                                       TankPartNames.HULL:    {'model': None, 'fake_model': None, '_stateFunc': lambda a, b: a['vehicleType'].hull['models'][b]},
                                       TankPartNames.TURRET:  {'model': None, 'fake_model': None, '_stateFunc': lambda a, b: a['vehicleType'].turret['models'][b]},
                                       TankPartNames.GUN:     {'model': None, 'fake_model': None, '_stateFunc': lambda a, b: a['vehicleType'].gun['models'][b]}}
                for value in CollisionSkins[vID].itervalues():
                    value['fake_model'] = BigWorld.Model('objects/fake_model.model')
                    value['model'] = BigWorld.Model(value['_stateFunc'](desc, 'undamaged').replace('normal/lod0/', 'collision_client/'))
                    value['model'].addMotor(BigWorld.Servo(value['fake_model'].matrix))
                    BigWorld.addModel(value['model'])
                    value['model'].visible = False

def new_AvatarReady():
    global CollisionSkins
    if not CONFIG['CollisionSkins']['EnemyOnly'] and not CONFIG['CollisionSkins']['InSightOnly']: #Показываем коллинжи на старте
        for vehicle in BigWorld.entities.values():
            if CollisionSkins.has_key(vehicle.id) and vehicle.isAlive() and vehicle.isStarted:
                compoundModel = vehicle.appearance.compoundModel
                for name, value in CollisionSkins[vehicle.id].iteritems():
                    compoundModel.node(name).attach(value['fake_model'])
                    value['model'].visible = True
                compoundModel.visible = False 

def new__destroyGUI(self):
    global GUI_TEXTLABLES, GUI_SHELLICON_PLAYER, GUI_SHELLICON_OTHER, \
           GUI_DEVICESICONS_PLAYER, GUI_DEVICESICONS_OTHER, CollisionSkins
    try:
        g_sessionProvider.getAmmoCtrl().onCurrentShellChanged -= add_onCurrentShellChanged
        if GUI_TEXTLABLES:
            for value in GUI_TEXTLABLES:
                if GUI_TEXTLABLES[value].Visible():
                    GUI_TEXTLABLES[value].Disable()
            GUI_TEXTLABLES.clear()
        if CONFIG['Shell']['Player']['Show'] and GUI_SHELLICON_PLAYER is not None:
            if GUI_SHELLICON_PLAYER.Visible():
                GUI_SHELLICON_PLAYER.Disable()
            GUI_SHELLICON_PLAYER = None
        if  CONFIG['Shell']['Other']['Show'] and GUI_SHELLICON_OTHER is not None:
            if GUI_SHELLICON_OTHER.Visible():
                GUI_SHELLICON_OTHER.Disable()
            GUI_SHELLICON_OTHER = None
        if CONFIG['Devices']['Player']['Show'] and GUI_DEVICESICONS_PLAYER:
            if GUI_DEVICESICONS_PLAYER[0].Visible():
                GUI_DEVICESICONS_PLAYER[0].Disable()
            if GUI_DEVICESICONS_PLAYER[1].Visible():
                GUI_DEVICESICONS_PLAYER[1].Disable()
            if GUI_DEVICESICONS_PLAYER[2].Visible():
                GUI_DEVICESICONS_PLAYER[2].Disable()
            GUI_DEVICESICONS_PLAYER = []
        if CONFIG['Devices']['Other']['Show'] and GUI_DEVICESICONS_OTHER:
            if GUI_DEVICESICONS_OTHER[0].Visible():
                GUI_DEVICESICONS_OTHER[0].Disable()
            if GUI_DEVICESICONS_OTHER[1].Visible():
                GUI_DEVICESICONS_OTHER[1].Disable()
            if GUI_DEVICESICONS_OTHER[2].Visible():
                GUI_DEVICESICONS_OTHER[2].Disable()
            GUI_DEVICESICONS_OTHER = []
        for vID in CollisionSkins:
            for value in CollisionSkins[vID].itervalues():
                if value['model'] in BigWorld.models():
                    BigWorld.delModel(value['model'])
        CollisionSkins.clear()
    finally:
        if old__destroyGUI is not None:
            old__destroyGUI(self)

def new_targetFocus(self, entity):    
    if old_targetFocus is not None:
        old_targetFocus(self, entity)
    global CollisionSkins
    if isinstance(entity, MVehicle.Vehicle) and entity.isAlive():
        if GUI_TEXTLABLES.has_key('TankToTankDistance'): GUI_TEXTLABLES['TankToTankDistance'].Enable()
        if GUI_TEXTLABLES.has_key('TargetPosition'): GUI_TEXTLABLES['TargetPosition'].Enable()
        if GUI_TEXTLABLES.has_key('NormalArmor'): GUI_TEXTLABLES['NormalArmor'].Enable()
        if GUI_TEXTLABLES.has_key('NormalAngle'): GUI_TEXTLABLES['NormalAngle'].Enable()
        if GUI_TEXTLABLES.has_key('Normalization'): GUI_TEXTLABLES['Normalization'].Enable()
        if GUI_TEXTLABLES.has_key('HitAngle'): GUI_TEXTLABLES['HitAngle'].Enable()
        if GUI_TEXTLABLES.has_key('ResultArmor'): GUI_TEXTLABLES['ResultArmor'].Enable()
        if CollisionSkins.has_key(entity.id) and entity.isStarted:
            if CONFIG['CollisionSkins']['InSightOnly'] and (not CONFIG['CollisionSkins']['EnemyOnly'] or (entity.publicInfo['team'] != BigWorld.player().team)):
                compoundModel = entity.appearance.compoundModel
                for name, value in CollisionSkins[entity.id].iteritems():
                    if not compoundModel.containsAttachment(value['fake_model']): 
                        compoundModel.node(name).attach(value['fake_model'])
                        value['model'].visible = True
                compoundModel.visible = False
        if  CONFIG['Shell']['Other']['Show'] and GUI_SHELLICON_OTHER is not None:
            GUI_SHELLICON_OTHER.FileName('objects/Meter/maps/icons/shell/' + entity.typeDescriptor.gun['shots'][entity.typeDescriptor.activeGunShotIndex]['shell']['icon'][0][:-3] + 'dds')
            GUI_SHELLICON_OTHER.Enable()
        if CONFIG['Devices']['Other']['Show'] and GUI_DEVICESICONS_OTHER: 
            GUI_DEVICESICONS_OTHER[0].FileName('objects/Meter/%s.dds' % entity.typeDescriptor.optionalDevices[0].icon[0][3:-4] \
                                               if entity.typeDescriptor.optionalDevices[0] is not None else \
                                               'objects/Meter/maps/icons/artefact/empty.dds')
            GUI_DEVICESICONS_OTHER[1].FileName('objects/Meter/%s.dds' % entity.typeDescriptor.optionalDevices[1].icon[0][3:-4] \
                                               if entity.typeDescriptor.optionalDevices[1] is not None else \
                                               'objects/Meter/maps/icons/artefact/empty.dds')
            GUI_DEVICESICONS_OTHER[2].FileName('objects/Meter/%s.dds' % entity.typeDescriptor.optionalDevices[2].icon[0][3:-4] \
                                               if entity.typeDescriptor.optionalDevices[2] is not None else \
                                               'objects/Meter/maps/icons/artefact/empty.dds')
            x, y = CONFIG['Devices']['Other']['Position']
            GUI_DEVICESICONS_OTHER[0].Position(x, y)
            GUI_DEVICESICONS_OTHER[0].Enable()
            x += CONFIG['Devices']['Other']['Width'] + 6
            GUI_DEVICESICONS_OTHER[1].Position(x, y)
            GUI_DEVICESICONS_OTHER[1].Enable()
            x += CONFIG['Devices']['Other']['Width'] + 6
            GUI_DEVICESICONS_OTHER[2].Position(x, y)
            GUI_DEVICESICONS_OTHER[2].Enable()
        TargetUpdate(entity.id)

def new_targetBlur(self, prevEntity):
    global TARGET_CALLBACK, CollisionSkins
    try:
        if isinstance(prevEntity, MVehicle.Vehicle):
            if TARGET_CALLBACK != None:
                BigWorld.cancelCallback(TARGET_CALLBACK)
                TARGET_CALLBACK = None
            if GUI_TEXTLABLES.has_key('TankToTankDistance') and GUI_TEXTLABLES['TankToTankDistance'].Visible(): GUI_TEXTLABLES['TankToTankDistance'].Disable()
            if GUI_TEXTLABLES.has_key('TargetPosition') and GUI_TEXTLABLES['TargetPosition'].Visible(): GUI_TEXTLABLES['TargetPosition'].Disable()
            if GUI_TEXTLABLES.has_key('NormalArmor') and GUI_TEXTLABLES['NormalArmor'].Visible(): GUI_TEXTLABLES['NormalArmor'].Disable()
            if GUI_TEXTLABLES.has_key('NormalAngle') and GUI_TEXTLABLES['NormalAngle'].Visible(): GUI_TEXTLABLES['NormalAngle'].Disable()
            if GUI_TEXTLABLES.has_key('Normalization') and GUI_TEXTLABLES['Normalization'].Visible(): GUI_TEXTLABLES['Normalization'].Disable()
            if GUI_TEXTLABLES.has_key('HitAngle') and GUI_TEXTLABLES['HitAngle'].Visible(): GUI_TEXTLABLES['HitAngle'].Disable()
            if GUI_TEXTLABLES.has_key('ResultArmor') and GUI_TEXTLABLES['ResultArmor'].Visible(): GUI_TEXTLABLES['ResultArmor'].Disable()
            if '%TargetPosition%' in DUMP.BattleCache: DUMP.BattleCache['%TargetPosition%'] = None
            if '%TargetPosition%' in LOG.BattleCache: LOG.BattleCache['%TargetPosition%'] = None
            if '%TankToTankDistance%' in DUMP.BattleCache: DUMP.BattleCache['%TankToTankDistance%'] = None
            if '%TankToTankDistance%' in LOG.BattleCache: LOG.BattleCache['%TankToTankDistance%'] = None
            if '%NormalArmor%' in DUMP.BattleCache: DUMP.BattleCache['%NormalArmor%'] = None
            if '%NormalArmor%' in LOG.BattleCache: LOG.BattleCache['%NormalArmor%'] = None
            if '%NormalAngle%' in DUMP.BattleCache: DUMP.BattleCache['%NormalAngle%'] = None
            if '%NormalAngle%' in LOG.BattleCache: LOG.BattleCache['%NormalAngle%'] = None
            if '%Normalization%' in DUMP.BattleCache: DUMP.BattleCache['%Normalization%'] = None
            if '%Normalization%' in LOG.BattleCache: LOG.BattleCache['%Normalization%'] = None
            if '%HitAngle%' in DUMP.BattleCache: DUMP.BattleCache['%HitAngle%'] = None
            if '%HitAngle%' in LOG.BattleCache: LOG.BattleCache['%HitAngle%'] = None
            if '%ResultArmor%' in DUMP.BattleCache: DUMP.BattleCache['%ResultArmor%'] = None
            if '%ResultArmor%' in LOG.BattleCache: LOG.BattleCache['%ResultArmor%'] = None
            if CollisionSkins.has_key(prevEntity.id) and prevEntity.isAlive() and prevEntity.isStarted:
                if CONFIG['CollisionSkins']['InSightOnly'] and (not CONFIG['CollisionSkins']['EnemyOnly'] or (prevEntity.publicInfo['team'] != BigWorld.player().team)):
                    compoundModel = prevEntity.appearance.compoundModel
                    compoundModel.visible = True
                    for name, value in CollisionSkins[prevEntity.id].iteritems():
                        if compoundModel.containsAttachment(value['fake_model']):
                            value['model'].visible = False
                            compoundModel.node(name).detach(value['fake_model'])
            if  CONFIG['Shell']['Other']['Show'] and GUI_SHELLICON_OTHER is not None:
                GUI_SHELLICON_OTHER.Disable()
            if CONFIG['Devices']['Other']['Show'] and GUI_DEVICESICONS_OTHER:
                GUI_DEVICESICONS_OTHER[0].Disable()
                GUI_DEVICESICONS_OTHER[1].Disable()
                GUI_DEVICESICONS_OTHER[2].Disable()
    finally:
        if old_targetBlur is not None:
            old_targetBlur(self, prevEntity)

def new_showTracer(self, shooterID, shotID, isRicochet, effectsIndex, refStartPoint, velocity, gravity, maxShotDist):
    global PLAYER_SHOTS, PLAYER_SHOTS_COUNT
    if old_showTracer is not None:
        old_showTracer(self, shooterID, shotID, isRicochet, effectsIndex, refStartPoint, velocity, gravity, maxShotDist)
    if shooterID == BigWorld.player().playerVehicleID and BigWorld.player().isVehicleAlive:
        PLAYER_SHOTS_COUNT += 1
        if GUI_TEXTLABLES.has_key('ShotCount') and GUI_TEXTLABLES['ShotCount'].Visible():
            GUI_TEXTLABLES['ShotCount'].Text(PLAYER_SHOTS_COUNT)
        if '%ShotCount%' in DUMP.BattleCache: DUMP.BattleCache['%ShotCount%'] = PLAYER_SHOTS_COUNT
        if '%ShotCount%' in LOG.BattleCache: LOG.BattleCache['%ShotCount%'] = PLAYER_SHOTS_COUNT
        PLAYER_SHOTS['ID'].append(shotID)
        PLAYER_SHOTS['Info'][shotID] = {}
        remainingTime = BattleReplay.g_replayCtrl.getArenaLength() if BattleReplay.g_replayCtrl.isPlaying else BigWorld.player().arena.periodEndTime - BigWorld.serverTime()
        PLAYER_SHOTS['Info'][shotID]['Time'] = remainingTime
        if GUI_TEXTLABLES.has_key('HitPointPosition') and GUI_TEXTLABLES['HitPointPosition'].Visible():
            GUI_TEXTLABLES['HitPointPosition'].Text('[]')
        if GUI_TEXTLABLES.has_key('TimeFlight') and GUI_TEXTLABLES['TimeFlight'].Visible():
            GUI_TEXTLABLES['TimeFlight'].Text('-')
    
def new_stopTracer(self, shotID, endPoint):
    global PLAYER_SHOTS
    if old_stopTracer is not None:
        old_stopTracer(self, shotID, endPoint)
    if BigWorld.player().isVehicleAlive:
        if shotID in PLAYER_SHOTS['ID']:
            PLAYER_SHOTS['ID'].remove(shotID)
            remainingTime = BattleReplay.g_replayCtrl.getArenaLength() if BattleReplay.g_replayCtrl.isPlaying else BigWorld.player().arena.periodEndTime - BigWorld.serverTime()
            PLAYER_SHOTS['Info'][shotID]['Time'] -= remainingTime
            if GUI_TEXTLABLES.has_key('TimeFlight') and GUI_TEXTLABLES['TimeFlight'].Visible():
                GUI_TEXTLABLES['TimeFlight'].Value(PLAYER_SHOTS['Info'][shotID]['Time'], DIGITS_COUNT, DIGITS_LEN)
            if '%TimeFlight%' in DUMP.BattleCache: DUMP.BattleCache['%TimeFlight%'] = FloatToString(PLAYER_SHOTS['Info'][shotID]['Time'], DUMP.DigitsCount, 0, '')
            if '%TimeFlight%' in LOG.BattleCache: LOG.BattleCache['%TimeFlight%'] = FloatToString(PLAYER_SHOTS['Info'][shotID]['Time'], LOG.DigitsCount, 0, '')
            if GUI_TEXTLABLES.has_key('HitPointPosition') and GUI_TEXTLABLES['HitPointPosition'].Visible():
                GUI_TEXTLABLES['HitPointPosition'].ValueMatrix(endPoint, DIGITS_COUNT, DIGITS_LEN)
            if '%HitPointPosition%' in DUMP.BattleCache: DUMP.BattleCache['%HitPointPosition%'] = FloatMatrixToString(endPoint, DUMP.DigitsCount, 0, '', 2)
            if '%HitPointPosition%' in LOG.BattleCache: LOG.BattleCache['%HitPointPosition%'] = FloatMatrixToString(endPoint, LOG.DigitsCount, 0, '', 2)
            

def new_explodeProjectile(self, shotID, effectsIndex, effectMaterialIndex, endPoint, velocityDir, damagedDestructibles):
    global PLAYER_SHOTS
    if old_explodeProjectile is not None:
        old_explodeProjectile(self, shotID, effectsIndex, effectMaterialIndex, endPoint, velocityDir, damagedDestructibles)    
    if BigWorld.player().isVehicleAlive:
        if shotID in PLAYER_SHOTS['ID']:
            PLAYER_SHOTS['ID'].remove(shotID)
            remainingTime = BattleReplay.g_replayCtrl.getArenaLength() if BattleReplay.g_replayCtrl.isPlaying else BigWorld.player().arena.periodEndTime - BigWorld.serverTime()
            PLAYER_SHOTS['Info'][shotID]['Time'] -= remainingTime
            if GUI_TEXTLABLES.has_key('TimeFlight') and GUI_TEXTLABLES['TimeFlight'].Visible():
                GUI_TEXTLABLES['TimeFlight'].Value(PLAYER_SHOTS['Info'][shotID]['Time'], DIGITS_COUNT, DIGITS_LEN)
            if '%TimeFlight%' in DUMP.BattleCache: DUMP.BattleCache['%TimeFlight%'] = FloatToString(PLAYER_SHOTS['Info'][shotID]['Time'], DUMP.DigitsCount, 0, '')
            if '%TimeFlight%' in LOG.BattleCache: LOG.BattleCache['%TimeFlight%'] = FloatToString(PLAYER_SHOTS['Info'][shotID]['Time'], LOG.DigitsCount, 0, '')            
            if GUI_TEXTLABLES.has_key('HitPointPosition') and GUI_TEXTLABLES['HitPointPosition'].Visible():
                    GUI_TEXTLABLES['HitPointPosition'].ValueMatrix(endPoint, DIGITS_COUNT, DIGITS_LEN)
            if '%HitPointPosition%' in DUMP.BattleCache: DUMP.BattleCache['%HitPointPosition%'] = FloatMatrixToString(endPoint, DUMP.DigitsCount, 0, '', 2)
            if '%HitPointPosition%' in LOG.BattleCache: LOG.BattleCache['%HitPointPosition%'] = FloatMatrixToString(endPoint, LOG.DigitsCount, 0, '', 2)

def new_getOwnVehicleSpeeds(self, getInstantaneous = False):
    result = old_getOwnVehicleSpeeds(self, getInstantaneous)
    try:
        if GUI_TEXTLABLES.has_key('TankDirectSpeed') and GUI_TEXTLABLES['TankDirectSpeed'].Visible():
            GUI_TEXTLABLES['TankDirectSpeed'].Value(result[0], DIGITS_COUNT, DIGITS_LEN)
        if '%TankDirectSpeed%' in DUMP.BattleCache: DUMP.BattleCache['%TankDirectSpeed%'] = FloatToString(result[0], DUMP.DigitsCount, 0, '')
        if '%TankDirectSpeed%' in LOG.BattleCache: LOG.BattleCache['%TankDirectSpeed%'] = FloatToString(result[0], LOG.DigitsCount, 0, '')
        if GUI_TEXTLABLES.has_key('TankRotateSpeed') and GUI_TEXTLABLES['TankRotateSpeed'].Visible():
            GUI_TEXTLABLES['TankRotateSpeed'].Value(math.degrees(result[1]), DIGITS_COUNT, DIGITS_LEN)
        if '%TankRotateSpeed%' in DUMP.BattleCache: DUMP.BattleCache['%TankRotateSpeed%'] = FloatToString(math.degrees(result[1]), DUMP.DigitsCount, 0, '')
        if '%TankRotateSpeed%' in LOG.BattleCache: LOG.BattleCache['%TankRotateSpeed%'] = FloatToString(math.degrees(result[1]), LOG.DigitsCount, 0, '')
    finally:
        return result

def new_VehicleGunRotator__updateGunMarker(self): #POST SERVER INFO
    if old_VehicleGunRotator__updateGunMarker is not None:
        old_VehicleGunRotator__updateGunMarker(self)
        
    shotPos, _ = self._VehicleGunRotator__getCurShotPosition()
    if GUI_TEXTLABLES.has_key('GunToMarkerDistance') and GUI_TEXTLABLES['GunToMarkerDistance'].Visible():
        GUI_TEXTLABLES['GunToMarkerDistance'].Value((self._VehicleGunRotator__markerInfo[0] - shotPos).length, DIGITS_COUNT, DIGITS_LEN)
    if '%GunToMarkerDistance%' in DUMP.BattleCache: DUMP.BattleCache['%GunToMarkerDistance%'] = FloatToString((self._VehicleGunRotator__markerInfo[0] - shotPos).length, DUMP.DigitsCount, 0, '')
    if '%GunToMarkerDistance%' in LOG.BattleCache: LOG.BattleCache['%GunToMarkerDistance%'] = FloatToString((self._VehicleGunRotator__markerInfo[0] - shotPos).length, LOG.DigitsCount, 0, '')
    if GUI_TEXTLABLES.has_key('MarkerPosition') and GUI_TEXTLABLES['MarkerPosition'].Visible():
        GUI_TEXTLABLES['MarkerPosition'].ValueMatrix(self._VehicleGunRotator__markerInfo[0], DIGITS_COUNT, DIGITS_LEN)
    if '%MarkerPosition%' in DUMP.BattleCache: DUMP.BattleCache['%MarkerPosition%'] = FloatMatrixToString(self._VehicleGunRotator__markerInfo[0], DUMP.DigitsCount, 0, '', 2)
    if '%MarkerPosition%' in LOG.BattleCache: LOG.BattleCache['%MarkerPosition%'] = FloatMatrixToString(self._VehicleGunRotator__markerInfo[0], LOG.DigitsCount, 0, '', 2)
    if GUI_TEXTLABLES.has_key('TurretYaw') and GUI_TEXTLABLES['TurretYaw'].Visible():
        GUI_TEXTLABLES['TurretYaw'].Value(math.degrees(self._VehicleGunRotator__turretYaw), DIGITS_COUNT, DIGITS_LEN)
    if '%TurretYaw%' in DUMP.BattleCache: DUMP.BattleCache['%TurretYaw%'] = FloatToString(math.degrees(self._VehicleGunRotator__turretYaw), DUMP.DigitsCount, 0, '')
    if '%TurretYaw%' in LOG.BattleCache: LOG.BattleCache['%TurretYaw%'] = FloatToString(math.degrees(self._VehicleGunRotator__turretYaw), LOG.DigitsCount, 0, '')
    if GUI_TEXTLABLES.has_key('GunPitch') and GUI_TEXTLABLES['GunPitch'].Visible():
        GUI_TEXTLABLES['GunPitch'].Value(math.degrees(self._VehicleGunRotator__gunPitch), DIGITS_COUNT, DIGITS_LEN)
    if '%GunPitch%' in DUMP.BattleCache: DUMP.BattleCache['%GunPitch%'] = FloatToString(math.degrees(self._VehicleGunRotator__gunPitch), DUMP.DigitsCount, 0, '')
    if '%GunPitch%' in LOG.BattleCache: LOG.BattleCache['%GunPitch%'] = FloatToString(math.degrees(self._VehicleGunRotator__gunPitch), LOG.DigitsCount, 0, '')
    gunMat = AimingSystems.getPlayerGunMat(self._VehicleGunRotator__turretYaw, self._VehicleGunRotator__gunPitch)
    if GUI_TEXTLABLES.has_key('AbsTurretYaw') and GUI_TEXTLABLES['AbsTurretYaw'].Visible():
        GUI_TEXTLABLES['AbsTurretYaw'].Value(math.degrees(gunMat.yaw), DIGITS_COUNT, DIGITS_LEN)
    if '%AbsTurretYaw%' in DUMP.BattleCache: DUMP.BattleCache['%AbsTurretYaw%'] = FloatToString(math.degrees(gunMat.yaw), DUMP.DigitsCount, 0, '')
    if '%AbsTurretYaw%' in LOG.BattleCache: LOG.BattleCache['%AbsTurretYaw%'] = FloatToString(math.degrees(gunMat.yaw), LOG.DigitsCount, 0, '')
    if GUI_TEXTLABLES.has_key('AbsGunPitch') and GUI_TEXTLABLES['AbsGunPitch'].Visible():
        GUI_TEXTLABLES['AbsGunPitch'].Value(math.degrees(gunMat.pitch), DIGITS_COUNT, DIGITS_LEN)
    if '%AbsGunPitch%' in DUMP.BattleCache: DUMP.BattleCache['%AbsGunPitch%'] = FloatToString(math.degrees(gunMat.pitch), DUMP.DigitsCount, 0, '')
    if '%AbsGunPitch%' in LOG.BattleCache: LOG.BattleCache['%AbsGunPitch%'] = FloatToString(math.degrees(gunMat.pitch), LOG.DigitsCount, 0, '')
    if GUI_TEXTLABLES.has_key('DispersionAngle') and GUI_TEXTLABLES['DispersionAngle'].Visible():
        GUI_TEXTLABLES['DispersionAngle'].Value(self._VehicleGunRotator__dispersionAngles[0], DIGITS_COUNT, DIGITS_LEN)
    if '%DispersionAngle%' in DUMP.BattleCache: DUMP.BattleCache['%DispersionAngle%'] = FloatToString(self._VehicleGunRotator__dispersionAngles[0], DUMP.DigitsCount, 0, '')
    if '%DispersionAngle%' in LOG.BattleCache: LOG.BattleCache['%DispersionAngle%'] = FloatToString(self._VehicleGunRotator__dispersionAngles[0], LOG.DigitsCount, 0, '')
    if GUI_TEXTLABLES.has_key('DispersionRadius') and GUI_TEXTLABLES['DispersionRadius'].Visible():
        GUI_TEXTLABLES['DispersionRadius'].Value(self._VehicleGunRotator__markerInfo[2] * 0.5, DIGITS_COUNT, DIGITS_LEN)
    if '%DispersionRadius%' in DUMP.BattleCache: DUMP.BattleCache['%DispersionRadius%'] = FloatToString(self._VehicleGunRotator__markerInfo[2] * 0.5, DUMP.DigitsCount, 0, '')
    if '%DispersionRadius%' in LOG.BattleCache: LOG.BattleCache['%DispersionRadius%'] = FloatToString(self._VehicleGunRotator__markerInfo[2] * 0.5, LOG.DigitsCount, 0, '')

def new_DynamicArcadeCameraInit(self, dataSec, aim):
    if old_DynamicArcadeCameraInit is not None:
        old_DynamicArcadeCameraInit(self, dataSec, aim)
    self._ArcadeCamera__cfg['distRange'] = MinMax(self._ArcadeCamera__cfg['distRange'][0], CONFIG['CameraTuner']['DistanceMax']) 
    self._ArcadeCamera__cfg['startDist'] = CONFIG['CameraTuner']['DistanceDefault']
    if CONFIG['CameraTuner']['Remove_DinamycEffects']:
        #Динамическая камера
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

def new_ArcadeCameraEnable(self, preferredPos = None, closesDist = False, postmortemParams = None, turretYaw = None, gunPitch = None):
    if old_ArcadeCameraEnable is not None:
        store = self._ArcadeCamera__postmortemMode
        self._ArcadeCamera__postmortemMode = False
        try:
            old_ArcadeCameraEnable(self, preferredPos, closesDist, postmortemParams, turretYaw, gunPitch)
        finally:
            self._ArcadeCamera__postmortemMode = store

def new_DynamicSniperCameraInit(self, dataSec, aim, binoculars):
    global GUI_TEXTLABLES
    if old_DynamicSniperCameraInit is not None:
        old_DynamicSniperCameraInit(self, dataSec, aim, binoculars)
    self._SniperCamera__cfg['zooms'] = CONFIG['CameraTuner']['SniperZoomSteps']
    self._SniperCamera__cfg['zoom']  = CONFIG['CameraTuner']['SniperZoomSteps'][0]  
    self._SniperCamera__cfg['increasedZoom'] = True
    if CONFIG['CameraTuner']['Remove_DinamycEffects']:
        #Динамическая камера
        self._SniperCamera__dynamicCfg['accelerationSensitivity']     = Vector3(0.0, 0.0, 0.0)
        self._SniperCamera__dynamicCfg['accelerationThreshold']       = 0.0
        self._SniperCamera__dynamicCfg['accelerationMax']             = 0.0
        self._SniperCamera__dynamicCfg['maxShotImpulseDistance']      = 0.0
        self._SniperCamera__dynamicCfg['maxExplosionImpulseDistance'] = 0.0
        self._SniperCamera__dynamicCfg['impulsePartToRoll']           = 0.0
        self._SniperCamera__dynamicCfg['pivotShift']                  = Vector3(0, -0.5, 0)
        for x in self._SniperCamera__dynamicCfg['impulseSensitivities']:
            self._SniperCamera__dynamicCfg['impulseSensitivities'][x] = 0.0
        for x in self._SniperCamera__dynamicCfg['impulseLimits']:
            self._SniperCamera__dynamicCfg['impulseLimits'][x] = (0.0, 0.0)
        for x in self._SniperCamera__dynamicCfg['noiseSensitivities']:
            self._SniperCamera__dynamicCfg['noiseSensitivities'][x] = 0.0
        for x in self._SniperCamera__dynamicCfg['noiseLimits']:
            self._SniperCamera__dynamicCfg['noiseLimits'][x] = (0.0, 0.0)
    self._SniperCamera__dynamicCfg['zoomExposure'] = tuple(0.5 for x in range(len(CONFIG['CameraTuner']['SniperZoomSteps'])))
    if CONFIG['CameraTuner']['ZoomIndicator']['Show']:
        GUI_TEXTLABLES['ZoomIndicator'] = TextLabel('x', '%.1f' %  self._SniperCamera__cfg['zoom'], '', False, \
           CONFIG['CameraTuner']['ZoomIndicator']['Position'][0], CONFIG['CameraTuner']['ZoomIndicator']['Position'][1], CONFIG['CameraTuner']['ZoomIndicator']['Color'], 'ZoomIndicator.font')

def new_DynamicSniperCamera__onSettingsChanged(self, diff):
    if 'fov' in diff:
        self.delayCallback(0.01, self._SniperCamera__applyZoom, self._SniperCamera__cfg['zoom'])

def new_SniperCameraEnable(self, targetPos, saveZoom):
    if old_SniperCameraEnable is not None:
        old_SniperCameraEnable(self, targetPos, saveZoom)
    if GUI_TEXTLABLES.has_key('ZoomIndicator') and not GUI_TEXTLABLES['ZoomIndicator'].Visible(): GUI_TEXTLABLES['ZoomIndicator'].Enable()

def new_SniperCameraDisable(self):
    if old_SniperCameraDisable is not None:
        old_SniperCameraDisable(self)
    if GUI_TEXTLABLES.has_key('ZoomIndicator') and GUI_TEXTLABLES['ZoomIndicator'].Visible(): GUI_TEXTLABLES['ZoomIndicator'].Disable()

def new_SniperCamera__SetupZoom(self, dz):
    if old_SniperCamera__SetupZoom is not None:
        old_SniperCamera__SetupZoom(self, dz)
    if GUI_TEXTLABLES.has_key('ZoomIndicator') and GUI_TEXTLABLES['ZoomIndicator'].Visible():
        GUI_TEXTLABLES['ZoomIndicator'].Text('%.1f' % self._SniperCamera__cfg['zoom'])

def new_Dynamic_StrategicCamera_init(self, dataSec, aim):
    if old_Dynamic_StrategicCamera_init is not None:
        old_Dynamic_StrategicCamera_init(self, dataSec, aim)
    self._StrategicCamera__cfg['distRange'] = [self._StrategicCamera__cfg['distRange'][0], CONFIG['CameraTuner']['DistanceMax']]
    if CONFIG['CameraTuner']['Remove_DinamycEffects']: #Динамическая камера
        for x in self._StrategicCamera__dynamicCfg['impulseSensitivities']:
            self._StrategicCamera__dynamicCfg['impulseSensitivities'][x] = 0.0
        for x in self._StrategicCamera__dynamicCfg['impulseLimits']:
            self._StrategicCamera__dynamicCfg['impulseLimits'][x] = (0.0, 0.0)
        for x in self._StrategicCamera__dynamicCfg['noiseSensitivities']:
            self._StrategicCamera__dynamicCfg['noiseSensitivities'][x] = 0.0
        for x in self._StrategicCamera__dynamicCfg['noiseLimits']:
            self._StrategicCamera__dynamicCfg['noiseLimits'][x] = (0.0, 0.0)

#Стабилизация
def new_EnableHorizontalStabilizerRuntime(self, enable):
    yawConstraint = math.pi * 2.1 if CONFIG['CameraTuner']['HorizontalStabilizer'] else 0.0
    self._SniperAimingSystem__yprDeviationConstraints.x = yawConstraint

#Cглаживание
def new_SmothCamera__InputInertiaGlide(self, posDelta):
    self._InputInertia__deltaEasing.reset(posDelta, Vector3(0.0), 0.001)

#Мигание и дрожание при попадании
def new_null_effect(self, model, list, args):
    pass

#Колебания при выстреле
def new_OscillatorInit(self, mass, stiffness, drag, constraints):
    if old_OscillatorInit is not None:
        old_OscillatorInit(self, 1e-05, (1e-05, 1e-05, 1e-05), (1e-05, 1e-05, 1e-05), (0.0, 0.0, 0.0))
        
def new_NoiseOscillatorInit(self, mass, stiffness, drag, restEpsilon=0.001):
    if old_NoiseOscillatorInit is not None:
        old_NoiseOscillatorInit(self, 1e-05, (1e-05, 1e-05, 1e-05), (1e-05, 1e-05, 1e-05), restEpsilon)

def new_RandomNoiseOscillatorFlat(mass, stiffness, drag, restEpsilon = 0.01):
    if old_RandomNoiseOscillatorFlat is not None:
        return old_RandomNoiseOscillatorFlat(1e-05, 1e-05, 1e-05, restEpsilon)

def new_RandomNoiseOscillatorSpherical(mass, stiffness, drag, scaleCoeff = Vector3(1.0, 1.0, 1.0), restEpsilon = 0.01):
    if old_RandomNoiseOscillatorSpherical is not None:
        return old_RandomNoiseOscillatorSpherical(1e-05, 1e-05, 1e-05, (0.0, 0.0, 0.0), restEpsilon)

# Hooks +++++++++++++++++++++++++++++++++++++++++++++++++++++++

if CONFIG:
    DUMP = DumpToFile()
    LOG  = LogToFile()
    LOG.dumpLogUpdate()
    
    old__startGUI = PlayerAvatar._PlayerAvatar__startGUI
    PlayerAvatar._PlayerAvatar__startGUI = new__startGUI
    
    old__destroyGUI = PlayerAvatar._PlayerAvatar__destroyGUI
    PlayerAvatar._PlayerAvatar__destroyGUI = new__destroyGUI

    old_vehicle_onEnterWorld = PlayerAvatar.vehicle_onEnterWorld
    PlayerAvatar.vehicle_onEnterWorld = new_vehicle_onEnterWorld
    
    old_vehicle_onLeaveWorld = PlayerAvatar.vehicle_onLeaveWorld
    PlayerAvatar.vehicle_onLeaveWorld = new_vehicle_onLeaveWorld

    old_onArenaVehicleKilled = PlayerAvatar._PlayerAvatar__onArenaVehicleKilled
    PlayerAvatar._PlayerAvatar__onArenaVehicleKilled = new_onArenaVehicleKilled

    old_targetFocus = PlayerAvatar.targetFocus
    PlayerAvatar.targetFocus = new_targetFocus
    
    old_targetBlur = PlayerAvatar.targetBlur
    PlayerAvatar.targetBlur = new_targetBlur

    old_showTracer = PlayerAvatar.showTracer
    PlayerAvatar.showTracer = new_showTracer

    old_stopTracer = PlayerAvatar.stopTracer
    PlayerAvatar.stopTracer = new_stopTracer

    old_explodeProjectile = PlayerAvatar.explodeProjectile
    PlayerAvatar.explodeProjectile = new_explodeProjectile
    
    old_getOwnVehicleSpeeds = PlayerAvatar.getOwnVehicleSpeeds
    PlayerAvatar.getOwnVehicleSpeeds = new_getOwnVehicleSpeeds

    old_VehicleGunRotator__updateGunMarker = VehicleGunRotator._VehicleGunRotator__updateGunMarker
    VehicleGunRotator._VehicleGunRotator__updateGunMarker = new_VehicleGunRotator__updateGunMarker
    
    old_DynamicArcadeCameraInit = ArcadeCamera.__init__
    ArcadeCamera.__init__ = new_DynamicArcadeCameraInit
    
    old_ArcadeCameraEnable = ArcadeCamera.enable
    ArcadeCamera.enable = new_ArcadeCameraEnable
    
    old_DynamicSniperCameraInit = SniperCamera.__init__
    SniperCamera.__init__ = new_DynamicSniperCameraInit
    
    SniperCamera._SniperCamera__onSettingsChanged = new_DynamicSniperCamera__onSettingsChanged
    
    old_SniperCameraEnable = SniperCamera.enable
    SniperCamera.enable = new_SniperCameraEnable
    
    old_SniperCameraDisable = SniperCamera.disable
    SniperCamera.disable = new_SniperCameraDisable
    
    old_SniperCamera__SetupZoom = SniperCamera._SniperCamera__setupZoom
    SniperCamera._SniperCamera__setupZoom = new_SniperCamera__SetupZoom

    old_Dynamic_StrategicCamera_init = StrategicCamera.__init__
    StrategicCamera.__init__ = new_Dynamic_StrategicCamera_init

    SniperAimingSystem.enableHorizontalStabilizerRuntime = new_EnableHorizontalStabilizerRuntime
    
    if CONFIG['CameraTuner']['Remove_DinamycEffects']:
        _InputInertia.glide = new_SmothCamera__InputInertiaGlide

        old_OscillatorInit = Oscillator.Oscillator.__init__
        Oscillator.Oscillator.__init__ = new_OscillatorInit
    
        old_NoiseOscillatorInit = Oscillator.NoiseOscillator.__init__
        Oscillator.NoiseOscillator.__init__ = new_NoiseOscillatorInit
    
        old_RandomNoiseOscillatorFlat = Oscillator.RandomNoiseOscillatorFlat
        Oscillator.RandomNoiseOscillatorFlat = new_RandomNoiseOscillatorFlat
    
        old_RandomNoiseOscillatorSpherical = Oscillator.RandomNoiseOscillatorSpherical
        Oscillator.RandomNoiseOscillatorSpherical = new_RandomNoiseOscillatorSpherical

    if CONFIG['CameraTuner']['Remove_DamageEffects']:
        helpers.EffectsList._FlashBangEffectDesc.create = new_null_effect
        helpers.EffectsList._ShockWaveEffectDesc.create = new_null_effect

    if CONFIG['CollisionSkins']['Show']:
        g_playerEvents.onAvatarReady += new_AvatarReady