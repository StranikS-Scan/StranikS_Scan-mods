# -*- coding: utf-8 -*-

__version__ = 'V1.7 P2.7 W1.0.0 17.03.2018'
__author__  = 'StranikS_Scan'

import BigWorld
from VehicleStickers import ModelStickers, SlotTypes
from account_helpers.CustomFilesCache import CustomFilesCache, WorkerThread
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

old___run_download = WorkerThread._WorkerThread__run_download

def new__run_download(self, url, modified_time, callback, **params):
    if str(url).find('emblem_64x64_tank.png') == -1:
        old___run_download(self, url, modified_time, callback, **params)

WorkerThread._WorkerThread__run_download = new__run_download

# Очистка кэша иконок в AppData\Roaming\ -------------------------------------------

def new__init__(self):
    try:
        Preferences = BigWorld.wg_getPreferencesFilePath()
        if path.isfile(Preferences):
            Custom_data = path.dirname(Preferences) + '/custom_data'
            if path.isdir(Custom_data):
                for name in next(walk(Custom_data))[2]:
                    name = Custom_data + '/'+ name
                    if path.isfile(name):
                        if 'icons.bak' in name or 'icons.dir' in name or 'icons.dat' in name:
                            try:
                                remove(name)
                            except:
                                pass
                            else:
                                print '[%s] EmblemsOff: cache of icons was deleted successfully!' % __author__
    finally:
        old__init__(self)

old__init__ = CustomFilesCache.__init__ 
CustomFilesCache.__init__ = new__init__

print '[%s] Loading mod: emblemsOff %s (http://www.koreanrandom.com/forum/topic/21432-)' % (__author__, __version__)