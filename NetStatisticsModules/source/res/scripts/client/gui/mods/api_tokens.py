# -*- coding: utf-8 -*-

__author__  = 'StranikS_Scan'
__version__ = 'V1.0 P2.7 W1.3.0 08.01.2019'

#+---------------------------------------------  ATTENTION --------------------------------------------------------+
#| If you are a modes maker and want to use the library for your own purposes, then you need to:                   |
#| 1. Register your application 'MyApplication' in the modes developer’s office (https://developers.wargaming.net) |
#| 2. Enter your application_id in self.TOKENS                                                                     |
#| 3. Compile this file with obfuscation, example in PjOrion, so as not to disclose your application_id            |
#| 4. Remove you 'api_tokens.py' from library sources                                                              |
#+-----------------------------------------------------------------------------------------------------------------+

from random import shuffle

class _API_TOKENS(object):
    CURRENT = property(lambda self: self.__current)

    def __init__(self):
        #Here should be your application_id or list of id's if you want to reduce the load on tokens
        self.tokens = ['76f79f28cc829699fe6225c90b7bda28']
        self.__current = self.__tokens[0]

    def RANDOMIZE(self):
        if len(self.__tokens) > 1:
            shuffle(self.__tokens)
            self.__current = self.__tokens[0]
        return self.__current

    def NEXT(self):
        if len(self.__tokens) > 1:
            index = self.__tokens.index(self.__current) + 1
            if index >= len(self.__tokens):
                index = 0
            self.__current = self.__tokens[index]
        return self.__current

API_TOKENS = _API_TOKENS()
