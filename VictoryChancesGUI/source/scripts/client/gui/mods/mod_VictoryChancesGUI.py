# -*- coding: utf-8 -*-

__author__  = 'StranikS_Scan'
__version__ = 'V2.0 P2.7 W0.9.21 16.01.2018'

import GUI, Event, BattleReplay
from gui.Scaleform.framework.entities.BaseDAAPIComponent import BaseDAAPIComponent
from gui.Scaleform.framework.entities.View import View
from gui.Scaleform.framework.managers.loaders import ViewLoadParams
from gui.Scaleform.framework import g_entitiesFactories, ViewSettings, ViewTypes, ScopeTemplates
from gui.shared import g_eventBus, events, EVENT_BUS_SCOPE
from gui.Scaleform.genConsts.BATTLE_VIEW_ALIASES import BATTLE_VIEW_ALIASES
from gui.app_loader import g_appLoader
from gui import g_guiResetters

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
             'LastChangeColor': ('#FC2847','#28FC47'),
             'CompareValuesColor': ('#28FC47','#FC2847'),
             'ToolTip': 'VictoryChancesGUI Panel'}

# Text Flash ===========================================================

class BattleFlashMeta(BaseDAAPIComponent):    
    
    def py_printLog(self, text):
        """
        :param text : String:
        :return :
        """
        self._printOverrideError('py_printLog')
    
    def py_updatePosition(self, container, x, y):
        """
        :param container : String:
        :param x : Number:
        :param y : Number:
        :return :
        """
        self._printOverrideError('py_updatePosition')
            
    def as_setTextS(self, container, element, value):
        """
        :param container : String:
        :param element : String:
        :param value:
            text : String:
        :return :
        """
        if self._isDAAPIInited():
            return self.flashObject.as_setText(container, element, value)
    
    def as_setImageS(self, container, element, value):
        """
        :param container : String:
        :param element : String:
        :param value:
            image : String:
        :return :
        """
        if self._isDAAPIInited():
            return self.flashObject.as_setImage(container, element, value)
            
    def as_setVisibleS(self, container, element, value):
        """
        :param container : String:
        :param element : String:
        :param value:
            visible : Boolean:
        :return :
        """
        if self._isDAAPIInited():
            return self.flashObject.as_setVisible(container, element, value)
            
    def as_setPositionS(self, container, element, value):
        """
        :param container : String:
        :param element : String:
        :param value:
            x : Number:
            y : Number:
        :return :
        """
        if self._isDAAPIInited():
            return self.flashObject.as_setPosition(container, element, value)
            
    def as_setAlphaS(self, container, element, value):
        """
        :param container : String:
        :param element : String:
        :param value:
            alpha : Number:
        :return :
        """
        if self._isDAAPIInited():
            return self.flashObject.as_setAlpha(container, element, value)
            
    def as_setRotationS(self, container, element, value):
        """
        :param container : String:
        :param element : String:
        :param value:
            rotation : Number:
        :return :
        """
        if self._isDAAPIInited():
            return self.flashObject.as_setRotation(container, element, value)
            
    def as_setSizeS(self, container, element, value):
        """
        :param container : String:
        :param element : String:
        :param value:
            width : Number:
            height : Number:
        :return :
        """
        if self._isDAAPIInited():
            return self.flashObject.as_setSize(container, element, value)
            
    def as_setShadowS(self, container, element, value):
        """
        :param container : String:
        :param element : String:
        :param value:
            distance : Number:
            angle : Number:
            color : String:
            alpha : Number:
            size : Number:
            strength : Number:
        :return :
        """
        if self._isDAAPIInited():
            return self.flashObject.as_setShadow(container, element, value)
            
    def as_setToolTipS(self, container, element, value):
        """
        :param container : String:
        :param element : String:
        :param value:
            tooltip : String:
        :return :
        """
        if self._isDAAPIInited():
            return self.flashObject.as_setToolTip(container, element, value)
    
    def as_screenS(self, width, height):
        """
        :param width : Number:
        :param height : Number:
        :return :
        """
        if self._isDAAPIInited():
            return self.flashObject.as_screen(width, height)

    def as_cursorS(self, show):
        """
        :param show : Boolean:
        :return :
        """
        if self._isDAAPIInited():
            return self.flashObject.as_cursor(show)
    
    def as_visibleS(self, show):
        """
        :param show : Boolean:
        :return :
        """
        if self._isDAAPIInited():
            return self.flashObject.as_visible(show)

