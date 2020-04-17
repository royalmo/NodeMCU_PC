import time
import random
import datetime
import telepot
from telepot.loop import MessageLoop
from requests import get

"""
This script controls a Telegram bot, to make sure that it is possible to power on and off the ESP8266 module, and the PC that it is connected to.
Make sure to read and install correctly all things that are on the repository: https://github.com/royalmo/NodeMCU_PC
"""

def handle(msg):
    chat_id = msg['chat']['id']
    command = msg['text']

    print 'Got command: %s' % command

    if command == '/roll':
        bot.sendMessage(chat_id, random.randint(1,6))
    elif command == '/time':
        bot.sendMessage(chat_id, str(datetime.datetime.now()))

bot = telepot.Bot('*** INSERT TOKEN ***')

request = get('http://192.168.1.19/status')

MessageLoop(bot, handle).run_as_thread()
print 'I am listening ...'

while 1:
    time.sleep(10)
