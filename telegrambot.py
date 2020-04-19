#!/usr/bin/env python
import time
import random
import datetime
import telepot
from telepot.loop import MessageLoop
from requests import get
import json
from pctracker import updatepc

'''
This script controls a Telegram bot, to make sure that it is possible to power on and off the ESP8266 module, and the PC that it is connected to.
Make sure to read and install correctly all things that are on the repository: https://github.com/royalmo/NodeMCU_PC

OP LEVELS:
- OP3: GOD USER: You have to manually change the chat_id in the json file.
- OP2: LOGGED USER: They have logged in with the key. Can see PCstatus, but can't start it without password. They can log out.
- OP1: COMMON USER: They can see PCstatus with a password, and they can login with another password.
- OP0: NEW USER: Just prints a welcome message, and becomes a common user.

REQUEST STATUS:
- 0: No previous action requested.
- 1: Asked login, waiting for password.
- 2: Asked action, waiting for password.

QUICK NOTE: Messages will be in spanish, because of an intern joke, so you are free to change all messages and keywords! :)
'''

global node_mcu_ip = 'http://192.168.1.99' #INSERT NODEMCU STATIC IP
global bot = telepot.Bot('*** INSERT TOKEN ***') #INSERT YOUR TELEGRAM BOT TOKEN
global login_key = '****' #INSERT PASSWORD TO LOGIN
global action_key = '****' #INSERT PASSWORD TO GET STATUS WHEN LOGOUT OR TO START PC WHEN LOGIN

def directory_path():  #CHANGE DIRECTORY PATH IF NEEDED
    return '/home/pi/NodeMCU_PC/'

if __name__ == "__main__":
    global bot
    MessageLoop(bot, handle).run_as_thread()
    while 1:
        time.sleep(10)

def handle(msg): #THIS FUNCTION EXECUTES WHEN MESSAGE RECEIVED.
    chat_id = msg['chat']['id']
    message = msg['text'].replace('\n', ' |n ')
    date = msg['date']
    name = msg['chat']['first_name']
    insertonlog(date, chat_id, message) #SEND MESSAGE TO LOGS
    user_info = get_user_info(chat_id)
    op = user_info[0]
    status = user_info[1]


    wget_mcu('/start')

    if message == '/start' or 'teniente' in message:
        bot.sendMessage(chat_id, "Muy buenas, ¿con quién estoy hablando?")

    elif command == '/time':
        bot.sendMessage(chat_id, str(datetime.datetime.now()))
        random.randint(1,6)

    # update_user_op(chat_id, oldop, newop)
    # update_user_status(chat_id, op, newstatus)

#public commands: /start /stop /help
#private keywords: panorama ascenso ejecuta paralo todo

#END MAIN FUNCTION


def insertonlog(date, chat_id, message):
    with open((directory_path() + 'logs_info.log'), 'r') as filein:
        loginfo = json.loads(filein)
    with open((directory_path() + loginfo['msgs-actual']), 'r') as filein:
        lines = len(filein.split('\n'))
    result = str(date) + '> ChatID: ' + str(chat_id) + '> Message: ' + message
    if lines < 100:
        with open((directory_path() + loginfo['msgs-actual']), 'a') as filein:
            filein.write(result)
    else: #IF LOG FILE IS FULL (+100 lines) IT CREATES ANOTHER
        newlog = loginfo
        newlog['msgs-saved'][loginfo['msgs-actual']] = time.time()
        newfile = 'logs/messages/' + str(int(time.time())) + '.log'
        newlog['msgs-actual'] = newfile
        fout = open((directory_path() +'logs_info.json'), 'w')
        fout.write(json.dumps(newlog))
        fout.close()
        with open((directory_path() + newfile), 'w') as filein:
            filein.write(result)

def wget_mcu(extension): #This function returns the content of a webpage (and does included actions).
    global node_mcu_ip
    result = get(node_mcu_ip + extension).content
    time.sleep(10)
    if extension != '/status':
        updatepc()
    return result

def get_user_info(chat_id): #This function returns op level of user, and previous status.
    with open((directory_path() + 'allowed_users.json'), 'r') as filein:
        users = json.loads(filein)
    for op_level in users:
        if chat_id in users[op_level]:
            return [int(op_level[3]), users[op_level][chat_id]]
    return [0, 0]

def update_user_op(chat_id, oldop, newop):
    with open((directory_path() + 'allowed_users.json'), 'r') as filein:
        users = json.loads(filein)
    users[('op-' + str(newop))][chat_id] = users[('op-' + str(oldop))][chat_id]
    users[('op-' + str(oldop))].pop(chat_id)
    fout = open((directory_path() + 'allowed_users.json'), 'w')
    fout.write(json.dumps(users))
    fout.close()


def update_user_status(chat_id, op, newstatus):
    with open((directory_path() + 'allowed_users.json'), 'r') as filein:
        users = json.loads(filein)
    users[('op-' + str(op))][chat_id] = newstatus
    fout = open((directory_path() + 'allowed_users.json'), 'w')
    fout.write(json.dumps(users))
    fout.close()