class BattleFlash(BattleFlashMeta):

    def __init__(self):
        super(BattleFlash, self).__init__()
        self._toggleVisible = {'fullStats': False, 'radialMenu': False}

    def __del__(self):
        pass

    def _populate(self):
        super(BattleFlash, self)._populate()
        g_battleFlash.isLoadedFlash(self.flashObject.name, self)
        g_eventBus.addListener(events.GameEvent.RADIAL_MENU_CMD, self._toggleRadialMenu, scope=EVENT_BUS_SCOPE.BATTLE)
        g_eventBus.addListener(events.GameEvent.FULL_STATS, self._toggleFullStats, scope=EVENT_BUS_SCOPE.BATTLE)
        g_eventBus.addListener(events.GameEvent.SHOW_CURSOR, self._showCursor, EVENT_BUS_SCOPE.GLOBAL)
        g_eventBus.addListener(events.GameEvent.HIDE_CURSOR, self._hideCursor, EVENT_BUS_SCOPE.GLOBAL)
        g_guiResetters.add(self._resizeScreen)        
        self._resizeScreen()

    def _dispose(self):
        g_battleFlash.isDestroyedFlash(self.flashObject.name)
        g_eventBus.removeListener(events.GameEvent.RADIAL_MENU_CMD, self._toggleRadialMenu, scope=EVENT_BUS_SCOPE.BATTLE)
        g_eventBus.removeListener(events.GameEvent.FULL_STATS, self._toggleFullStats, scope=EVENT_BUS_SCOPE.BATTLE)
        g_eventBus.removeListener(events.GameEvent.SHOW_CURSOR, self._showCursor, EVENT_BUS_SCOPE.BATTLE)
        g_eventBus.removeListener(events.GameEvent.HIDE_CURSOR, self._hideCursor, EVENT_BUS_SCOPE.BATTLE)
        g_guiResetters.discard(self._resizeScreen)
        super(BattleFlash, self)._dispose()

    def _resizeScreen(self):
        screenWidth, screenHeight = GUI.screenResolution()
        self.as_screenS(screenWidth, screenHeight)
    
    def _toggleRadialMenu(self, event):
        if BattleReplay.isPlaying(): return
        self._toggleVisible['radialMenu'] = event.ctx['isDown']
        self._flashVisible()
    
    def _toggleFullStats(self, event):
        self._toggleVisible['fullStats'] = event.ctx['isDown']
        self._flashVisible()
    
    def _flashVisible(self):
        isVisible = not self._toggleVisible['fullStats'] and not self._toggleVisible['radialMenu']
        self.as_visibleS(isVisible)
    
    def _showCursor(self, _):
        self.as_cursorS(True)

    def _hideCursor(self, _):
        self.as_cursorS(False)
        
    def py_updatePosition(self, container, x, y):
        g_battleFlash.OnUpdatePosition(self.flashObject.name, container, x, y)
        
    def py_printLog(self, text):
        print 'BattleFlash [ %s ] %s' % (str(self.flashObject.name), str(text))

class BattleFlashInjector(View):

    def __init__(self):
        super(BattleFlashInjector, self).__init__()

    def __del__(self):
        super(BattleFlashInjector, self).__del__()

    def _populate(self):
        super(BattleFlashInjector, self)._populate()
        id = self.getID()
        idx = self.getIndex(id)
        self.as_battleInjectS(id, idx)
        #self.destroy()
        
    def _dispose(self):
        super(BattleFlashInjector, self)._dispose()

    def getID(self):
        return self.getUniqueName().replace(g_battleFlash.Injector, '')
    
    def getIndex(self, id):
        return g_battleFlash.flashIDs.get(id)

    def py_printLog(self, text):
        print 'BattleFlash_Injector [ %s ] %s' % (str(self.getUniqueName()), str(text))

    def as_battleInjectS(self, id, idx):
        if self._isDAAPIInited():
            return self.flashObject.as_battleInject(id, idx)

