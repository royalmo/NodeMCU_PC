#!/usr/bin/env python
import time
import random
import datetime
import telepot
from telepot.loop import MessageLoop
from requests import get
import json
#from pctracker import updatepc

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

node_mcu_ip = 'http://192.168.1.99' #INSERT NODEMCU STATIC IP
bot = telepot.Bot('') #INSERT YOUR TELEGRAM BOT TOKEN

def directory_path():  #CHANGE DIRECTORY PATH IF NEEDED
    #return '/home/pi/NodeMCU_PC/'
    return ''

def handle(msg): #THIS FUNCTION EXECUTES WHEN MESSAGE RECEIVED.
    global bot
    chat_id = msg['chat']['id']
    message = msg['text'].replace('\n', ' |n ')
    date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(msg['date']))
    insertonlog(date, chat_id, message) #SEND MESSAGE TO LOGS
    user_info = get_user_info(chat_id)
    op = user_info[0]
    status = user_info[1]
    if op == 0:
        bot.sendMessage(chat_id, 'Ostias! Hacia tiempo que no te veia, de hecho, nunca te he visto por aqui...')
        add_user(chat_id, 1)
        op = 1
    if message == '/start' or 'teniente' in message:
        if op == 1:
            bot.sendMessage(chat_id, 'Muy buenas, misero soldado.')
        elif op == 2:
            bot.sendMessage(chat_id, 'Muy buenas, compatriota.')
        else:
            bot.sendMessage(chat_id, 'Muy buenas, mi capitan. Que buen viento le trae aqui?')
    elif message == '/help' or 'aiuda' in message:
        bot.sendMessage(chat_id, 'Aver, como quieres que te ayuda desde una PC pocha? Ya eres suficientemente grande para pensar solito.')
    elif message == '/stop' or 'descenso' in message:
        if op == 1:
            bot.sendMessage(chat_id, 'Lo siento, pero no puedo descenderte mas de lo que ya estas, no quiero que te vayas con Julen :)')
        elif op == 2:
            bot.sendMessage(chat_id, 'Bueno, para descenderte no te lo voy a pedir dos veces, tampoco soy gilipollas... ahora eres un soldado de nuevo.')
            update_user_op(chat_id, 2, 1)
        else:
            bot.sendMessage(chat_id, 'Lo siento mi sen*or, pero no tengo los huevos suficientemente grandes para descenderte...')
    elif 'ascenso' in message:
        if op == 2:
            bot.sendMessage(chat_id, 'Lo siento, pero no puedes ascender mas, bienvenido a la hipocresia, my friend :)')
        elif op == 1:
            bot.sendMessage(chat_id, 'Bueno, no te voy a ascender tan facilmente, dame por lo menos una razon valida.')
            update_user_status(chat_id, 1, 1)
        else:
            bot.sendMessage(chat_id, 'Lo siento mi sen*or, pero no te puedo subir mas arriba que Espan*a...')
    elif 'aralo todo' in message and op == 3:
        data = wget_mcu('/data')
        if data[0] == 1 and data[1] == 0:
            bot.sendMessage(chat_id, 'A sus ordenes, mi capitan.')
            delay(10)
            if wget_mcu('/shutdown')[0] == 'D':
                bot.sendMessage(chat_id, 'Se a cumplido la mision con sumo exito.')
            else:
                bot.sendMessage(chat_id, 'Lo siento jefe, pero nos han hackeado la mision...')
        bot.sendMessage(chat_id, 'Lo siento jefe, pero nos han hackeado la mision...')
    elif 'jecuta' in message and op == 3:
        data = wget_mcu('/data')
        bot.sendMessage(chat_id, 'A sus ordenes, mi capitan.')
        if data[0] == 0 and data[1] != 2:
            delay(10)
            if wget_mcu('/start')[0] == 'D':
                bot.sendMessage(chat_id, 'Se a cumplido la mision con sumo exito.')
            else:
                bot.sendMessage(chat_id, 'Lo siento jefe, pero nos han hackeado la mision...')
        bot.sendMessage(chat_id, 'Lo siento jefe, pero nos han hackeado la mision...')
    elif 'jecuta' in message and op == 2:
        bot.sendMessage(chat_id, 'Aver, vale que seas mi compatriota, pero no lo voy a hacer sin un jamon 5J.')
        update_user_status(chat_id, 2, 2)
    elif 'bruh' in message and op == 2 and status == 2:
        update_user_status(chat_id, 2, 0)
        data = wget_mcu('/data')
        bot.sendMessage(chat_id, 'Suficiente, ahora lo hago.')
        if data[0] == 0 and data[1] != 2:
            delay(10)
            if wget_mcu('/start')[0] == 'D':
                bot.sendMessage(chat_id, 'Se a cumplido la mision con sumo exito.')
            else:
                bot.sendMessage(chat_id, 'Lo siento compatriota, pero nos han hackeado la mision...')
        bot.sendMessage(chat_id, 'Lo siento compatriota, pero nos han hackeado la mision...')
    elif 'panorama' in message and op != 1:
        bot.sendMessage(chat_id, 'Preguntandole al subdito delegado como esta el panorama.')
        mcustatus = wget_mcu('/data')
        if mcustatus[0] == '0':
            answer = ', you computer was off, and the fan switch state was on position number '
        else:
            answer = ', you computer was on, and the fan switch state was on position number '
        answer = answer + mcustatus[1] + '.'
        timestring = str(datetime.datetime.now())[0:-7].split(' ')
        bot.sendMessage(chat_id, ('Today, ' + timestring[0] + ' at ' + timestring[1] + answer))
    elif 'panorama' in message and op == 1:
        bot.sendMessage(chat_id, 'Dame una razon para que te pueda dar datos de la alta nobleza.')
        update_user_status(chat_id, 1, 2)
    elif 'eyeyey' in message and op == 1 and status == 1:
        update_user_op(chat_id, 1, 2)
        update_user_status(chat_id, 2, 0)
        bot.sendMessage(chat_id, 'Bueno, veo que te conoces mis bugs. Ascendido, cabron. Ahora eres mi compatriota :)')
    elif 'bitcoin' in message and op == 1 and status == 2:
        update_user_status(chat_id, 1, 0)
        bot.sendMessage(chat_id, 'Preguntandole al subdito delegado como esta el panorama.')
        mcustatus = wget_mcu('/data')
        if mcustatus[0] == '0':
            answer = ', you computer was off, and the fan switch state was on position number '
        else:
            answer = ', you computer was on, and the fan switch state was on position number '
        answer = answer + mcustatus[1] + '.'
        timestring = str(datetime.datetime.now())[0:-7].split(' ')
        bot.sendMessage(chat_id, ('Today, ' + timestring[0] + ' at ' + timestring[1] + answer))
    else:
        bot.sendMessage(chat_id, 'Lo siento, pero me llamo Osvaldo, no Alexa, y en consecuente no dispongo de infinitas respuestas para tus mierdas.')

