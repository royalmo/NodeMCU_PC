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
    message = msg['text']
    date = msg['date']
    name = msg['chat']['first_name']

    #SEND MESSAGE TO LOGS
    print 'Got message: %s' % message

    if message == '/start' or 'teniente' in message:
        bot.sendMessage(chat_id, "Muy buenas, ¿con quién estoy hablando?")

    elif command == '/time':
        bot.sendMessage(chat_id, str(datetime.datetime.now()))
random.randint(1,6)

def wget_mcu(extension): #This function returns the content of a webpage (and does included actions).
    global node_mcu_ip
    return get(node_mcu_ip + extension).content

def get_user_info(chat_id): #This function returns op level of user, and previous status.
    with open('allowed_users.json', 'r') as filein:
        users = json.loads(filein)
    if chat_id in users['op-3']:
        return [3, ]
    return result;

time.time()
