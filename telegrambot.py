#!/usr/bin/env python
# -*- coding: utf-8 -*-

from time import strftime, localtime, sleep, time
from random import randint
from datetime import datetime
import telepot
from telepot.loop import MessageLoop
from requests import get
from json import loads, dumps
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
- 2: Asked action (status or start), waiting for password.
"""

def load_configs():
    global bot
    global directory_path
    global nodemcu_ip
    global msg_path
    global json_answers
    global json_commands
    directory_path = getcwd() + "/"
    with open((directory_path + "config.json"), "r") as filein:
        configlog = loads(filein.read())
    nodemcu_ip = "http://"
    for element in configlog["nodemcu-ip"]:
        nodemcu_ip += str(element) + "."
    nodemcu_ip = nodemcu_ip[0:-1]
    if configlog["nodemcu-port"] != 80:
        nodemcu_ip += ":" + str(configlog["nodemcu-port"])
    bot = telepot.Bot(configlog["telegram-token"])
    msg_path = directory_path + "lang-" + configlog["main-language"] + ".json"
    with open(msg_path, "r") as filein:
        json_file = loads(filein.read())
        json_answers = json_file["answers"]
        json_commands = json_file["commands"]

def handle(msg):
    global bot
    global json_answers
    chat_id = msg["chat"]["id"]
    message = msg["text"].replace("\n", " |n ")
    date = strftime("%Y-%m-%d %H:%M:%S", localtime(msg["date"]))
    insertonlog(date, chat_id, message)
    op, status = get_user_info(chat_id)
    if status == 0: #IF AWAITING FOR PASSWORD
        if op == 0: #NEW USER
            bot.sendMessage(chat_id, json_answers["first-time-msg"])
            add_user(chat_id, 1)
            bot.sendMessage(chat_id, json_answers["hello-op1"])
        elif does_it_contain(message, "hello-cmds"):
            bot.sendMessage(chat_id, json_answers["hello-op" + str(op)])
        elif does_it_contain(message, "help-cmds"):
            bot.sendMessage(chat_id, json_answers["help-msg"])
        elif does_it_contain(message, "login-cmds"):
            bot.sendMessage(chat_id, json_answers["login-op" + str(op)])
            if op == 1:
                update_user_status(chat_id, 1, 1)
        elif does_it_contain(message, "logout-cmds"):
            bot.sendMessage(chat_id, json_answers["logout-op" + str(op)])
            if op == 2:
                update_user_op(chat_id, 2, 1)
        elif does_it_contain(message, "pcstatus-cmds"):
            bot.sendMessage(chat_id, json_answers["pcstatus-op" + str(op) + "-received"])
            if op != 1:
                bot.sendMessage(chat_id, send_status())
            else:
                update_user_status(chat_id, 1, 2)
        elif does_it_contain(message, "pcstart-cmds") and op != 1:
            bot.sendMessage(chat_id, json_answers["pcstart-op" + str(op) + "-received"])
            if op == 3:
                bot.sendMessage(chat_id, json_answers[action_pc("start", op)])
            else:
                update_user_status(chat_id, 2, 2)
        elif does_it_contain(message, "pcshutdown-cmds") and op == 3:
            bot.sendMessage(chat_id, json_answers["pcshutdown-op3-received"])
            bot.sendMessage(chat_id, json_answers[action_pc()])
        else:
            bot.sendMessage(chat_id, random_answer())
    else:
        if does_it_contain(message, "login-pwds") and status == 1:
            update_user_op(chat_id, 1, 2)
            op = 2
            bot.sendMessage(chat_id, json_answers["login-op1-pwd-done"])
        elif does_it_contain(message, "pcstatus-pwds") and op == 1 and status == 2:
            bot.sendMessage(chat_id, json_answers["pcstatus-op1-pwd-done"])
            bot.sendMessage(chat_id, send_status())
        elif does_it_contain(message, "pcstart-pwds") and op == 2 and status == 2:
            bot.sendMessage(chat_id, json_answers["pcstart-op2-pwd-done"])
            bot.sendMessage(chat_id, json_answers[action_pc("start", op)])
        else:
            bot.sendMessage(chat_id, json_answers["pwd-failed"])
        update_user_status(chat_id, op, 0)

def does_it_contain(message, command_code):
    global json_commands
    keywords = json_commands[command_code]
    for key in keywords:
        if key in message:
            return True
    return False

def send_status():
    global json_answers
    mcustatus = wget_mcu("/data")
    timestring = str(datetime.now())[0:-7].split(" ")
    msg_list = json_answers["pcstatus-answer-protocol"]
    answer = msg_list[0] + timestring[0] + msg_list[1] + timestring[1] + msg_list[2] + msg_list[int(mcustatus[0]) + 3]
    return (answer + msg_list[5] + mcustatus[1] + msg_list[int(mcustatus[1]) + 6])

def action_pc(action = "shutdown", op = 3):
    data = wget_mcu("/telegram" + action, True)[0]
    msg_code = "pc" + action + "-op" + str(op) + "-code" + data
    return (msg_code)

def random_answer():
    global json_answers
    randoms = json_answers["else-messages"]
    return randoms[randint(0, len(randoms)-1)]

def insertonlog(date, chat_id, message):
    global directory_path
    with open((directory_path + "logs_info.json"), "r") as filein:
        loginfo = loads(filein.read())
    with open((directory_path + loginfo["msgs-actual"]), "r") as filein:
        lines = len(filein.read().split("\n"))
    result ="[" + date + "] ChatID=" + str(chat_id) + " Message: " + message
    if lines < 100:
        with open((directory_path + loginfo["msgs-actual"]), "a") as filein:
            filein.write("\n" + result)
    else: #IF LOG FILE IS FULL (+100 lines) IT CREATES ANOTHER
        newlog = loginfo
        newlog["msgs-saved"][loginfo["msgs-actual"]] = time()
        newfile = "logs/messages/" + str(int(time())) + ".log"
        newlog["msgs-actual"] = newfile
        fout = open((directory_path +"logs_info.json"), "w")
        fout.write(dumps(newlog))
        fout.close()
        with open((directory_path + newfile), "w") as filein:
            filein.write(result)

def wget_mcu(extension, update = False): #This function returns the content of a webpage (and does included actions).
    global nodemcu_ip
    result = get(nodemcu_ip + extension).content.decode("utf-8").split("\n")
    if update:
        updatepc(True, result[1])
    return result[0]

def get_user_info(chat_id): #This function returns op level of user, and previous status.
    global directory_path
    with open((directory_path + "allowed_users.json"), "r") as filein:
        users = loads(filein.read())
    for op_level in users:
        if str(chat_id) in users[op_level]:
            return [int(op_level[3]), users[op_level][str(chat_id)]]
    return [0, 0]

def update_user_op(chat_id, oldop, newop):
    global directory_path
    with open((directory_path + "allowed_users.json"), "r") as filein:
        users = loads(filein.read())
    users[("op-" + str(newop))][str(chat_id)] = users[("op-" + str(oldop))][str(chat_id)]
    users[("op-" + str(oldop))].pop(str(chat_id))
    fout = open((directory_path + "allowed_users.json"), "w")
    fout.write(dumps(users))
    fout.close()


def update_user_status(chat_id, op, newstatus):
    global directory_path
    with open((directory_path + "allowed_users.json"), "r") as filein:
        users = loads(filein.read())
    users[("op-" + str(op))][str(chat_id)] = newstatus
    fout = open((directory_path + "allowed_users.json"), "w")
    fout.write(dumps(users))
    fout.close()

def add_user(chat_id, op):
    global directory_path
    with open((directory_path + "allowed_users.json"), "r") as filein:
        users = loads(filein.read())
    users[("op-" + str(op))][str(chat_id)] = 0
    fout = open((directory_path + "allowed_users.json"), "w")
    fout.write(dumps(users))
    fout.close()

def updatepc(from_bot = True, data = -1):
    global directory_path
    with open((directory_path + "logs_info.json"), "r") as filein:
        loginfo = loads(filein.read())
    with open((directory_path + loginfo["status-actual"]), "r") as filein:
        filein = filein.read().split("\n")
        lines = len(filein)
        latest = filein[lines - 1]
    if data == -1:
        data = wget_mcu("/data")
    result = ">>> PC status: " + data[0] + " FAN status: " + data[1]
    if not(result in latest): #UPDATES LOG FILE IF NECESSARY
        if from_bot:
            result+= " [Requested by Telegram bot]"
        if lines < 100:
            with open((directory_path + loginfo["status-actual"]), "a") as filein:
                filein.write("\n" + str(datetime.now()) + result)
        else: #IF LOG FILE IS FULL (+100 lines) IT CREATES ANOTHER
            newlog = loginfo
            newlog["status-saved"][loginfo["status-actual"]] = time()
            newfile = "logs/status/" + str(int(time())) + ".log"
            newlog["status-actual"] = newfile
            fout = open((directory_path +"logs_info.json"), "w")
            fout.write(dumps(newlog))
            fout.close()
            with open((directory_path + newfile), "w") as filein:
                filein.write(str(datetime.now()) + result)

if __name__ == "__main__":
    global bot
    load_configs()
    MessageLoop(bot, handle).run_as_thread()
    while 1:
        sleep(10)