class _BattleFlash(object):

    title = 'battleFlash'
    version = '1.1.4'
    path = '0.9.15.1'
    date = '30.08.2016'

    def __init__(self):        
        g_eventBus.addListener(events.ComponentEvent.COMPONENT_REGISTERED, self.__onComponentRegistered, EVENT_BUS_SCOPE.GLOBAL)
        self.isLoadedFlash = Event.Event()
        self.isDestroyedFlash = Event.Event()
        self.OnUpdatePosition = Event.Event()
        self.Injector = '_Injector'
        self.flashIDs = {}

    def __del__(self):
        g_eventBus.removeListener(events.ComponentEvent.COMPONENT_REGISTERED, self.__onComponentRegistered, EVENT_BUS_SCOPE.GLOBAL)
        self.isLoadedFlash.clear()
        self.isDestroyedFlash.clear()
        self.OnUpdatePosition.clear()
        del self.Injector
        del self.flashIDs       

    def load(self, id, swf, idx = None):
        if id not in self.flashIDs:
            self.flashIDs[id] = idx           
            g_entitiesFactories.addSettings(ViewSettings(id + self.Injector, BattleFlashInjector, swf, ViewTypes.WINDOW, None, ScopeTemplates.GLOBAL_SCOPE))
            g_entitiesFactories.addSettings(ViewSettings(id, BattleFlash, None, ViewTypes.COMPONENT, None, ScopeTemplates.DEFAULT_SCOPE))

    def unload(self, id):
        if id in self.flashIDs:
            del self.flashIDs[id]
            g_entitiesFactories.removeSettings(id + self.Injector)
            g_entitiesFactories.removeSettings(id)

    def __onComponentRegistered(self, event):
        if event.alias == BATTLE_VIEW_ALIASES.DAMAGE_PANEL:
            if g_appLoader.getDefBattleApp():
                if self.flashIDs:
                    for id in self.flashIDs:
                        g_appLoader.getDefBattleApp().loadView(ViewLoadParams(id + self.Injector, None))

g_battleFlash = _BattleFlash()

class FlashTextLabels(object):
    def __init__(self):
        self.id = 'VictoryChancesGUI_Flash'
        self.ui = None
        self.OnLoadedFlash = Event.Event()
        self.OnUpdatePosition = Event.Event()
        g_battleFlash.load(self.id, 'mod_battleflash.swf', FLASH_Z)
        g_battleFlash.isLoadedFlash += self.load
        g_battleFlash.OnUpdatePosition += self.update
        g_battleFlash.isDestroyedFlash += self.destroy

    def __del__(self):
        g_battleFlash.isLoadedFlash -= self.load
        g_battleFlash.OnUpdatePosition -= self.update
        g_battleFlash.isDestroyedFlash -= self.destroy
        self.OnLoadedFlash.clear()
        self.OnUpdatePosition.clear()

    def load(self, id, ui):
        if id == self.id:
            self.ui = ui
            self.OnLoadedFlash()

    def update(self, id, container, x, y):
        if id == self.id:
            g_flashTextLabels.OnUpdatePosition(container, x, y)

    def destroy(self, id):
        if id == self.id:
            self.ui = None

FLASH_Z = 2.461824
g_flashTextLabels = FlashTextLabels()

