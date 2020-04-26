#!/usr/bin/env python
import time
from random import randint
import datetime
import telepot
from telepot.loop import MessageLoop
from requests import get
import json
from os import getcwd

"""
This script controls a Telegram bot, to make sure that it is possible to power
on and off  the PC that it is connected to the ESP8266 module.
Make sure to read and install correctly all things that are on the repository:
https://github.com/royalmo/NodeMCU_PC

############################################################
## READ THIS INFO IF YOU ARE PLANNING TO CHANGE SOMETHING ##
############################################################

OP LEVELS:
- OP3: GOD USER: You have to manually change the chat_id in the json file.
- OP2: LOGGED USER: They have logged in with the key. Can see PCstatus, but can"t start it without password. They can log out.
- OP1: COMMON USER: They can see PCstatus with a password, and they can login with another password.
- OP0: NEW USER: Just prints a welcome message, and becomes a common user.

REQUEST STATUS:
- 0: No previous action requested.
- 1: Asked login, waiting for password.
- 2: Asked action, waiting for password.
"""

def load_configs():
    global bot
    global directory_path
    global nodemcu_ip
    global msg_path
    directory_path = getcwd()
    with open((directory_path + "/config.json"), "r") as filein:
        configlog = json.loads(filein.read())
    nodemcu_ip = "http://"
    for element in configlog["nodemcu-ip"]:
        nodemcu_ip += str(element) + "."
    nodemcu_ip = nodemcu_ip[0:-1]
    if configlog["nodemcu-port"] != 80:
        nodemcu_ip += ":" + str(configlog["nodemcu-port"])
    bot = telepot.Bot(configlog["telegram-token"])
    msg_path = directory_path + "/lang-" + configlog["main-language"] + ".json"

def get_msg(msg_code, is_list = False, list_element = -1):
    global msg_path
    with open(msg_path, "r") as filein:
        output = json.loads(filein.read())[msg_code]
    if not(is_list):
        return unicode(output, errors = "replace")
    if list_element != -1:
        return unicode(output[list_element], errors = "replace")
    result = []
    for element in output:
        result.append(unicode(element, errors = "replace"))
    return result


def handle(msg):
    global bot
    chat_id = msg["chat"]["id"]
    message = msg["text"].replace("\n", " |n ")
    date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(msg["date"]))
    insertonlog(date, chat_id, message)
    user_info = get_user_info(chat_id)
    op = user_info[0]
    status = user_info[1]
    if op == 0:
        bot.sendMessage(chat_id, get_msg("first-time-msg"))
        add_user(chat_id, 1)
        op = 1
    if message == "/start" or "teniente" in message:
        bot.sendMessage(chat_id, get_msg("hello-op" + str(op)))
    elif message == "/help" or "aiuda" in message:
        bot.sendMessage(chat_id, get_msg("help-msg"))
    elif message == "/stop" or "descenso" in message:
        bot.sendMessage(chat_id, get_msg("logout-op" + str(op)))
        if op == 2:
            update_user_op(chat_id, 2, 1)
    elif "ascenso" in message:
        bot.sendMessage(chat_id, get_msg("login-op" + str(op)))
        if op == 1:
            update_user_status(chat_id, 1, 1)
    elif "aralo todo" in message and op == 3:
        bot.sendMessage(chat_id, get_msg("pcstop-op3-received"))
        data = wget_mcu("/data")
        delay(10)
        if data[0] == 1 and data[1] == 0 and wget_mcu("/shutdown", True)[0] == "D":
            bot.sendMessage(chat_id, get_msg("pcstop-op3-success"))
        else:
            bot.sendMessage(chat_id, get_msg("pcstop-op3-fail"))
    elif "jecuta" in message and op == 3:
        bot.sendMessage(chat_id, get_msg("pcstart-op3-received"))
        data = wget_mcu("/data")
        delay(10)
        if data[0] == 0 and data[1] != 2 and wget_mcu("/start", True)[0] == "D":
            bot.sendMessage(chat_id, get_msg("pcstart-op3-success"))
        else:
            bot.sendMessage(chat_id, get_msg("pcstart-op3-fail"))
    elif "jecuta" in message and op == 2:
        bot.sendMessage(chat_id, get_msg("pcstart-op2-pwd-ask"))
        update_user_status(chat_id, 2, 2)
    elif "bruh" in message and op == 2 and status == 2:
        bot.sendMessage(chat_id, get_msg("pcstart-op2-pwd-done"))
        update_user_status(chat_id, 2, 0)
        data = wget_mcu("/data")
        delay(10)
        if data[0] == 0 and data[1] != 2 and wget_mcu("/start", True)[0] == "D":
            bot.sendMessage(chat_id, get_msg("pcstart-op2-success"))
        else:
            bot.sendMessage(chat_id, get_msg("pcstart-op2-fail"))
    elif "panorama" in message and op != 1:
        bot.sendMessage(chat_id, get_msg("pcstatus-op" + str(op) + "-received"))
        mcustatus = wget_mcu("/data")
        timestring = str(datetime.datetime.now())[0:-7].split(" ")
        msg_list = get_msg("pcstatus-answer-protocol", True)
        answer = msg_list[0] + timestring[0] + msg_list[1] + timestring[1] + msg_list[2] + msg_list[int(mcustatus[0]) + 3]
        bot.sendMessage(chat_id, (answer + msg_list[5] + mcustatus[1] + msg_list[int(mcustatus[1]) + 6]))
    elif "panorama" in message and op == 1:
        bot.sendMessage(chat_id, get_msg("pcstatus-op1-pwd-ask"))
        update_user_status(chat_id, 1, 2)
    elif "eyeyey" in message and op == 1 and status == 1:
        update_user_op(chat_id, 1, 2)
        update_user_status(chat_id, 2, 0)
        bot.sendMessage(chat_id, get_msg("login-op1-pwd-done"))
    elif "bitcoin" in message and op == 1 and status == 2:
        bot.sendMessage(chat_id, get_msg("pcstatus-op1-pwd-done"))
        mcustatus = wget_mcu("/data")
        timestring = str(datetime.datetime.now())[0:-7].split(" ")
        msg_list = get_msg("pcstatus-answer-protocol", True)
        answer = msg_list[0] + timestring[0] + msg_list[1] + timestring[1] + msg_list[2] + msg_list[int(mcustatus[0]) + 3]
        bot.sendMessage(chat_id, (answer + msg_list[5] + mcustatus[1] + msg_list[int(mcustatus[1]) + 6]))
    else:
        bot.sendMessage(chat_id, random_answer(message))

