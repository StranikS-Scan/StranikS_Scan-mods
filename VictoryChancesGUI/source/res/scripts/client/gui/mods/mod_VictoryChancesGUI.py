# -*- coding: utf-8 -*-

__author__  = 'StranikS_Scan'
__version__ = 'V2.2 P2.7 W1.0.0 17.03.2018'

import BigWorld, Event, BattleReplay, Keys
from gui.Scaleform.framework.entities.BaseDAAPIComponent import BaseDAAPIComponent
from gui.Scaleform.framework.entities.View import View
from gui.Scaleform.framework.managers.loaders import ViewLoadParams
from gui.Scaleform.framework import g_entitiesFactories, ViewSettings, ViewTypes, ScopeTemplates
from gui.shared import g_eventBus, events, EVENT_BUS_SCOPE
from gui.Scaleform.genConsts.BATTLE_VIEW_ALIASES import BATTLE_VIEW_ALIASES
from gui.app_loader import g_appLoader
from gui import g_guiResetters
from gui import InputHandler

from Avatar import PlayerAvatar

import re
from datetime import datetime
import ResMgr, os, codecs, json
import unicodedata

# Consts and Vars ..........................................................................

CONFIG_FILENAME = None
LOG_FILENAME    = None

SHOW_INFO  = True
SHOW_ITEMS = {}
KEYS_SHOWHIDEALL = {}
KEYS_TANKSLIST = {}
PRINT_LOG  = True
PRINT_ITEMS = {}

NEW_BATTLE = False

GUI_TEXT  = {'Name': 'VictoryChancesGUI',
             'Font': 'Lucida Console',
             'Bold': True,
             'Size': 16,
             'Color': '#00EDFF',
             'Pos': (400, -400),
             'Alpha': 0.95,
             'Shadow': True,
             'LastChangeColor': ('#FC2847','#28FC47'),
             'CompareValuesColor': ('#28FC47','#FC2847'),
             'ToolTip': 'VictoryChancesGUI Panel'}

# Text Flash ===========================================================

import GUI

