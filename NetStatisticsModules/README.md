# NetStatisticsModules(NSM)

## List of modules:
* "XVMStatistics" - getting statistics from the XVM-server
* "VictoryChances" - calculation of chances for victory in battle

## Install
Put the zip-file to a folder "World_of_Tanks\mods\X.X.X\"

## Terms of Use
#### Module "XVMStatistics"
Events access:
```
from gui.mods.XVMStatistics import g_XVMStatisticsEvents

  #Returns the statistics of the player during authorization in the game client,
  #if there is no data on the server or there is no connection or there is no token, it returns None
  g_XVMStatisticsEvents.OnStatsAccountBecomePlayer(-> dict or None)
    #{"b":19807,
    # "e":1462,
    # "v":{"63505":{"b":1,"w":0,"cap":0,"def":0,"dmg":52,"frg":0,"spo":0,"srv":0,"wtr":753}, ...},
    # "w":11594,
    # "dt":"2018-01-30T00:52:23.465+00:00",
    # "nm":"StranikS_Scan",
    # "ts":1517273543000,"xp":null,"_id":2365719,"cap":38210,"cid":69731,"def":14537,"dmg":29176230,"frg":23928,"hip":71,"lvl":7.53855,
    # "spo":22198,"srv":null,"wgr":8989,"wn8":2103,"wtr":6744,"flag":null,"lang":null,"dmg_r":null,"max_xp":null,
    # "status":1,"max_dmg":null,"max_frg":null,"is_banned":null}

  #Returns the statistics of all players when the battle is loaded,
  #if there is no connection to the server or there is no token, then it returns None
  g_XVMStatisticsEvents.OnStatsBattleLoaded(-> dict or None)
    #{"players":[{"b":19807,
    #             "e":1462,
    #             "r":8989,
    #             "v":{"b":331,"w":202,"cap":1159,"def":286,"dmg":98371,"frg":592,"spo":459,"srv":122,"wtr":2919},
    #             "w":11594,
    #             "nm":"StranikS_Scan",
    #             "ts":1517273543465,"xp":null,"_id":2365719,"cap":38210,"cid":69731,"def":14537,"dmg":29176230,"frg":23928,"hip":71,"lvl":7.53855,
    #             "spo":22198,"srv":null,"wgr":8989,"wn8":2103,"wtr":6744,"flag":null,"lang":null,"dmg_r":null,"max_xp":null,"status":1,"max_dmg":null,"max_frg":null,"is_banned":null},
    #            {"b":39441,
    #             "e":881,
    #             "r":4981,
    #             "v":{"b":40,"w":20,"xp":6367,"cap":0,"def":0,"dmg":2682,"frg":13,"mom":3,"spo":35,"srv":7,"wtr":2642},
    #             "w":19317,
    #             "nm":"JM71",
    #             "ts":1517552268047,"xp":14205000,"_id":4100782,"cap":24261,"cid":null,"def":22125,"dmg":33753828,"frg":26228,"hip":51,"lvl":7.27749,
    #             "spo":40334,"srv":8651,"wgr":4981,"wn8":1082,"wtr":4186,
    #             "flag":null,"lang":null,"dmg_r":25312886,"max_xp":2306,"status":null,"max_dmg":6392,"max_frg":8,"is_banned":null}]}
```
Console access:
```
#If there is no connection to the server or there is no token, then it returns None
from gui.mods.XVMStatistics import g_XVMConsole

  #Returns reports from the server for the _Async requests, if no onAsyncReport is specified
  g_XVMConsole.OnAsyncReports(-> dict or None)

  #Return info by current version of XVM and icons list of 50-top clans
  g_XVMConsole.getVersionWithLimit() -> dict or None
  g_XVMConsole.getVersionWithLimit_Async(onAsyncReport=func or None)

  #Return statistics for one player with all the tanks by a accountDBID
  #example accountDBID=2365719
  g_XVMConsole.getStatsByID(accountDBID=int) -> dict or None
  g_XVMConsole.getStatsByID_Async(accountDBID=int, onAsyncReport=func or None)

  #The same, but with the help of the player's nickname
  #example region='RU', nick='StranikS_Scan'
  g_XVMConsole.getStatsByNick(region=str, nick=str) -> dict or None
  g_XVMConsole.getStatsByNick_Async(region=str, nick=str, onAsyncReport=func or None)

  #Return statistics for a specific tank for one or multiple users
  #example ids = {2365719:54529, 4100782:51841, accountDBID:compactDescr, ...}
  g_XVMConsole.getStats(ids=dict) -> dict or None
  g_XVMConsole.getStats_Async(ids=dict, onAsyncReport=func or None)

  #Return online WOT-server statistics
  g_XVMConsole.getOnlineUsersCount() -> dict or None
  g_XVMConsole.getOnlineUsersCount_Async(onAsyncReport=func or None)
```
Other:
```
#Used token
from gui.mods.XVMStatistics import g_UserToken

g_UserToken.accountDBID  -> int or None
g_UserToken.userToken    -> str or None
g_UserToken.errorStatus  -> str
```
---
#### Module "VictoryChances"
Events access:
```
#Set of events to track changes in the tanks composition and the chances of winning
from gui.mods.VictoryChances import g_StatisticEvents

  #It works when the caching of users and tanks information is completed when the battle is loaded
  #Returns a pointer to g_TanksStatistic
  g_StatisticEvents.OnBattleLoaded(-> statistic=class)

  #It works when the players and the parameters of the tanks change
  #Returns a pointer to g_TanksStatistic, reasone type as UPDATE_REASONE and vehicleID
  g_StatisticEvents.OnVehiclesChanged(-> statistic=class, reasone=int, vID=int)

  #It works when change the count of tanks in teams
  #Returns tuple with count tanks as (ally, enemy)
  g_StatisticEvents.OnCountChanged(-> count=tuple)

  #It works when the health of users changed
  #Returns tuple with total healths of teams as (ally, enemy)
  g_StatisticEvents.OnHealthChanged(-> health=tuple)

  #It works when the chances of victory changed
  #Returns tuples with chances 0-100 and total forces of teams as (ally, enemy)
  g_StatisticEvents.OnChanceChanged(-> chances=tuple, forces=tuple)
```
Other:
```
#Parameters of tanks and players statistics
from gui.mods.VictoryChances import g_TanksStatistic

  g_TanksStatistic.base               -> dict
  g_TanksStatistic.allyChance         -> int or None
  g_TanksStatistic.enemyChance        -> int or None
  g_TanksStatistic.allyTanksCount     -> int or None
  g_TanksStatistic.enemyTanksCount    -> int or None
  g_TanksStatistic.allyTeamHP         -> int or None
  g_TanksStatistic.enemyTeamHP        -> int or None
  g_TanksStatistic.allyTeamOneDamage  -> int or None
  g_TanksStatistic.enemyTeamOneDamage -> int or None
  g_TanksStatistic.allyTeamDPM        -> int or None
  g_TanksStatistic.enemyTeamDPM       -> int or None
  g_TanksStatistic.allyTeamForces     -> int or None
  g_TanksStatistic.enemyTeamForces    -> int or None
    
#Types of reasons in OnVehiclesChanged event
from gui.mods.VictoryChances import UPDATE_REASONE

  UPDATE_REASONE.VEHICLE_ADDED  -> int
  UPDATE_REASONE.VEHICLE_DEATH  -> int
  UPDATE_REASONE.HEALTH_CHANGED -> int
```
