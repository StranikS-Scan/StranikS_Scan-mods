# SimpleLogger

### Description
Mod records various information about battles, vehicles, players in CSV-files (using the **NetStatisticsModules**). The mod receives information about the player's statistics via the WG-API and also through the XVM-API. To collect information about player online-statistics from XVM-API, activation on the [XVM-website](https://modxvm.com/) is necessary. It is not required to install the XVM-mod itself.

## Install
Extract all files from "[SimpleLogger.zip][]" to the folder "World_of_Tanks\"

## Using
Install the mod into the game and run the replay, the information from which you want to extract. Play replay until the end is not necessary. After that, files with information will appear in the folder "World_of_Tanks\mods\logs\":
* **"sl_battles_xxx.csv"** - information about the map, player, type of battle
* **"sl_players_xxx.csv"** - information about the composition of teams, nicknames and IDs of players, names and types of vehicles, player ratings and statistics
* **"sl_events_xxx.csv"** - information about the events in the game: shots, hits, piercings, etc.

The mod settings are in the file "World_of_Tanks\mods\configs\SimpleLogger\SimpleLogger.cfg".

## Examples
Examples of studying hits in the tank using mod can be found in [Wiki](https://github.com/StranikS-Scan/StranikS_Scan-mods/wiki)

## History
With the history of versions can be found [here](./HISTORY.md)

[mod.NetStatisticsModules_X.X.X.wotmod]:../NetStatisticsModules/zip
[SimpleLogger.zip]:./zip