class FlashTextLabel(object):
    def __init__(self, params):
        self.text = ''
        self.visible = True
        self.name = params['Name']
        options = {'visible': self.visible, 'width': 350, 'height': 600, \
                   'drag': True, 'multiline': True, 'border': True, 'text': self.text, \
                   'shadow': {'distance': 0, 'angle': 135, 'color': 0x101010, 'alpha': 0.95, 'blurX': 2, 'blurY': 2, 'strength': 1, 'quality': 1}}
        self.x, self.y = params['Pos'] if 'Pos' in params else (0,0)
        screenWidth, screenHeight = GUI.screenResolution()
        options['x'] = screenWidth // 2 + self.x
        options['y'] = screenHeight // 2 + self.y
        if 'Alpha' in params:
            options['alpha'] = params['Alpha']
        if 'ToolTip' in params:
            options['tooltip'] = params['ToolTip']
        #---
        self.font = params['Font'] if 'Font' in params else 'Arial'
        self.size = params['Size'] if 'Size' in params else 16
        self.bold = params['Bold'] if 'Bold' in params else False
        self.italic = params['Italic'] if 'Italic' in params else False
        self.color = params['Color'] if 'Color' in params else '#FFFFFF'
        self.begin = '<font face="%s" size="%d" color="%s">%s%s' % (self.font, self.size, self.color, '<b>' if self.bold else '', '<i>' if self.italic else '')
        self.end   = '%s%s</font>' % ('</b>' if self.bold else '', '</i>' if self.italic else '')
        #===
        g_guiFlash.createComponent(self.name, COMPONENT_TYPE.LABEL, options)
        COMPONENT_EVENT.UPDATED += self.updatePosition

    def __del__(self):
        COMPONENT_EVENT.UPDATED -= self.updatePosition
        g_guiFlash.deleteComponent(self.name)

    def setPosition(self, value):
        self.x, self.y = value
        screenWidth, screenHeight = GUI.screenResolution()
        g_guiFlash.updateComponent(self.name, {'x': screenWidth // 2 + self.x, 'y': screenHeight // 2 + self.y})

    def updatePosition(self, name, options):
        if str(name) == self.name:
            x = options.get('x')
            y = options.get('y')
            if x is not None and y is not None:
                screenWidth, screenHeight = GUI.screenResolution()
                x -= screenWidth // 2
                y -= screenHeight // 2
                if x != self.x or y != self.y:
                    self.x = x
                    self.y = y
                    if CONFIG_FILENAME:
                        s = re.sub('"Position"\s*:\s*\[\s*-?\s*\d+\s*,\s*-?\s*\d+\s*\]', '"Position": [%d,%d]' % (self.x, self.y), codecs.open(CONFIG_FILENAME, 'r', 'utf-8-sig').read())
                        with codecs.open(CONFIG_FILENAME, 'w', 'utf-8-sig') as f:
                            f.write(s)

    def getSimpleTextWithTags(self, text):
        return self.begin + text + self.end if text else ''

    def getHtmlTextWithTags(self, text, font=None, size=None, color=None, bold=None, italic=None):
        return '<font face="%s" size="%d" color="%s">%s%s%s%s%s</font>' % (font if font else self.font, size if size else self.size,
               color if color else self.color, '<b>' if bold or self.bold else '', '<i>' if italic or self.italic else '', text, \
               '</b>' if bold or self.bold else '', '</i>' if italic or self.italic else '') if text else ''

    def getHtmlTextWithTagsOnly(self, text, font=None, size=None, color=None, bold=None, italic=None):
        if font or size or color:
            return '<font %s %s %s>%s%s%s%s%s</font>' % ('face="%s"' % font if font else '', 'size="%d"' % size if size else '',
                   'color="%s"' % color if color else '', '<b>' if bold else '', '<i>' if italic else '', text, \
                   '</b>' if bold else '', '</i>' if italic else '') if text else ''
        else:
            return '%s%s%s%s%s' % ('<b>' if bold else '', '<i>' if italic else '', text, '</b>' if bold else '', '</i>' if italic else '') if text else ''

    def SimpleText(self, text):
        self.text = text
        g_guiFlash.updateComponent(self.name, {'text': self.begin + self.text + self.end if self.text else self.text})

    def HtmlText(self, text):
        self.text = text
        g_guiFlash.updateComponent(self.name, {'text': self.text})

    def Visible(self, value):
        self.visible = value
        g_guiFlash.updateComponent(self.name, {'visible': self.visible})

# Classes and functions ===========================================================

def getRoot():
    root = ''
    values = ResMgr.openSection('../paths.xml')['Paths'].values()[0:2]
    for value in values:
        if 'res_mods' in value.asString:
            continue
        root = value.asString + '/'
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
    filename = getRoot() + 'configs/VictoryChancesGUI/VictoryChancesGUI.cfg'
    return filename if os.path.exists(filename) else None

def removeAccents(value): 
    return u"".join([c for c in unicodedata.normalize('NFKD', unicode(value)) if not unicodedata.combining(c)])

def tankTypeAbb(tag):
    return 'MT' if 'mediumTank' == tag else 'HT' if 'heavyTank'== tag else 'AT' if 'AT-SPG' == tag else 'SPG' if 'SPG' == tag else 'LT'

def printStrings(value): 
    if LOG_FILENAME is not None and PRINT_LOG:
        with codecs.open(LOG_FILENAME, 'a', 'utf-8-sig') as file:
            if isinstance(value, list) or isinstance(value, tuple):
                file.writelines(value)
            else:
                file.write(value)

getPrintOneStat = lambda stat, full: '%s %s\t%4d HP\t%5.1f mm\t%5.2f sec\t%s\t%s dmg\t%s dpm\t%6.2f %s %s' % ('E' if stat['isEnemy'] else 'A', \
                                     tankTypeAbb(stat['type']['tag']), stat['hp'], stat['gun']['caliber'], stat['gun']['reload'], stat['gun']['currentShell'], \
                                     ('|'.join([' %s %6.1f ' % (sID, stat['gun']['shell'][sID]['damage']) for sID in stat['gun']['shell']])).ljust(20), \
                                     ('|'.join([' %s %6.1f ' % (sID, stat['gun']['shell'][sID]['dpm']) for sID in stat['gun']['shell']])).ljust(20), \
                                     stat['contribution'], '%', stat['name']) \
                                     if full else \
                                     '%s %s\t%4d HP\t%6.2f %s %s' % ('E' if stat['isEnemy'] else 'A', tankTypeAbb(stat['type']['tag']), stat['hp'], stat['contribution'], '%', stat['name'])

def printStat(stat, full=False, changeID=None):
    if LOG_FILENAME is not None and PRINT_LOG:
        with codecs.open(LOG_FILENAME, 'a', 'utf-8-sig') as file:
            if PRINT_ITEMS['TanksCount']:
                file.write('Count:   %6d <-> %6d\n'     % (stat.allyTanksCount, stat.enemyTanksCount))
            if PRINT_ITEMS['TeamHP']:
                file.write('HP:      %6d <-> %6d\n'     % (stat.allyTeamHP, stat.enemyTeamHP))
            if PRINT_ITEMS['TeamAvgDmg']:
                file.write('AvgDmg:  %6.1f <-> %6.1f\n' % (float(stat.allyTeamOneDamage)  / (stat.allyTanksCount if stat.allyTanksCount > 0 else 1), \
                                                          float(stat.enemyTeamOneDamage) / (stat.enemyTanksCount if stat.enemyTanksCount > 0 else 1)))
            if PRINT_ITEMS['TeamAvgDPM']:
                file.write('AvgDPM:  %6.1f <-> %6.1f\n' % (float(stat.allyTeamDPM)  / (stat.allyTanksCount if stat.allyTanksCount > 0 else 1), \
                                                          float(stat.enemyTeamDPM) / (stat.enemyTanksCount if stat.enemyTanksCount > 0 else 1)))
            if PRINT_ITEMS['TeamChances']:
                file.write('Chances: %6.2f <-> %6.2f\n' % (stat.allyChance, stat.enemyChance))
            file.write('\n')
            if PRINT_ITEMS['TanksList']:
                vIDSort = list(stat.base.keys())
                vIDSort.sort(lambda x,y: 1 if stat.base[y]['contribution'] > stat.base[x]['contribution'] else \
                                        -1 if stat.base[y]['contribution'] < stat.base[x]['contribution'] else 0)
                for vID in [vID for vID in vIDSort if stat.base[vID]['isAlive'] and not stat.base[vID]['isEnemy']]:
                    file.write(getPrintOneStat(stat.base[vID], full) + ('\t*\n' if vID == changeID else '\n'))
                file.write('\n')
                for vID in [vID for vID in vIDSort if stat.base[vID]['isAlive'] and stat.base[vID]['isEnemy']]:
                    file.write(getPrintOneStat(stat.base[vID], full) + ('\t*\n' if vID == changeID else '\n'))
                file.write('\n')

getShowOneStat = lambda stat: '%s  %4d HP %6.2f %s  %s\n' % ('E' if stat['isEnemy'] else 'A', stat['hp'], stat['contribution'], '%', removeAccents(stat['name']))

def showStat(stat, changeID=None):
    if SHOW_INFO and hasattr(g_appLoader.getDefBattleApp(), 'VictoryChancesGUI'):
        label = g_appLoader.getDefBattleApp().VictoryChancesGUI
        info  = ''
        if SHOW_ITEMS['TanksCount']:
            Ally, Enemy = stat.allyTanksCount, stat.enemyTanksCount 
            AllyText  = label.getHtmlTextWithTags('%6d' % Ally,  color=GUI_TEXT['CompareValuesColor'][2 if Ally == Enemy else 0 if Ally >  Enemy else 1])
            EnemyText = label.getHtmlTextWithTags('%6d' % Enemy, color=GUI_TEXT['CompareValuesColor'][2 if Ally == Enemy else 0 if Ally <= Enemy else 1])
            info += label.getSimpleTextWithTags('Count:   %s | %s\n') % (AllyText, EnemyText)
        if SHOW_ITEMS['TeamHP']:
            Ally, Enemy = stat.allyTeamHP, stat.enemyTeamHP 
            AllyText  = label.getHtmlTextWithTags('%6d' % Ally,  color=GUI_TEXT['CompareValuesColor'][2 if Ally == Enemy else 0 if Ally > Enemy else 1])
            EnemyText = label.getHtmlTextWithTags('%6d' % Enemy, color=GUI_TEXT['CompareValuesColor'][2 if Ally == Enemy else 0 if Ally < Enemy else 1])
            info += label.getSimpleTextWithTags('HP:      %s | %s\n') % (AllyText, EnemyText)
        if SHOW_ITEMS['TeamAvgDmg']:
            Ally, Enemy = float(stat.allyTeamOneDamage)  / (stat.allyTanksCount if stat.allyTanksCount > 0 else 1), \
                          float(stat.enemyTeamOneDamage) / (stat.enemyTanksCount if stat.enemyTanksCount > 0 else 1)
            AllyText  = label.getHtmlTextWithTags('%6.1f' % Ally,  color=GUI_TEXT['CompareValuesColor'][2 if Ally == Enemy else 0 if Ally > Enemy else 1])
            EnemyText = label.getHtmlTextWithTags('%6.1f' % Enemy, color=GUI_TEXT['CompareValuesColor'][2 if Ally == Enemy else 0 if Ally < Enemy else 1])
            info += label.getSimpleTextWithTags('AvgDmg:  %s | %s\n') % (AllyText, EnemyText)
        if SHOW_ITEMS['TeamAvgDPM']:
            Ally, Enemy = float(stat.allyTeamDPM)  / (stat.allyTanksCount if stat.allyTanksCount > 0 else 1), \
                          float(stat.enemyTeamDPM) / (stat.enemyTanksCount if stat.enemyTanksCount > 0 else 1)
            AllyText  = label.getHtmlTextWithTags('%6.1f' % Ally,  color=GUI_TEXT['CompareValuesColor'][2 if Ally == Enemy else 0 if Ally > Enemy else 1])
            EnemyText = label.getHtmlTextWithTags('%6.1f' % Enemy, color=GUI_TEXT['CompareValuesColor'][2 if Ally == Enemy else 0 if Ally < Enemy else 1])
            info += label.getSimpleTextWithTags('AvgDPM:  %s | %s\n') % (AllyText, EnemyText)
        if SHOW_ITEMS['TeamChances']:
            Ally, Enemy = stat.allyChance, stat.enemyChance
            AllyText  = label.getHtmlTextWithTags('%6.2f' % Ally,  color=GUI_TEXT['CompareValuesColor'][2 if Ally == Enemy else 0 if Ally > Enemy else 1])
            EnemyText = label.getHtmlTextWithTags('%6.2f' % Enemy, color=GUI_TEXT['CompareValuesColor'][2 if Ally == Enemy else 0 if Ally < Enemy else 1])
            info += label.getSimpleTextWithTags('Chances: %s | %s\n') % (AllyText, EnemyText)
        if SHOW_ITEMS['TanksList']:
            if info:
                info += '\n'
            vIDSort = list(stat.base.keys())
            vIDSort.sort(lambda x,y: 1 if stat.base[y]['contribution'] > stat.base[x]['contribution'] else \
                                    -1 if stat.base[y]['contribution'] < stat.base[x]['contribution'] else 0)
            for vID in [vID for vID in vIDSort if stat.base[vID]['isAlive'] and not stat.base[vID]['isEnemy']]:
                info += label.getHtmlTextWithTags(getShowOneStat(stat.base[vID]), color=GUI_TEXT['LastChangeColor'][0]) if vID == changeID else \
                        label.getSimpleTextWithTags(getShowOneStat(stat.base[vID]))
            info += '\n'
            for vID in [vID for vID in vIDSort if stat.base[vID]['isAlive'] and stat.base[vID]['isEnemy']]:
                info += label.getHtmlTextWithTags(getShowOneStat(stat.base[vID]), color=GUI_TEXT['LastChangeColor'][1]) if vID == changeID else \
                        label.getSimpleTextWithTags(getShowOneStat(stat.base[vID]))
        label.HtmlText(info)

# Hooks ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

def onVehiclesChanged(statistic, reasone, vID):
    showStat(statistic, vID if reasone != UPDATE_REASONE.VEHICLE_ADDED else None)
    if reasone != UPDATE_REASONE.VEHICLE_ADDED:
        if reasone == UPDATE_REASONE.VEHICLE_DEATH:
            printStrings(('------------------------- %s -------------------------\n' % datetime.now().strftime('%d.%m.%y %H:%M:%S'), '\nReason: VehicleDeath\n\n'))
        elif reasone == UPDATE_REASONE.HEALTH_CHANGED:
            printStrings(('------------------------- %s -------------------------\n' % datetime.now().strftime('%d.%m.%y %H:%M:%S'), '\nReason: HealthChanged\n\n'))
        printStat(statistic, False, vID)

def onBattleLoaded(statistic):
    global CONFIG_FILENAME, LOG_FILENAME, SHOW_INFO, SHOW_ITEMS, KEYS_SHOWHIDEALL, KEYS_TANKSLIST, \
           PRINT_LOG, PRINT_ITEMS, GUI_TEXT, NEW_BATTLE
    CONFIG_FILENAME = getConfigFileName()
    if CONFIG_FILENAME is not None:
        #Config ------------------------------------------
        config     = json.loads(re.compile('(/\*(.|\n)*?\*/)|((#|//).*?$)', re.I | re.M).sub('', codecs.open(CONFIG_FILENAME, 'r', 'utf-8-sig').read()))
        SHOW_INFO  = config['System']['TeamChances']['GUIStatistics']['Show']
        SHOW_ITEMS = config['System']['TeamChances']['GUIStatistics']['ShowItems']
        KEYS_SHOWHIDEALL  = config['System']['TeamChances']['Hotkeys']['ShowHideAll']
        KEYS_SHOWHIDEALL['Key'] = getattr(Keys, KEYS_SHOWHIDEALL['Key'])
        KEYS_TANKSLIST    = config['System']['TeamChances']['Hotkeys']['TanksList']
        KEYS_TANKSLIST['Key'] = getattr(Keys, KEYS_TANKSLIST['Key'])
        GUI_TEXT['Name']   = config['System']['TeamChances']['GUIFormat']['Font']['Name']
        GUI_TEXT['Size']   = config['System']['TeamChances']['GUIFormat']['Font']['Size']
        GUI_TEXT['Color']  = config['System']['TeamChances']['GUIFormat']['Font']['Color'].replace('$','#')
        GUI_TEXT['Bold']   = config['System']['TeamChances']['GUIFormat']['Font']['Bold']
        GUI_TEXT['Alpha']  = config['System']['TeamChances']['GUIFormat']['Font']['Alpha']
        GUI_TEXT['Shadow'] = config['System']['TeamChances']['GUIFormat']['Font']['Shadow']
        GUI_TEXT['Pos']    = (config['System']['TeamChances']['GUIFormat']['Position'][0],
                              config['System']['TeamChances']['GUIFormat']['Position'][1])
        GUI_TEXT['LastChangeColor'] = (config['System']['TeamChances']['GUIFormat']['LastChangeColor']['AllyTeam'].replace('$','#'), 
                                       config['System']['TeamChances']['GUIFormat']['LastChangeColor']['EnemyTeam'].replace('$','#'))
        GUI_TEXT['CompareValuesColor'] = (config['System']['TeamChances']['GUIFormat']['CompareValuesColor']['BestValue'].replace('$','#'), 
                                          config['System']['TeamChances']['GUIFormat']['CompareValuesColor']['WorstValue'].replace('$','#'),
                                          config['System']['TeamChances']['GUIFormat']['Font']['Color'].replace('$','#'))
        PRINT_LOG    = config['System']['TeamChances']['PrintLog']
        PRINT_ITEMS  = config['System']['TeamChances']['LogFormat']['PrintItems']
        LOG_FILENAME = getLogFileName(config['System']['TeamChances']['LogFormat']['Dir'], config['System']['TeamChances']['LogFormat']['Prefix'])
        #Flash -------------------------------------------
        g_appLoader.getDefBattleApp().VictoryChancesGUI = VictoryChancesGUI = FlashTextLabel(GUI_TEXT)
        VictoryChancesGUI.Visible(KEYS_SHOWHIDEALL['ShowDefault'])
        #Keys --------------------------------------------
        if SHOW_INFO:
            InputHandler.g_instance.onKeyDown += onKeyDown
        if SHOW_ITEMS['TanksList'] and KEYS_TANKSLIST['ShowKeyDownOnly']:
            SHOW_ITEMS['TanksList'] = False
            InputHandler.g_instance.onKeyDown += onShowHideTanksList
            InputHandler.g_instance.onKeyUp   += onShowHideTanksList
        #Statistic ---------------------------------------
        g_StatisticEvents.OnVehiclesChanged += onVehiclesChanged
        showStat(statistic)
        printStrings(('------------------------- %s -------------------------\n' % datetime.now().strftime('%d.%m.%y %H:%M:%S'), '\nReason: BattleLoading\n\n')) 
        printStat(statistic, True)

def onKeyDown(event):
    global KEYS_SHOWHIDEALL
    if event.isKeyDown() and BigWorld.isKeyDown(KEYS_SHOWHIDEALL['Key']):
        KEYS_SHOWHIDEALL['ShowDefault'] = not KEYS_SHOWHIDEALL['ShowDefault']
    if hasattr(g_appLoader.getDefBattleApp(), 'VictoryChancesGUI'):
        g_appLoader.getDefBattleApp().VictoryChancesGUI.Visible(KEYS_SHOWHIDEALL['ShowDefault'])
    if CONFIG_FILENAME:
        s = re.sub('"ShowDefault"\s*:\s*(true|false)', '"ShowDefault": ' + str(KEYS_SHOWHIDEALL['ShowDefault']).lower(), codecs.open(CONFIG_FILENAME, 'r', 'utf-8-sig').read())
        with codecs.open(CONFIG_FILENAME, 'w', 'utf-8-sig') as f:
            f.write(s)

def onShowHideTanksList(event):
    global SHOW_ITEMS
    if (event.isKeyDown() and BigWorld.isKeyDown(KEYS_TANKSLIST['Key']) and not SHOW_ITEMS['TanksList']) or \
       (event.isKeyUp() and not BigWorld.isKeyDown(KEYS_TANKSLIST['Key']) and SHOW_ITEMS['TanksList']):
        SHOW_ITEMS['TanksList'] = not SHOW_ITEMS['TanksList']
        showStat(g_TanksStatistic)

def new__destroyGUI(self):
    InputHandler.g_instance.onKeyDown -= onKeyDown
    InputHandler.g_instance.onKeyDown -= onShowHideTanksList
    InputHandler.g_instance.onKeyUp   -= onShowHideTanksList
    old__destroyGUI(self)

def new_onBecomeNonPlayer(self):
    try:
        g_StatisticEvents.OnVehiclesChanged -= onVehiclesChanged
    finally:
        old_onBecomeNonPlayer(self)

try:
    from gui.mods.gambiter import g_guiFlash
    from gui.mods.gambiter.flash import COMPONENT_TYPE, COMPONENT_EVENT
except:
    print '[%s] Loading mod: Not found "gambiter.guiflash" module, loading stoped!' % __author__
else:
    try:
        from gui.mods.VictoryChances import g_StatisticEvents, g_TanksStatistic, UPDATE_REASONE
    except:
        print '[%s] Loading mod: Not found "VictoryChances" module, loading stoped!' % __author__
    else:
        g_StatisticEvents.OnBattleLoaded  += onBattleLoaded
    
        old__destroyGUI = PlayerAvatar._PlayerAvatar__destroyGUI
        PlayerAvatar._PlayerAvatar__destroyGUI = new__destroyGUI
    
        old_onBecomeNonPlayer = PlayerAvatar.onBecomeNonPlayer
        PlayerAvatar.onBecomeNonPlayer = new_onBecomeNonPlayer
    
        print '[%s] Loading mod: VictoryChancesGUI %s (http://www.koreanrandom.com)' % (__author__, __version__)
