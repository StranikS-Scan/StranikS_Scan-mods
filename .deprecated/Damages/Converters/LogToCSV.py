# -*- coding: utf-8 -*-
'''
Converting log-file to csv-file for Excel 
'''

__version__ = 'V1.3 P2.7 15.11.2015'
__author__  = 'StranikS_Scan'

# User options ----------------------------------------------------------

LogFileNamePrefix = 'damages_' #Начало названия log-файлов
LogFileNameExt    = '.log'     #Расширение log-файлов
AllLogsToOne      = False      #Сливать все файлы в один

# System options --------------------------------------------------------

EXTENSION = '.csv'

# Code ------------------------------------------------------------------

from os import path, listdir
import codecs

files = filter(lambda x: x.startswith(LogFileNamePrefix) and x.endswith(LogFileNameExt), listdir('.'))

def getExcelStyleInfo(filename):
    stat = codecs.open(filename, 'r', 'utf-8-sig').read()
    stat = stat.replace(u'\ufeff','')
    stat = [x for x in stat.split('\n') if x and not x.startswith('Reason')]
    i = 1
    tanks = {}
    while not stat[i].startswith('---'):
        line = [x for x in stat[i].split('\t') if x]
        tank_name, user_name = line[-1].split(' (')
        user_name = user_name[:-1]
        tanks[user_name] = {'name': tank_name, 'command': line[0], 'tank_type': line[1], 'bw': float(line[2][:-2]), 'hp': int(line[3][:-2]), 'caliber': float(line[4][:-2])}
        tanks[user_name]['base_shell'] = line[5]    
        line = line[6][:-3].replace(' ','').split('|')
        tanks[user_name]['AP']   = float(line[0].split('-')[1])
        tanks[user_name]['APRC'] = float(line[1].split('-')[1])
        tanks[user_name]['HC']   = float(line[2].split('-')[1])
        tanks[user_name]['HE']   = float(line[3].split('-')[1])
        tanks[user_name]['UNK']  = tanks[user_name][tanks[user_name]['base_shell']]
        i += 1
    lines = len(stat)
    info = ''
    while i<lines:
        if stat[i].startswith('---'):
            date, time = stat[i].replace('-', '')[1:-1].split(' ')
            date = date.replace('.','-')
            i += 1
            line = [x for x in stat[i].split(' ') if x]
            attacker = {'commad': line[0], 'shell_type': line[1], 'dmg': float(line[2]), 'percent': float(line[4][:-1]), 'name': line[6][1:-1]}
            i += 1
            line =  [x for x in stat[i].split(' ') if x]
            if line[1] == 'BOOM!':
                hp = line[2].split('->')
                target = {'commad': line[0], 'ammo_destroyed': 1, 'hp_before': int(hp[0]), 'hp_after': int(hp[1]), 'name': line[5][1:-1]}
            else:
                hp = line[1].split('->')
                target = {'commad': line[0], 'ammo_destroyed': '', 'hp_before': int(hp[0]), 'hp_after': int(hp[1]), 'name': line[4][1:-1]}
            i += 1
            line = ";".join([date,
                             time, 
                             '"%s"' % attacker['name'], 
                             '"%s"' % attacker['commad'],
                             '"%s"' % tanks[attacker['name']]['name'],
                             '"%s"' % tanks[attacker['name']]['tank_type'],
                             ('%.1f' % tanks[attacker['name']]['caliber']).replace('.',','),
                             '%d' % tanks[attacker['name']][attacker['shell_type']],
                             '"%s"' % attacker['shell_type'],
                             '%s' % target['ammo_destroyed'],
                             '%d' % attacker['dmg'], 
                             ('%.1f' % attacker['percent']).replace('.',','),
                             '"%s"' % target['name'],
                             '"%s"' % target['commad'],
                             '"%s"' % tanks[target['name']]['name'],
                             '%d' % target['hp_before'],
                             '%d' % target['hp_after']])
            info += line + '\n'
    return info

Header = '"Date";"Time";"Attacker";"Command";"Tank";"Type";"Caliber";"Base_Dmg";"Type";"AmmoDestroyed";"Dmg";"Percent";"Target";"Command";"Tank";"HP_Before";"HP_After"\n'

if files:
    if AllLogsToOne:
        with codecs.open(path.splitext(files[0])[0]+EXTENSION, 'w', 'utf-8-sig') as f: 
            f.write(Header)
            for log in files:
                f.write(getExcelStyleInfo(log))
    else:
        for log in files:
            with codecs.open(path.splitext(log)[0]+EXTENSION, 'w', 'utf-8-sig') as f:
                f.write(Header)
                f.write(getExcelStyleInfo(log))            


