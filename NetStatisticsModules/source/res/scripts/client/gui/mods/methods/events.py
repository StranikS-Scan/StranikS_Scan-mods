# -*- coding: utf-8 -*-

__author__  = 'StranikS_Scan'
__version__ = 'V1.0 P2.7 W1.3.0 17.01.2019'

from random import shuffle
from copy import deepcopy

class _AppTokens(object):
    appToken = property(lambda self: self.__current)

    def __init__(self, tokens=None):
        self.__tokens = []
        self.__current = None
        if tokens:
            self.setAppTokens(tokens)

    def setAppTokens(self, tokens):
        self.__tokens = [] if not tokens else [tokens] if isinstance(tokens, str) else deepcopy(tokens) 
        self.__current = self.__tokens[0] if self.__tokens else None

    def addAppTokens(self, tokens):
        if tokens:
            self.__tokens += [tokens] if isinstance(tokens, str) else tokens
            if not self.__current:
                self.__current = self.__tokens[0]

    def delAppTokens(self, tokens):
        if tokens:
            if isinstance(tokens, str):
                tokens = [tokens]
            for token in tokens:
                if token in self.__tokens:
                    self.__tokens.remove(token)
            self.__current = self.__tokens[0] if self.__tokens else None

    def mixAppTokens(self):
        if self.__tokens and len(self.__tokens) > 1:
            shuffle(self.__tokens)
            self.__current = self.__tokens[0]

    def nextAppToken(self):
        if self.__tokens and len(self.__tokens) > 1:
            index = self.__tokens.index(self.__current) + 1
            if index >= len(self.__tokens):
                index = 0
            self.__current = self.__tokens[index]
        return self.__current

class EVENTS:
    ACCOUNT_BECOME_PLAYER = 0
    BATTLE_LOADED         = 1
    FULL_BATTLE_LOADED    = 2

class _StatisticsEvents(object):
    _onStats_AccountBecomePlayer = property(lambda self: reduce(lambda r, x: r.extend(x) or r, self.__onStats[EVENTS.ACCOUNT_BECOME_PLAYER].values(), []))
    _onStats_BattleLoaded = property(lambda self: reduce(lambda r, x: r.extend(x) or r, self.__onStats[EVENTS.BATTLE_LOADED].values(), []))
    _onStats_FullBattleLoaded = property(lambda self: reduce(lambda r, x: r.extend(x) or r, self.__onStats[EVENTS.FULL_BATTLE_LOADED].values(), []))
    _appTokens_AccountBecomePlayer = property(lambda self: self.__appTokens[EVENTS.ACCOUNT_BECOME_PLAYER])
    _appTokens_BattleLoaded = property(lambda self: self.__appTokens[EVENTS.BATTLE_LOADED])
    _appTokens_FullBattleLoaded = property(lambda self: self.__appTokens[EVENTS.FULL_BATTLE_LOADED])

    def __init__(self):
        self.__onStats = {}
        self.__onStats[EVENTS.ACCOUNT_BECOME_PLAYER] = {}
        self.__onStats[EVENTS.BATTLE_LOADED] = {}
        self.__onStats[EVENTS.FULL_BATTLE_LOADED] = {}
        self.__appTokens = {}
        self.__appTokens[EVENTS.ACCOUNT_BECOME_PLAYER] = _AppTokens()
        self.__appTokens[EVENTS.BATTLE_LOADED] = _AppTokens()
        self.__appTokens[EVENTS.FULL_BATTLE_LOADED] = _AppTokens()

    def __addStats(self, appToken, action, event):
        onStats = self.__onStats[action]
        if appToken in onStats:
            onStats[appToken].append(event)
        else:
            onStats[appToken] = [event]
            self.__appTokens[action].addAppTokens(appToken)

    def __delStats(self, appToken, action, event):
        onStats = self.__onStats[action]
        if event:
            if event in onStats[appToken]:
                onStats[appToken].remove(event)
            if not onStats[appToken]:
                onStats.pop(appToken)
                self.__appTokens[action].delAppTokens(appToken)
        else:
            self.__onStats[action].pop(appToken)
            self.__appTokens[action].delAppTokens(appToken)

    def addStatsAccountBecomePlayer(self, appToken, event):
        if appToken and event:
            self.__addStats(appToken, EVENTS.ACCOUNT_BECOME_PLAYER, event)

    def delStatsAccountBecomePlayer(self, appToken, event=None):
        if appToken and appToken in self.__onStats[EVENTS.ACCOUNT_BECOME_PLAYER]:
            self.__delStats(appToken, EVENTS.ACCOUNT_BECOME_PLAYER, event)

    def addStatsBattleLoaded(self, appToken, event):
        if appToken and event:
            self.__addStats(appToken, EVENTS.BATTLE_LOADED, event)

    def delStatsBattleLoaded(self, appToken, event=None):
        if appToken and appToken in self.__onStats[EVENTS.BATTLE_LOADED]:
            self.__delStats(appToken, EVENTS.BATTLE_LOADED, event)

    def addStatsFullBattleLoaded(self, appToken, event):
        if appToken and event:
            self.__addStats(appToken, EVENTS.FULL_BATTLE_LOADED, event)

    def delStatsFullBattleLoaded(self, appToken, event=None):
        if appToken and appToken in self.__onStats[EVENTS.FULL_BATTLE_LOADED]:
            self.__delStats(appToken, EVENTS.FULL_BATTLE_LOADED, event)