def insertonlog(date, chat_id, message):
    with open((directory_path() + 'logs_info.json'), 'r') as filein:
        loginfo = json.loads(filein.read())
    with open((directory_path() + loginfo['msgs-actual']), 'r') as filein:
        lines = len(filein.read().split('\n'))
    result ='[' + date + '] ChatID=' + str(chat_id) + ' Message: ' + message
    if lines < 100:
        with open((directory_path() + loginfo['msgs-actual']), 'a') as filein:
            filein.write('\n' + result)
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
    if extension != '/status' or extension != '/data':
        updatepc()
    return result

def get_user_info(chat_id): #This function returns op level of user, and previous status.
    with open((directory_path() + 'allowed_users.json'), 'r') as filein:
        users = json.loads(filein.read())
    for op_level in users:
        if str(chat_id) in users[op_level]:
            return [int(op_level[3]), users[op_level][str(chat_id)]]
    return [0, 0]

def update_user_op(chat_id, oldop, newop):
    with open((directory_path() + 'allowed_users.json'), 'r') as filein:
        users = json.loads(filein.read())
    users[('op-' + str(newop))][str(chat_id)] = users[('op-' + str(oldop))][str(chat_id)]
    users[('op-' + str(oldop))].pop(str(chat_id))
    fout = open((directory_path() + 'allowed_users.json'), 'w')
    fout.write(json.dumps(users))
    fout.close()


def update_user_status(chat_id, op, newstatus):
    with open((directory_path() + 'allowed_users.json'), 'r') as filein:
        users = json.loads(filein.read())
    users[('op-' + str(op))][str(chat_id)] = newstatus
    fout = open((directory_path() + 'allowed_users.json'), 'w')
    fout.write(json.dumps(users))
    fout.close()

def add_user(chat_id, op):
    with open((directory_path() + 'allowed_users.json'), 'r') as filein:
        users = json.loads(filein.read())
    users[('op-' + str(op))][str(chat_id)] = 0
    fout = open((directory_path() + 'allowed_users.json'), 'w')
    fout.write(json.dumps(users))
    fout.close()

def updatepc(from_bot = True):
    with open((directory_path() + 'logs_info.log'), 'r') as filein:
        loginfo = json.loads(filein.read())
    with open((directory_path() + loginfo['status-actual']), 'r') as filein:
        filein = filein.read().split('\n')
        lines = len(filein)
        latest = filein[lines - 1]
    result = '>>> ' + wget_mcu('/status')[0:-1]
    if not(result in latest): #UPDATES LOG FILE IF NECESSARY
        if from_bot:
            result+= '[Requested by Telegram bot]'
        if lines < 100:
            with open((directory_path() + loginfo['status-actual']), 'a') as filein:
                filein.write('\n' + str(datetime.datetime.now()) + result)
        else: #IF LOG FILE IS FULL (+100 lines) IT CREATES ANOTHER
            newlog = loginfo
            newlog['status-saved'][loginfo['status-actual']] = time.time()
            newfile = 'logs/status/' + str(int(time.time())) + '.log'
            newlog['status-actual'] = newfile
            fout = open((directory_path() +'logs_info.json'), 'w')
            fout.write(json.dumps(newlog))
            fout.close()
            with open((directory_path() + newfile), 'w') as filein:
                filein.write(str(datetime.datetime.now()) + result)

if __name__ == '__main__':
    MessageLoop(bot, handle).run_as_thread()
    while 1:
        time.sleep(10)
