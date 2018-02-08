# -*- coding: utf-8 -*-

__author__  = 'StranikS_Scan'
__version__ = 'V1.7 P2.7 W0.9.16 22.10.2016'

print '[%s] Loading mod: Chances %s (http://www.koreanrandom.com/forum/topic/27695-/#2)' % (__author__, __version__)

import BigWorld, GUI, Event, BattleReplay
from gui.Scaleform.framework.entities.BaseDAAPIComponent import BaseDAAPIComponent
from gui.Scaleform.framework.entities.View import View
from gui.Scaleform.framework import g_entitiesFactories, ViewSettings, ViewTypes, ScopeTemplates
from gui.shared import g_eventBus, events, EVENT_BUS_SCOPE
from gui.Scaleform.genConsts.BATTLE_VIEW_ALIASES import BATTLE_VIEW_ALIASES
from gui import g_guiResetters
from gui.app_loader import g_appLoader
from Avatar import PlayerAvatar
from Vehicle import Vehicle

import re
from datetime import datetime
import ResMgr, os, codecs, json
import unicodedata

# Consts ..........................................................................

CONFIG_FILENAME = None
LOG_FILENAME    = None

SHOW_INFO  = True
SHOW_ITEMS = {}
PRINT_LOG  = True
PRINT_ITEMS = {}

GUI_TEXT  = {'Name': 'Chances_Chances',
             'Font': 'Lucida Console',
             'Bold': True,
             'Size': 16,
             'Color': '#00EDFF',
             'Pos': (400, -400),
             'Alpha': 0.95,
             'LastChangeColor': ('#FC2847','#28FC47'),
             'CompareValuesColor': ('#28FC47','#FC2847'),
             'ToolTip': 'Chances Panel'}
GLOBAL_STATISTICS = {}
TANKS_STATISTICS  = {}

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
        g_battleFlash.onUpdatePosition(self.flashObject.name, container, x, y)
        
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
        self.destroy()
        
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
        self.onUpdatePosition = Event.Event()
        self.Injector = '_Injector'
        self.flashIDs = {}

    def __del__(self):
        g_eventBus.removeListener(events.ComponentEvent.COMPONENT_REGISTERED, self.__onComponentRegistered, EVENT_BUS_SCOPE.GLOBAL)
        self.isLoadedFlash.clear()
        self.isDestroyedFlash.clear()
        self.onUpdatePosition.clear()
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
                        g_appLoader.getDefBattleApp().loadView(id + self.Injector)

g_battleFlash = _BattleFlash()

class FlashTextLabels(object):
    def __init__(self):
        self.id = 'Chances_Flash'
        self.ui = None
        self.onLoadedFlash = Event.Event()
        self.onUpdatePosition = Event.Event()
        g_battleFlash.load(self.id, 'mod_battleflash.swf', FLASH_Z)
        g_battleFlash.isLoadedFlash += self.load
        g_battleFlash.onUpdatePosition += self.update
        g_battleFlash.isDestroyedFlash += self.destroy

    def __del__(self):
        g_battleFlash.isLoadedFlash -= self.load
        g_battleFlash.onUpdatePosition -= self.update
        g_battleFlash.isDestroyedFlash -= self.destroy
        self.onLoadedFlash.clear()
        self.onUpdatePosition.clear()

    def load(self, id, ui):
        if id == self.id:
            self.ui = ui
            self.onLoadedFlash()

    def update(self, id, container, x, y):
        if id == self.id:
            g_flashTextLabels.onUpdatePosition(container, x, y)

    def destroy(self, id):
        if id == self.id:
            self.ui = None

FLASH_Z = 2.471824
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
            g_flashTextLabels.onUpdatePosition += self.updatePosition

    def __del__(self):
        if self.config and self.section and self.key:
            g_flashTextLabels.onUpdatePosition -= self.updatePosition
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
    filename = getRoot() + 'Chances.cfg'
    return filename if os.path.exists(filename) else None

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

def getAllyTanksCount(withDead=True):
    count = 0
    for value in TANKS_STATISTICS.itervalues():
        if not value['isEnemy'] and (withDead or value['isAlive']):
            count += 1
    return count

def getEnemyTanksCount(withDead=True):
    count = 0
    for value in TANKS_STATISTICS.itervalues():
        if value['isEnemy'] and (withDead or value['isAlive']):
            count += 1
    return count

