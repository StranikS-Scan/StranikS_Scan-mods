# -*- coding: utf-8 -*-

__version__ = 'V2.0 P2.7 W1.4.0 25.02.2019'
__author__  = 'StranikS_Scan'

import BigWorld
from VehicleStickers import ModelStickers, SlotTypes
from account_helpers.CustomFilesCache import CustomFilesCache
from os import path, walk, remove

# Хук на аттач эмблем --------------------------------------------------------------

def new_ModelStickers__init__(self, componentIdx, stickerPacks, *a, **k):
    stickerPacks[SlotTypes.CLAN] = ()
    old_ModelStickers__init__(self, componentIdx, stickerPacks, *a, **k)

old_ModelStickers__init__ = ModelStickers.__init__
ModelStickers.__init__ = new_ModelStickers__init__

# Хук на скачивание эмблем кланов --------------------------------------------------

def new_CustomFilesCache__readRemoteFile(self, url, *a, **k):
    if str(url).find('emblem_64x64_tank.png') == -1:
        old_CustomFilesCache__readRemoteFile(self, url, *a, **k)

old_CustomFilesCache__readRemoteFile = CustomFilesCache._CustomFilesCache__readRemoteFile
CustomFilesCache._CustomFilesCache__readRemoteFile = new_CustomFilesCache__readRemoteFile

# Очистка кэша иконок в AppData\Roaming\ -------------------------------------------

ICONS_FILES = ('icons.bak', 'icons.dir', 'icons.dat')

def new_CustomFilesCache__init__(self, *a, **k):
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
        old_CustomFilesCache__init__(self, *a, **k)

old_CustomFilesCache__init__ = CustomFilesCache.__init__ 
CustomFilesCache.__init__ = new_CustomFilesCache__init__

print '[%s] Loading mod: "emblems_off" %s (http://www.koreanrandom.com/forum/topic/21432-)' % (__author__, __version__)