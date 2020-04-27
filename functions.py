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

"""
This script contains most important functions for all python files that need some.
Be sure to read all instructions before modifying at https://github.com/royalmo/NodeMCU_PC
"""
## THIS FUNCTION LOAD ALL CONFIG_LOG SETTINGS, AND ALSO LANGUAGE SETTINGS AND DATA.

def load_configs():
    directory_path = str(Path(__file__).parent.absolute()) + "/"
    with open((directory_path + "config.json"), "r") as filein:
        config_log = loads(filein.read())
    return config_log

def load_mcu_ip(config_log):
    nodemcu_ip = "http://"
    for element in config_log["nodemcu-ip"]:
        nodemcu_ip += str(element) + "."
    nodemcu_ip = nodemcu_ip[0:-1]
    if config_log["nodemcu-port"] != 80:
        nodemcu_ip += ":" + str(config_log["nodemcu-port"])
    return nodemcu_ip

## THIS FUNCTION MANAGES ALL MCU REQUESTS, AND UPDATES IF NECESSARY

def wget_mcu(extension, update = False):
    nodemcu_ip = load_mcu_ip(load_configs())
    result = get(nodemcu_ip + extension).content.decode("utf-8").split("\n")
    if update:
        update_pc_log(True, result[1])
    return result[0]

## THESE 2 FUNCTIONS GETS INFO FROM MCU (by previous function) AND DO ACTIONS
## OR MANAGE ANSWERS IF NECESSARY.

def send_status(json_answers):
    mcustatus = wget_mcu("/data")
    timestring = str(datetime.now())[0:-7].split(" ")
    msg_list = json_answers["pcstatus-answer-protocol"]
    answer = msg_list[0] + timestring[0] + msg_list[1] + timestring[1] + msg_list[2] + msg_list[int(mcustatus[0]) + 3]
    return (answer + msg_list[5] + mcustatus[1] + msg_list[int(mcustatus[1]) + 6])

def action_pc(action = "shutdown", op = 3):
    data = wget_mcu("/telegram" + action, True)[0]
    msg_code = "pc" + action + "-op" + str(op) + "-code" + data
    return (msg_code)

## THIS FUNCTION PUTS PC STATUS ONTO LOGFILE

def update_pc_log(from_bot = True, data = -1):
    loginfo, logfile = get_logs_files("status")
    lines = len(logfile)
    latest = logfile[lines - 1]
    if data == -1:
        data = wget_mcu("/data")
    result = str(datetime.now())[0:-7] + " >>> PCstatus=" + data[0] + " FANstatus=" + data[1]
    if not(result in latest): #UPDATES LOG FILE IF NECESSARY
        if from_bot:
            result+= " [Requested by Telegram bot]"
        log_work("status", "status", loginfo, result, lines)

## THIS FUNCTION PUTS EVERY MESSAGE ON THE LOGFILE, INCLUDING DATETIME AND USER_ID

def insert_on_log(date, chat_id, message):
    loginfo, logfile = get_logs_files("msgs")
    lines = len(logfile)
    directory_path = str(Path(__file__).parent.absolute()) + "/"
    with open((directory_path + "logs_info.json"), "r") as filein:
        loginfo = loads(filein.read())
    with open((directory_path + loginfo["msgs-actual"]), "r") as filein:
        lines = len(filein.read().split("\n"))
    result ="[" + date + "] ChatID=" + str(chat_id) + " Message: " + message
    log_work("msgs", "messages", loginfo, result, lines)

## THIS TWO NEXT FUNCTIONS PREVENT REPEATING LINES ON THE TWO PREVIOUS FUNCTIONS

def log_work(log_name, log_path, old_log, result, lines):
    directory_path = str(Path(__file__).parent.absolute()) + "/"
    if lines < 100:
        with open((directory_path + old_log[log_name + "-actual"]), "a") as filein:
            filein.write("\n" + result)
    else: #IF LOG FILE IS FULL (+100 lines) IT CREATES ANOTHER
        full_log = old_log
        full_log[log_name + "-saved"][old_log[log_name + "-actual"]] = time()
        newfile = "logs/" + log_path + "/" + str(int(time())) + ".log"
        full_log[log_name + "-actual"] = newfile
        fout = open((directory_path +"logs_info.json"), "w")
        fout.write(dumps(full_log))
        fout.close()
        with open((directory_path + newfile), "w") as filein:
            filein.write(result)

def get_logs_files(type):
    directory_path = str(Path(__file__).parent.absolute()) + "/"
    with open((directory_path + "logs_info.json"), "r") as filein:
        loginfo = loads(filein.read())
    with open((directory_path + loginfo[type + "-actual"]), "r") as filein:
        logfile = filein.read().split("\n")
    return [loginfo, logfile]

## THIS FUCNTION IS LIKE AN ADVANCED 'IN' CONDITIONAL
## IT RETURNS IF SENTENCE IS IN GROUP OF COMMANDS, EVEN PARTIALLY

def does_it_contain(message, command_code, json_commands):
    keywords = json_commands[command_code]
    for key in keywords:
        if key in message:
            return True
    return False

## THESE 4 FUNCTIONS MANAGE USER SETTINGS, AND ARE REQEUSTED BY HANDLE

def get_user_info(chat_id):
    directory_path = str(Path(__file__).parent.absolute()) + "/"
    with open((directory_path + "allowed_users.json"), "r") as filein:
        users = loads(filein.read())
    for op_level in users:
        if str(chat_id) in users[op_level]:
            return [int(op_level[3]), users[op_level][str(chat_id)]]
    return [0, 0]

def update_user_op(chat_id, oldop, newop):
    directory_path = str(Path(__file__).parent.absolute()) + "/"
    with open((directory_path + "allowed_users.json"), "r") as filein:
        users = loads(filein.read())
    users[("op-" + str(newop))][str(chat_id)] = users[("op-" + str(oldop))][str(chat_id)]
    users[("op-" + str(oldop))].pop(str(chat_id))
    fout = open((directory_path + "allowed_users.json"), "w")
    fout.write(dumps(users))
    fout.close()

def update_user_status(chat_id, op, newstatus):
    directory_path = str(Path(__file__).parent.absolute()) + "/"
    with open((directory_path + "allowed_users.json"), "r") as filein:
        users = loads(filein.read())
    users[("op-" + str(op))][str(chat_id)] = newstatus
    fout = open((directory_path + "allowed_users.json"), "w")
    fout.write(dumps(users))
    fout.close()

def add_user(chat_id, op):
    directory_path = str(Path(__file__).parent.absolute()) + "/"
    with open((directory_path + "allowed_users.json"), "r") as filein:
        users = loads(filein.read())
    users[("op-" + str(op))][str(chat_id)] = 0
    fout = open((directory_path + "allowed_users.json"), "w")
    fout.write(dumps(users))
    fout.close()

## THIS FUNCTION RETURNS RANDOM SENTENCES FROM A LIST, FUTURE A.I., MAYBE?

def random_answer(json_answers):
    randoms = json_answers["else-messages"]
    return randoms[randint(0, len(randoms)-1)]