def getAllyTanksHP(withDead=False):
    hp = 0
    for value in TANKS_STATISTICS.itervalues():
        if not value['isEnemy'] and (withDead or value['isAlive']):
            hp += value['hp']
    return hp    

def getEnemyTanksHP(withDead=False):
    hp = 0
    for value in TANKS_STATISTICS.itervalues():
        if value['isEnemy'] and (withDead or value['isAlive']):
            hp += value['hp']
    return hp

#def getAllyTanksBW(withDead=False):
#   bw = 0
#   for value in TANKS_STATISTICS.itervalues():
#       if not value['isEnemy'] and (withDead or value['isAlive']):
#            bw += value['balanceWeight']
#   return bw
#
#def getEnemyTanksBW(withDead=False):
#   bw = 0
#   for value in TANKS_STATISTICS.itervalues():
#       if value['isEnemy'] and (withDead orvalue['isAlive']):
#            bw += value['balanceWeight']
#   return bw

def getAllyTanksOneDamage(withDead=False):
    odmg = 0
    for value in TANKS_STATISTICS.itervalues():
        if not value['isEnemy']:
            if withDead or value['isAlive']:
                odmg += value['gun']['mainDamage']
    return odmg

def getEnemyTanksOneDamage(withDead=False):
    odmg = 0
    for value in TANKS_STATISTICS.itervalues():
        if value['isEnemy'] and (withDead or value['isAlive']):
            odmg += value['gun']['mainDamage']
    return odmg

def getAllyTanksMainDPM(withDead=False):
    dpm = 0
    for value in TANKS_STATISTICS.itervalues():
        if not value['isEnemy'] and (withDead or value['isAlive']):
            dpm += value['gun']['mainDpm']
    return dpm

def getEnemyTanksMainDPM(withDead=False):
    dpm = 0
    for value in TANKS_STATISTICS.itervalues():
        if value['isEnemy'] and (withDead or value['isAlive']):
                dpm += value['gun']['mainDpm']
    return dpm

def getAllyTanksForces(withDead=False):
    forces = 0
    for value in TANKS_STATISTICS.itervalues():
        if not value['isEnemy'] and (withDead or value['isAlive']):
            forces += value['force']
    return forces

def getEnemyTanksForces(withDead=False):
    forces = 0
    for value in TANKS_STATISTICS.itervalues():
        if value['isEnemy'] and (withDead or value['isAlive']):
            forces += value['force']
    return forces

def calcGlobalStatistics():
    global GLOBAL_STATISTICS, TANKS_STATISTICS
    allyTanksHP  = getAllyTanksHP()
    enemyTanksHP = getEnemyTanksHP()    
    for value in TANKS_STATISTICS.itervalues():
        if value['isAlive']: 
            try:
                value['force'] = value['hp'] * value['gun']['mainDpm'] / (allyTanksHP if value['isEnemy'] else enemyTanksHP)
            except:
                value['force'] = 999999.9
        else:
            value['force'] = 0
    allyTanksForces  = getAllyTanksForces()
    enemyTanksForces = getEnemyTanksForces()
    GLOBAL_STATISTICS['allyChance']  = 100 * allyTanksForces  / (allyTanksForces + enemyTanksForces)
    GLOBAL_STATISTICS['enemyChance'] = 100 * enemyTanksForces / (allyTanksForces + enemyTanksForces)

def printStrings(value): 
    if LOG_FILENAME is not None and PRINT_LOG:
        with codecs.open(LOG_FILENAME, 'a', 'utf-8-sig') as file:
            if isinstance(value, list) or isinstance(value, tuple):
                file.writelines(value)
            else:
                file.write(value)

def printInfo(full=False):
    def getStat(stat, full):
        if full:
            return '%s\t%s\t%6.2f HP\t%5.1f mm\t%5.2f sec\t%s\t%s dmg\t%s dpm\t%6.1f FR\t%s\n' % ('E' if stat['isEnemy'] else 'A', \
                   stat['type']['name'], stat['hp'], stat['gun']['caliber'], stat['gun']['reload'], stat['gun']['shell'][stat['gun']['mainShell']]['typeName'], \
                   ('|'.join(['%s-%6.1f' % (stat['gun']['shell'][sID]['typeName'], stat['gun']['shell'][sID]['damage']) for sID in stat['gun']['shell']])).ljust(20), \
                   ('|'.join(['%s-%6.1f' % (stat['gun']['shell'][sID]['typeName'], stat['gun']['shell'][sID]['dpm']) for sID in stat['gun']['shell']])).ljust(20), \
                   stat['force'], stat['name'])
        else:
            return '%s\t%s\t%4d HP\t%6.1f FR\t%s\n' % ('E' if stat['isEnemy'] else 'A', stat['type']['name'], stat['hp'], stat['force'], stat['name'])

    if LOG_FILENAME is not None and PRINT_LOG:
        with codecs.open(LOG_FILENAME, 'a', 'utf-8-sig') as file:
            if PRINT_ITEMS['TanksCount']:
                file.write('Tanks Count:   %d\t<->\t%d\n'         % (getAllyTanksCount(False),       getEnemyTanksCount(False)))
            if PRINT_ITEMS['TanksHP']:
                file.write('Tanks HP:      %d\t<->\t%d\n'         % (getAllyTanksHP(False),          getEnemyTanksHP(False)))
