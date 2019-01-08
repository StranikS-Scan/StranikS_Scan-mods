# NetStatisticsModules(NSM)

## List of modules:
* "xvm_statistics" - getting statistics from the XVM-server
* "wg_statistics" - getting statistics from the WG-server
* "rating_calculation" - functions for calculating ratings and player scores
* "victory_chances" - calculation of chances for victory in battle
* "hook_methods" - system module for the Monkey patch (is similar to the code from XVM)

## Install
1. Register your application 'MyApplication' in the modes developer’s office (https://developers.wargaming.net)
2. Enter your application_id in self.TOKENS in the file 'api_tokens.py'
3. Compile this file with obfuscation, example in PjOrion, so as not to disclose your application_id
4. Create wotmod-file using 'Zip-Packer.cmd'
5. Put the wotmod-file to a folder "World_of_Tanks\mods\X.X.X\"

## Official theme
https://koreanrandom.com/forum/topic/47960-

## History
With the history of versions can be found [here][]

[here]:./HISTORY.md