class FlashTextLabel(object):
    def __init__(self, params):
        self.text = ''
        self.visible = True
        self.container = params['Name']
        self.label = 'TextLabel'
        self.ui = g_flashTextLabels.ui
        self.ui.as_setTextS(self.container, self.label, [self.text])
        self.x, self.y = params['Pos'] if 'Pos' in params else (0,0)
        screenWidth, screenHeight = GUI.screenResolution()
        self.ui.as_setPositionS(self.container, self.label, [screenWidth // 2 + self.x, screenHeight // 2 + self.y])
#       self.ui.as_setShadowS(self.container, self.label, [0, 135, '#101010', 100, 2, 80]) #distance, angle, color, alpha, size, strength
        if 'Alpha' in params:
            self.ui.as_setAlphaS(self.container, self.label, [min(max(params['Alpha'] * 100, 0), 100)])
        if 'ToolTip' in params:
            self.ui.as_setToolTipS(self.container, '', [params['ToolTip']])
        self.ui.as_setVisibleS(self.container, '', [self.visible])
        self.font = params['Font'] if 'Font' in params else 'Arial'
        self.size = params['Size'] if 'Size' in params else 16
        self.bold = params['Bold'] if 'Bold' in params else False
        self.italic = params['Italic'] if 'Italic' in params else False
        self.color = params['Color'] if 'Color' in params else '#FFFFFF'
        #---
        self.begin = '<font face="%s" size="%d" color="%s">%s%s' % (self.font, self.size, self.color, '<b>' if self.bold else '', '<i>' if self.italic else '')
        self.end   = '%s%s</font>' % ('</b>' if self.bold else '', '</i>' if self.italic else '')
        #---
        self.config = params['Config'] if 'Config' in params else None
        self.section = params['Section'] if 'Section' in params else None
        self.key = params['Key'] if 'Key' in params else None
        if self.config and self.section and self.key:
            g_flashTextLabels.OnUpdatePosition += self.updatePosition

    def __del__(self):
        if self.config and self.section and self.key:
            g_flashTextLabels.OnUpdatePosition -= self.updatePosition
        self.ui = None

    def setPosition(self, pos):
        self.x, self.y = pos
        screenWidth, screenHeight = GUI.screenResolution()
        self.ui.as_setPositionS(self.container, self.label, [screenWidth // 2 + self.x, screenHeight // 2 + self.y])

    def updatePosition(self, container, x, y):
        if container == self.container:
            if x > 0 or y > 0:
                self.x += x
                self.y += y
                if not BigWorld.new_ConfigLoader.configWritePositionValue(self.config, self.section, self.key, (self.x, self.y)):
                    g_flashTextLabels.OnUpdatePosition -= self.updatePosition

    def getSimpleTextWithTags(self, text):
        return self.begin + text + self.end if text and self.visible else ''

    def getHtmlTextWithTags(self, text, font=None, size=None, color=None, bold=None, italic=None):
        return '<font face="%s" size="%d" color="%s">%s%s%s%s%s</font>' % (font if font else self.font, size if size else self.size,
               color if color else self.color, '<b>' if bold or self.bold else '', '<i>' if italic or self.italic else '', text, \
               '</b>' if bold or self.bold else '', '</i>' if italic or self.italic else '') if text and self.visible else ''

    def getHtmlTextWithTagsOnly(self, text, font=None, size=None, color=None, bold=None, italic=None):
        if font or size or color:
            return '<font %s %s %s>%s%s%s%s%s</font>' % ('face="%s"' % font if font else '', 'size="%d"' % size if size else '',
                   'color="%s"' % color if color else '', '<b>' if bold else '', '<i>' if italic else '', text, \
                   '</b>' if bold else '', '</i>' if italic else '') if text and self.visible else ''
        else:
            return '%s%s%s%s%s' % ('<b>' if bold else '', '<i>' if italic else '', text, '</b>' if bold else '', '</i>' if italic else '') if text and self.visible else ''

    def SimpleText(self, text):
        if self.visible:
            self.text = text
            self.ui.as_setTextS(self.container, self.label, [self.begin + self.text + self.end if self.text else self.text])

    def HtmlText(self, text):
        if self.visible:
            self.text = text
            self.ui.as_setTextS(self.container, self.label, [self.text])

    def Visible(self, value):
        self.visible = value
        self.ui.as_setVisibleS(self.container, '', [self.visible])

# Classes and functions ===========================================================

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
    filename = getRoot() + 'VictoryChancesGUI.cfg'
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

def onLoadedFlash(): 
    g_appLoader.getDefBattleApp().VictoryChancesGUI = FlashTextLabel(GUI_TEXT)

def onVehiclesChanged(statistic, reasone, vID):
    showStat(statistic, vID if reasone != UPDATE_REASONE.VEHICLE_ADDED else None)
    if reasone != UPDATE_REASONE.VEHICLE_ADDED:
        if reasone == UPDATE_REASONE.VEHICLE_DEATH:
            printStrings(('------------------------- %s -------------------------\n' % datetime.now().strftime('%d.%m.%y %H:%M:%S'), '\nReason: VehicleDeath\n\n'))
        elif reasone == UPDATE_REASONE.HEALTH_CHANGED:
            printStrings(('------------------------- %s -------------------------\n' % datetime.now().strftime('%d.%m.%y %H:%M:%S'), '\nReason: HealthChanged\n\n'))
        printStat(statistic, False, vID)

def onBattleLoaded(statistic):
    global CONFIG_FILENAME, LOG_FILENAME, SHOW_INFO, SHOW_ITEMS, PRINT_LOG, PRINT_ITEMS, GUI_TEXT, NEW_BATTLE
    CONFIG_FILENAME = getConfigFileName()
    if CONFIG_FILENAME is not None:
        #Config ------------------------------------------
        config     = json.loads(re.compile('(/\*(.|\n)*?\*/)|((#|//).*?$)', re.I | re.M).sub('', codecs.open(CONFIG_FILENAME, 'r', 'utf-8-sig').read()))
        SHOW_INFO  = config['System']['TeamChances']['GUIStatistics']['Show']
        SHOW_ITEMS = config['System']['TeamChances']['GUIStatistics']['ShowItems']
        GUI_TEXT['Name']  = config['System']['TeamChances']['GUIFormat']['Font']['Name']
        GUI_TEXT['Size']  = config['System']['TeamChances']['GUIFormat']['Font']['Size']
        GUI_TEXT['Color'] = config['System']['TeamChances']['GUIFormat']['Font']['Color'].replace('$','#')
        GUI_TEXT['Bold']  = config['System']['TeamChances']['GUIFormat']['Font']['Bold']
        GUI_TEXT['Pos']   = (config['System']['TeamChances']['GUIFormat']['Position'][0],
                             config['System']['TeamChances']['GUIFormat']['Position'][1])
        GUI_TEXT['LastChangeColor'] = (config['System']['TeamChances']['GUIFormat']['LastChangeColor']['AllyTeam'].replace('$','#'), 
                                       config['System']['TeamChances']['GUIFormat']['LastChangeColor']['EnemyTeam'].replace('$','#'))
        GUI_TEXT['CompareValuesColor'] = (config['System']['TeamChances']['GUIFormat']['CompareValuesColor']['BestValue'].replace('$','#'), 
                                          config['System']['TeamChances']['GUIFormat']['CompareValuesColor']['WorstValue'].replace('$','#'),
                                          config['System']['TeamChances']['GUIFormat']['Font']['Color'].replace('$','#'))
        PRINT_LOG    = config['System']['TeamChances']['PrintLog']
        PRINT_ITEMS  = config['System']['TeamChances']['LogFormat']['PrintItems']
        LOG_FILENAME = getLogFileName(config['System']['TeamChances']['LogFormat']['Dir'], config['System']['TeamChances']['LogFormat']['Prefix'])
        #Statistic ---------------------------------------
        g_StatisticEvents.OnVehiclesChanged += onVehiclesChanged
        showStat(statistic)
        printStrings(('------------------------- %s -------------------------\n' % datetime.now().strftime('%d.%m.%y %H:%M:%S'), '\nReason: BattleLoading\n\n')) 
        printStat(statistic, True)

def new_onBecomeNonPlayer(self):
    try:
        g_StatisticEvents.OnVehiclesChanged -= onVehiclesChanged
    finally:
        old_onBecomeNonPlayer(self)

try:
    from gui.mods.VictoryChances import g_StatisticEvents, UPDATE_REASONE
except:
    print '[%s] Loading mod: Not found "VictoryChances" module, loading stoped!' % __author__
else:
    g_flashTextLabels.OnLoadedFlash  += onLoadedFlash
    g_StatisticEvents.OnBattleLoaded += onBattleLoaded

    old_onBecomeNonPlayer = PlayerAvatar.onBecomeNonPlayer
    PlayerAvatar.onBecomeNonPlayer = new_onBecomeNonPlayer

    print '[%s] Loading mod: VictoryChancesGUI %s (http://www.koreanrandom.com)' % (__author__, __version__)