#           if PRINT_ITEMS['TanksBW']:
#               file.write('Tanks BW:      %d\t<->\t%d\n'         % (getAllyTanksBW(False),          getEnemyTanksBW(False)))
            if PRINT_ITEMS['TanksOneDmg']:
                file.write('Tanks OneDmg:  %d\t<->\t%d\n'         % (getAllyTanksOneDamage(False),   getEnemyTanksOneDamage(False)))
            if PRINT_ITEMS['TanksMainDPM']:
                file.write('Tanks MainDPM: %d\t<->\t%d\n'         % (getAllyTanksMainDPM(False),     getEnemyTanksMainDPM(False)))
            if PRINT_ITEMS['TanksForces']:
                file.write('Tanks Forces:  %6.1f\t<->\t%6.1f\n'   % (getAllyTanksForces(False),      getEnemyTanksForces(False)))
            if PRINT_ITEMS['TeamChances']:
                file.write('Team Chances:  %5.2f\t<->\t%5.2f\n'   % (GLOBAL_STATISTICS['allyChance'],GLOBAL_STATISTICS['enemyChance']))
            file.write('\n')
            if PRINT_ITEMS['TanksList']:
                vIDSort = list(TANKS_STATISTICS.keys())
                vIDSort.sort(lambda x,y: 1 if TANKS_STATISTICS[y]['force'] > TANKS_STATISTICS[x]['force'] else -1 if TANKS_STATISTICS[y]['force'] < TANKS_STATISTICS[x]['force'] else 0)
                for vID in [vID for vID in vIDSort if TANKS_STATISTICS[vID]['isAlive'] and not TANKS_STATISTICS[vID]['isEnemy']]:
                    file.write(getStat(TANKS_STATISTICS[vID], full))
                file.write('\n')
                for vID in [vID for vID in vIDSort if TANKS_STATISTICS[vID]['isAlive'] and TANKS_STATISTICS[vID]['isEnemy']]:
                    file.write(getStat(TANKS_STATISTICS[vID], full))
                file.write('\n')

def showInfo(changeID=None):
    def getStat(stat):
        return '%s    %4d HP    %6.1f FR    %s\n' % ('E' if stat['isEnemy'] else 'A', stat['hp'], stat['force'], RemoveAccents(stat['name']))
        
    if SHOW_INFO and hasattr(g_appLoader.getDefBattleApp(), 'Chances_Chances'):
        label = g_appLoader.getDefBattleApp().Chances_Chances
        info  = ''
        if SHOW_ITEMS['TanksCount']:
            Ally  = getAllyTanksCount(False)
            Enemy = getEnemyTanksCount(False)
            AllyText = label.getHtmlTextWithTags('%d' % Ally, color=GUI_TEXT['CompareValuesColor'][2 if Ally == Enemy else 0 if Ally > Enemy else 1])
            EnemyText = label.getHtmlTextWithTags('%d' % Enemy, color=GUI_TEXT['CompareValuesColor'][2 if Ally == Enemy else 0 if Ally <= Enemy else 1])
            info += label.getSimpleTextWithTags('Tanks Count:   %s <-> %s\n') % (AllyText, EnemyText)
        if SHOW_ITEMS['TanksHP']:
            Ally  = getAllyTanksHP(False)
            Enemy = getEnemyTanksHP(False)
            AllyText = label.getHtmlTextWithTags('%d' % Ally, color=GUI_TEXT['CompareValuesColor'][2 if Ally == Enemy else 0 if Ally > Enemy else 1])
            EnemyText = label.getHtmlTextWithTags('%d' % Enemy, color=GUI_TEXT['CompareValuesColor'][2 if Ally == Enemy else 0 if Ally < Enemy else 1])
            info += label.getSimpleTextWithTags('Tanks HP:      %s <-> %s\n') % (AllyText, EnemyText)
