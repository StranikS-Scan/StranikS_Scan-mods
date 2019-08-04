# -*- coding: utf-8 -*-

__author__  = 'StranikS_Scan'
__version__ = 'V1.1 P2.7 W0.9.15 26.05.2016'

import GUI

class _TextLabel(object):
    def __init__(self, x, y, color, font, linesCount=1):
        self.__lines = []
        self.__linesCount = linesCount
        self.__x = x
        self.__y = y
        self.__color = '\c%s;' % color
        self.__gui = GUI.Text('')
        self.__gui.visible = False
        self.__gui.colourFormatting = self.__gui.multiline = True
        self.__gui.widthMode = self.__gui.heightMode = self.__gui.verticalPositionMode = self.__gui.horizontalPositionMode = 'PIXEL'
        self.__gui.horizontalAnchor = 'LEFT'
        self.__gui.verticalAnchor = 'TOP'
        self.__gui.font = font

    def destroy(self):
        self.hide()
        self.__lines = self.__gui = None

    def add(self, text):
        self.__lines.insert(0, text)
        self.__lines = self.__lines[:self.__linesCount]
        self.__gui.text = self.__color + '\n'.join(self.__lines)

    def append(self, text):
        self.__lines.append(text)
        self.__lines = self.__lines[-self.__linesCount:]
        self.__gui.text = self.__color + '\n'.join(self.__lines)

    def show(self):
        x0, y0 = GUI.screenResolution()
        GUI.addRoot(self.__gui)
        self.__gui.position = ((x0 + self.__x) // 2, (y0 + self.__y) // 2, 0.15)
        self.__gui.visible = True

    def hide(self):
        if self.__gui.visible:
            self.__gui.visible = False
            GUI.delRoot(self.__gui)

    def text(self, text=''):
        self.__lines = [text]
        self.__gui.text = self.__color + self.__lines[0]

g_guiTexts = {}