# -*- coding: utf-8 -*-

__version__ = 'V1.7.2 P2.7 W1.0.0 09.08.2018'
__author__  = 'StranikS_Scan'

import BigWorld
from VehicleStickers import ModelStickers, SlotTypes
from account_helpers.CustomFilesCache import CustomFilesCache
from os import path, walk, remove

# Хук на аттач эмблем --------------------------------------------------------------

def new_attachStickers(self, model, parentNode, isDamaged, toPartRootMatrix=None):
    self.detachStickers()
    self._ModelStickers__model = model
    if toPartRootMatrix is not None:
        self.__toPartRootMatrix = toPartRootMatrix
    self._ModelStickers__parentNode = parentNode
    self._ModelStickers__isDamaged = isDamaged
    self._ModelStickers__stickerModel.setupSuperModel(self._ModelStickers__model, self._ModelStickers__toPartRootMatrix)
    self._ModelStickers__parentNode.attach(self._ModelStickers__stickerModel)
    for slotType, slots in self._ModelStickers__slotsByType.iteritems():
        if slotType != SlotTypes.CLAN:
            self._ModelStickers__doAttachStickers(slotType)
    return

ModelStickers.attachStickers = new_attachStickers

# Хук на скачивание эмблем кланов --------------------------------------------------

old__readRemoteFile = CustomFilesCache._CustomFilesCache__readRemoteFile

def new__readRemoteFile(self, url, modified_time, showImmediately, headers):
    if str(url).find('emblem_64x64_tank.png') == -1:
        old__readRemoteFile(self, url, modified_time, showImmediately, headers)

CustomFilesCache._CustomFilesCache__readRemoteFile = new__readRemoteFile

# Очистка кэша иконок в AppData\Roaming\ -------------------------------------------

ICONS_FILES = ('icons.bak', 'icons.dir', 'icons.dat')

def new__init__(self, cacheFolder):
    try:
        Preferences = BigWorld.wg_getPreferencesFilePath()
        if path.isfile(Preferences):
            Custom_data = path.dirname(Preferences) + '/custom_data'
            if path.isdir(Custom_data):
                for name in next(walk(Custom_data))[2]:
                    name = Custom_data + '/'+ name
                    if path.isfile(name):                        
                        for icons_file in ICONS_FILES:
                            if icons_file in name:
                                try:
                                    remove(name)
                                except:
                                    pass
                                else:
                                    print '[%s] "emblems_off": %s was deleted successfully!' % (__author__, icons_file)
    finally:
        old__init__(self, cacheFolder)

old__init__ = CustomFilesCache.__init__ 
CustomFilesCache.__init__ = new__init__

print '[%s] Loading mod: "emblems_off" %s (http://www.koreanrandom.com/forum/topic/21432-)' % (__author__, __version__)