def random_answer(message):
    randoms = get_msg("else-messages", True)
    return randoms[randint(0, len(randoms))]

def insertonlog(date, chat_id, message):
    with open((directory_path() + "logs_info.json"), "r") as filein:
        loginfo = json.loads(filein.read())
    with open((directory_path() + loginfo["msgs-actual"]), "r") as filein:
        lines = len(filein.read().split("\n"))
    result ="[" + date + "] ChatID=" + str(chat_id) + " Message: " + message
    if lines < 100:
        with open((directory_path() + loginfo["msgs-actual"]), "a") as filein:
            filein.write("\n" + result)
    else: #IF LOG FILE IS FULL (+100 lines) IT CREATES ANOTHER
        newlog = loginfo
        newlog["msgs-saved"][loginfo["msgs-actual"]] = time.time()
        newfile = "logs/messages/" + str(int(time.time())) + ".log"
        newlog["msgs-actual"] = newfile
        fout = open((directory_path() +"logs_info.json"), "w")
        fout.write(json.dumps(newlog))
        fout.close()
        with open((directory_path() + newfile), "w") as filein:
            filein.write(result)

def wget_mcu(extension, update = False): #This function returns the content of a webpage (and does included actions).
    global nodemcu_ip
    result = get(nodemcu_ip + extension).content
    time.sleep(10)
    if update:
        updatepc()
    return result

def get_user_info(chat_id): #This function returns op level of user, and previous status.
    global directory_path
    with open((directory_path + "allowed_users.json"), "r") as filein:
        users = json.loads(filein.read())
    for op_level in users:
        if str(chat_id) in users[op_level]:
            return [int(op_level[3]), users[op_level][str(chat_id)]]
    return [0, 0]

def update_user_op(chat_id, oldop, newop):
    global directory_path
    with open((directory_path + "allowed_users.json"), "r") as filein:
        users = json.loads(filein.read())
    users[("op-" + str(newop))][str(chat_id)] = users[("op-" + str(oldop))][str(chat_id)]
    users[("op-" + str(oldop))].pop(str(chat_id))
    fout = open((directory_path + "allowed_users.json"), "w")
    fout.write(json.dumps(users))
    fout.close()


def update_user_status(chat_id, op, newstatus):
    global directory_path
    with open((directory_path + "allowed_users.json"), "r") as filein:
        users = json.loads(filein.read())
    users[("op-" + str(op))][str(chat_id)] = newstatus
    fout = open((directory_path + "allowed_users.json"), "w")
    fout.write(json.dumps(users))
    fout.close()

def add_user(chat_id, op):
    global directory_path
    with open((directory_path + "allowed_users.json"), "r") as filein:
        users = json.loads(filein.read())
    users[("op-" + str(op))][str(chat_id)] = 0
    fout = open((directory_path + "allowed_users.json"), "w")
    fout.write(json.dumps(users))
    fout.close()

def updatepc(from_bot = True):
    global directory_path
    with open((directory_path + "logs_info.json"), "r") as filein:
        loginfo = json.loads(filein.read())
    with open((directory_path + loginfo["status-actual"]), "r") as filein:
        filein = filein.read().split("\n")
        lines = len(filein)
        latest = filein[lines - 1]
    result = ">>> " + wget_mcu("/status")[0:-1]
    if not(result in latest): #UPDATES LOG FILE IF NECESSARY
        if from_bot:
            result+= "[Requested by Telegram bot]"
        if lines < 100:
            with open((directory_path + loginfo["status-actual"]), "a") as filein:
                filein.write("\n" + str(datetime.datetime.now()) + result)
        else: #IF LOG FILE IS FULL (+100 lines) IT CREATES ANOTHER
            newlog = loginfo
            newlog["status-saved"][loginfo["status-actual"]] = time.time()
            newfile = "logs/status/" + str(int(time.time())) + ".log"
            newlog["status-actual"] = newfile
            fout = open((directory_path +"logs_info.json"), "w")
            fout.write(json.dumps(newlog))
            fout.close()
            with open((directory_path + newfile), "w") as filein:
                filein.write(str(datetime.datetime.now()) + result)

if __name__ == "__main__":
    global bot
    load_configs()
    MessageLoop(bot, handle).run_as_thread()
    while 1:
        time.sleep(10)
