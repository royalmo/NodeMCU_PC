#!/usr/bin/env python
# -*- coding: utf-8 -*-

from time import strftime, localtime, sleep, time
from random import randint
from datetime import datetime
import telepot
from telepot.loop import MessageLoop
from requests import get
from json import loads, dumps
from pathlib import Path
from functions import *

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

## THIS FUNCTION MANAGES EVERY POSSIBLE ANSWER TO MESSAGES.

def handle(msg):
    global bot
    global json_answers
    chat_id = msg["chat"]["id"]
    message = msg["text"].replace("\n", " |n ")
    date = strftime("%Y-%m-%d %H:%M:%S", localtime(msg["date"]))
    insert_on_log(date, chat_id, message)
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

## SATRTUP FUNCTION (well, better call it code than function)
if __name__ == "__main__":
    directory_path = str(Path(__file__).parent.absolute()) + "/"
    config_log = load_configs()
    nodemcu_ip = load_mcu_ip(config_log)

    bot = telepot.Bot(config_log["telegram-token"])
    msg_path = directory_path + "lang-" + config_log["main-language"] + ".json"
    with open(msg_path, "r") as filein:
        json_file = loads(filein.read())
        json_answers = json_file["answers"]
        json_commands = json_file["commands"]

    #STARTS BOT, AND INFINITE LOOP TO KEEP IT RUNNING
    MessageLoop(bot, handle).run_as_thread()
    while 1:
        sleep(10)
