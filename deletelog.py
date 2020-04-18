from os import remove
import time
import json
from telegrambot import directory_path

'''
This file will delete old logs (that have more than 30 days since they have been saved forever.)
This script will run every day at 5am.
'''

if __name__ == "__main__":
    remove_old()

def remove_old():
    with open((directory_path() +'logs_info.json'), 'r') as filein:
        loginfo = json.loads(filein)
    fout = open((directory_path() +'logs_info.json'), 'w')
    result = {'msgs-actual': loginfo['msgs-actual'], 'status-actual' : loginfo['status-actual'], 'msgs-saved' : {}, 'status-saved' : {}}
    for filename, saved in loginfo['msgs-saved'].items():
        if (saved + 2592000) < time.time():
            remove((directory_path() + 'logs/messages/' + filename))
        else:
            result['msgs-saved'][filename] = saved
    for filename, saved in loginfo['status-saved'].items():
        if (saved + 2592000) < time.time():
            remove((directory_path() + 'logs/status/' + filename))
        else:
            result['status-saved'][filename] = saved
    fout.write(json.dumps(result))
    fout.close()