#       if SHOW_ITEMS['TanksBW']:
#           Ally  = getAllyTanksBW(False)
#           Enemy = getEnemyTanksBW(False)
#           AllyText = label.getHtmlTextWithTags('%d' % Ally, color=GUI_TEXT['CompareValuesColor'][2 if Ally == Enemy else 0 if Ally > Enemy else 1])
#           EnemyText = label.getHtmlTextWithTags('%d' % Enemy, color=GUI_TEXT['CompareValuesColor'][2 if Ally == Enemy else 0 if Ally < Enemy else 1])
#           info += label.getSimpleTextWithTags('Tanks BW:      %s <-> %s\n') % (AllyText, EnemyText)
        if SHOW_ITEMS['TanksOneDmg']:
            Ally  = getAllyTanksOneDamage(False)
            Enemy = getEnemyTanksOneDamage(False)
            AllyText = label.getHtmlTextWithTags('%d' % Ally, color=GUI_TEXT['CompareValuesColor'][2 if Ally == Enemy else 0 if Ally > Enemy else 1])
            EnemyText = label.getHtmlTextWithTags('%d' % Enemy, color=GUI_TEXT['CompareValuesColor'][2 if Ally == Enemy else 0 if Ally < Enemy else 1])
            info += label.getSimpleTextWithTags('Tanks OneDmg:  %s <-> %s\n') % (AllyText, EnemyText)
        if SHOW_ITEMS['TanksMainDPM']:
            Ally  = getAllyTanksMainDPM(False)
            Enemy = getEnemyTanksMainDPM(False)
            AllyText = label.getHtmlTextWithTags('%d' % Ally, color=GUI_TEXT['CompareValuesColor'][2 if Ally == Enemy else 0 if Ally > Enemy else 1])
            EnemyText = label.getHtmlTextWithTags('%d' % Enemy, color=GUI_TEXT['CompareValuesColor'][2 if Ally == Enemy else 0 if Ally < Enemy else 1])
            info += label.getSimpleTextWithTags('Tanks MainDPM: %s <-> %s\n') % (AllyText, EnemyText)
        if SHOW_ITEMS['TanksForces']:
            Ally  = getAllyTanksForces(False)
            Enemy = getEnemyTanksForces(False)
            AllyText = label.getHtmlTextWithTags('%6.1f' % Ally, color=GUI_TEXT['CompareValuesColor'][3 if Ally == Enemy else 0 if Ally > Enemy else 1])
            EnemyText = label.getHtmlTextWithTags('%6.1f' % Enemy, color=GUI_TEXT['CompareValuesColor'][3 if Ally == Enemy else 0 if Ally < Enemy else 1])
            info += label.getSimpleTextWithTags('Tanks Forces:  %s <-> %s\n') % (AllyText, EnemyText)
        if SHOW_ITEMS['TeamChances']:
            Ally  = GLOBAL_STATISTICS['allyChance']
            Enemy = GLOBAL_STATISTICS['enemyChance']
            AllyText = label.getHtmlTextWithTags('%5.2f' % Ally, color=GUI_TEXT['CompareValuesColor'][2 if Ally == Enemy else 0 if Ally > Enemy else 1])
            EnemyText = label.getHtmlTextWithTags('%5.2f' % Enemy, color=GUI_TEXT['CompareValuesColor'][2 if Ally == Enemy else 0 if Ally < Enemy else 1])
            info += label.getSimpleTextWithTags('Team Chances:  %s <-> %s\n') % (AllyText, EnemyText)
        if SHOW_ITEMS['TanksList']:
            if info:
                info += '\n'
            vIDSort = list(TANKS_STATISTICS.keys())
            vIDSort.sort(lambda x,y: 1 if TANKS_STATISTICS[y]['force'] > TANKS_STATISTICS[x]['force'] else -1 if TANKS_STATISTICS[y]['force'] < TANKS_STATISTICS[x]['force'] else 0)
            for vID in [vID for vID in vIDSort if TANKS_STATISTICS[vID]['isAlive'] and not TANKS_STATISTICS[vID]['isEnemy']]:
                if vID == changeID:
                    info += label.getHtmlTextWithTags(getStat(TANKS_STATISTICS[vID]), color=GUI_TEXT['LastChangeColor'][0])
                else:
                    info += label.getSimpleTextWithTags(getStat(TANKS_STATISTICS[vID]))
            info += '\n'
            for vID in [vID for vID in vIDSort if TANKS_STATISTICS[vID]['isAlive'] and TANKS_STATISTICS[vID]['isEnemy']]:
                if vID == changeID:
                    info += label.getHtmlTextWithTags(getStat(TANKS_STATISTICS[vID]), color=GUI_TEXT['LastChangeColor'][1])
                else:
                    info += label.getSimpleTextWithTags(getStat(TANKS_STATISTICS[vID]))
        label.HtmlText(info)

