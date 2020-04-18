import time
import datetime
import json
from telegrambot import directory_path, wget_mcu

'''
This file will check every five minutes if PC state has changed. If so, logs will be written down.
'''

if __name__ == '__main__':
    updatepc()

def updatepc(from_bot = False):
    with open((directory_path() + 'logs_info.log'), 'r') as filein:
        loginfo = json.loads(filein)
    with open((directory_path() + loginfo['status-actual']), 'r') as filein:
        filein = filein.split('\n')
        lines = len(filein)
        latest = filein[lines - 1]
    result = wget_mcu('/status')
    if not(result in latest):
        if from_bot:
            result+= '[Requested by Telegram bot]'
        if lines < 100:
            with open((directory_path() + loginfo['status-actual']), 'a') as filein:
                filein.write('\n' + str(datetime.datetime.now()) + result)
        else:
            result = loginfo
            result['status-saved'][loginfo['status-actual']] = time.time()
            newfile = 'logs/status/' + str(int(time.time())) + '.log'
            result['status-actual'] = newfile
            fout = open((directory_path() +'logs_info.json'), 'w')
            fout.write(json.dumps(result))
            fout.close()
            with open((directory_path() + newfile), 'w') as filein:
                filein.write(str(datetime.datetime.now()) + result)