# Hooks ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

def new_onHealthChanged(self, newHealth, attackerID, attackReasonID):
    old_onHealthChanged(self, newHealth, attackerID, attackReasonID)
    global TANKS_STATISTICS
    if self.id in TANKS_STATISTICS:
        value = TANKS_STATISTICS[self.id]
        if value['hp'] != self.health:
            value['hp'] = self.health
            calcGlobalStatistics()
            showInfo(self.id)
            if value['hp'] == 0:
                value['isAlive'] = False
                printStrings(('------------------------- %s -------------------------\n' % datetime.now().strftime('%d.%m.%y %H:%M:%S'), '\nReason: VehicleDied\n\n'))
            else:
                printStrings(('------------------------- %s -------------------------\n' % datetime.now().strftime('%d.%m.%y %H:%M:%S'), '\nReason: HealthChanged\n\n'))
            printInfo()

def new_vehicle_onEnterWorld(self, vehicle):
    old_vehicle_onEnterWorld(self, vehicle)
    global TANKS_STATISTICS
    entity = BigWorld.entity(vehicle.id)
    if entity and vehicle.id in TANKS_STATISTICS:
        value = TANKS_STATISTICS[vehicle.id]
        if value['hp'] != entity.health:
            value['hp'] = entity.health
            if value['hp'] == 0:
                value['isAlive'] = False
            calcGlobalStatistics()
            showInfo(vehicle.id)
            printStrings(('------------------------- %s -------------------------\n' % datetime.now().strftime('%d.%m.%y %H:%M:%S'), '\nReason: VehicleEnterWorld\n\n'))
            printInfo()

def new_onArenaVehicleKilled(self, targetID, attackerID, equipmentID, reason):
    global TANKS_STATISTICS
    try:
        if targetID in TANKS_STATISTICS:
            value = TANKS_STATISTICS[targetID]
            if value['isAlive'] != False:
                value['isAlive'] = False
                value['hp'] = 0
                calcGlobalStatistics()
                showInfo(targetID)
                printStrings(('------------------------- %s -------------------------\n' % datetime.now().strftime('%d.%m.%y %H:%M:%S'), '\nReason: VehicleKilled\n\n'))
                printInfo()
    finally:
        old_onArenaVehicleKilled(self, targetID, attackerID, equipmentID, reason)

def new__startGUI(self):
    old__startGUI(self)
    global CONFIG_FILENAME, LOG_FILENAME, SHOW_INFO, SHOW_ITEMS, PRINT_LOG, PRINT_ITEMS, GUI_TEXT
    CONFIG_FILENAME = getConfigFileName()
    if CONFIG_FILENAME is not None:
        config         = json.loads(re.compile('(/\*(.|\n)*?\*/)|((#|//).*?$)', re.I | re.M).sub('', codecs.open(CONFIG_FILENAME, 'r', 'utf-8-sig').read()))
        SHOW_INFO      = config['System']['TeamChances']['GUIStatistics']['Show']
        SHOW_ITEMS     = config['System']['TeamChances']['GUIStatistics']['ShowItems']
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
        PRINT_LOG      = config['System']['TeamChances']['PrintLog']
        PRINT_ITEMS    = config['System']['TeamChances']['LogFormat']['PrintItems']
        LOG_FILENAME   = getLogFileName(config['System']['TeamChances']['LogFormat']['Dir'], config['System']['TeamChances']['LogFormat']['Prefix'])
    global GLOBAL_STATISTICS, TANKS_STATISTICS
    GLOBAL_STATISTICS.clear()
    TANKS_STATISTICS.clear()
    for vID in BigWorld.player().arena.vehicles: #Кэшируем статистику
        vehicleType = BigWorld.player().arena.vehicles[vID]['vehicleType']
        TANKS_STATISTICS[vID] = value = {}
        value['name']          = vehicleType.type.shortUserString.replace(' ','')
        value['type']          = {}
        value['type']['id'], \
        value['type']['name']  = getTankType(vehicleType.type.tags)
        value['isEnemy']       = (BigWorld.player().arena.vehicles[vID]['team'] != BigWorld.player().team)
        value['isAlive']       = True
        value['level']         = int(vehicleType.level)
#       value['balanceWeight'] = float(vehicleType.balanceWeight)
        value['hp']            = int(vehicleType.maxHealth)
        #Оборудование
        RammerOD = False #Досылатель
        for item in vehicleType.optionalDevices:
            if item and 'TankRammer' in item.name:
                RammerOD = True
                break
        value['gun']           = {} #Орудие
        value['gun']['reload'] = float(vehicleType.gun['reloadTime'])
        if RammerOD:
            value['gun']['reload'] = value['gun']['reload'] * 0.9
        if vehicleType.gun.has_key('clip'):
            if vehicleType.gun['clip'][0] > 1:
                value['gun']['ammer'] = {} #Барабан
                value['gun']['ammer']['reload']      = value['gun']['reload']
                value['gun']['ammer']['shellCount']  = int(vehicleType.gun['clip'][0])
                value['gun']['ammer']['shellReload'] = float(vehicleType.gun['clip'][1])
                if RammerOD:
                    value['gun']['ammer']['shellReload'] = value['gun']['ammer']['shellReload'] * 0.9
                #Эквивалентное время: 2 сек - 5 x 1 дмг | 30 сек -> 2+30/5 = 8 сек
                value['gun']['reload'] = value['gun']['ammer']['shellReload'] + value['gun']['ammer']['reload'] / value['gun']['ammer']['shellCount'] 
        value['gun']['shell'] = {0: {'typeName': 'AP',   'damage': 0, 'dpm': 0}, \
                                                 1: {'typeName': 'APRC', 'damage': 0, 'dpm': 0}, \
                                                 2: {'typeName': 'HC',   'damage': 0, 'dpm': 0}, \
                                                 3: {'typeName': 'HE',   'damage': 0, 'dpm': 0}} #Снаряды
        for shellID in vehicleType.gun['shots']:
            index, _ = getShellTypeID(shellID['shell']['kind'])
            value['gun']['caliber'] = float(shellID['shell']['caliber'])
            damage = float(shellID['shell']['damage'][0])
            if damage > value['gun']['shell'][index]['damage']:
                value['gun']['shell'][index]['damage'] = damage
                value['gun']['shell'][index]['dpm']    = damage * 60 / value['gun']['reload']
        if value['type']['id'] == 4: #САУ
            shellID = 3 #ОФ
        else: #Остальные
            if value['gun']['shell'][0]['damage'] != 0:
                shellID = 0 #ББ
            elif value['gun']['shell'][1]['damage'] != 0:
                shellID = 1 #ПК для тех у кого нет ББ
            else:
                shellID = 3 #иначе ОФ
        value['gun']['mainShell']  = shellID #Базовый снаряд танка        
        value['gun']['mainDamage'] = value['gun']['shell'][value['gun']['mainShell']]['damage'] * (0.5 if value['gun']['mainShell'] == 3 else 1) #Урон базовым снарядом
        value['gun']['mainDpm']    = value['gun']['shell'][value['gun']['mainShell']]['dpm'] * (0.5 if value['gun']['mainShell'] == 3 else 1) #DPM базовым снарядом
    calcGlobalStatistics()
    printStrings(('------------------------- %s -------------------------\n' % datetime.now().strftime('%d.%m.%y %H:%M:%S'), '\nReason: BattleLoading\n\n'))    
    printInfo(True)

def flashLoad(): 
    if SHOW_INFO:
        g_appLoader.getDefBattleApp().Chances_Chances = FlashTextLabel(GUI_TEXT)
        showInfo()

g_flashTextLabels.onLoadedFlash += flashLoad

old_onHealthChanged = Vehicle.onHealthChanged
Vehicle.onHealthChanged = new_onHealthChanged

old_vehicle_onEnterWorld = PlayerAvatar.vehicle_onEnterWorld
PlayerAvatar.vehicle_onEnterWorld = new_vehicle_onEnterWorld

old_onArenaVehicleKilled = PlayerAvatar._PlayerAvatar__onArenaVehicleKilled
PlayerAvatar._PlayerAvatar__onArenaVehicleKilled = new_onArenaVehicleKilled

old__startGUI = PlayerAvatar._PlayerAvatar__startGUI
PlayerAvatar._PlayerAvatar__startGUI = new__startGUI