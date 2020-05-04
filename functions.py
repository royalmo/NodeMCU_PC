#!/usr/bin/env python
# -*- coding: utf-8 -*-

from time import strftime, localtime, sleep, time
from random import randint
from datetime import datetime
from requests import get
from json import loads, dumps
from pathlib import Path

"""
This script contains most important functions for all python files that need some.
Be sure to read all instructions before modifying at https://github.com/royalmo/NodeMCU_PC
"""
## THIS FUNCTION BUILDS THE NODEMCU's IP.

def load_mcu_ip(config_log):
    nodemcu_ip = "http://"
    for element in config_log["nodemcu-ip"]:
        nodemcu_ip += str(element) + "."
    nodemcu_ip = nodemcu_ip[0:-1]
    if config_log["nodemcu-port"] != 80:
        nodemcu_ip += ":" + str(config_log["nodemcu-port"])
    return nodemcu_ip

## SIMPLE FUNCTION THAT RETURNS DIRECTORY PATH

def get_path():
    return str(Path(__file__).parent.absolute()) + "/"

## FUNCTIONS TO LOAD AND DUMP JSON FILES

def load_json_file(file_path):
    with open((get_path() + file_path), "r") as filein:
        return_log = loads(filein.read())
    return return_log

def dump_json_file(file_path, json_file):
    with open((get_path() + file_path), "w") as fileout:
        fileout.write(dumps(json_file))

## THIS FUNCTION MANAGES ALL MCU REQUESTS, AND UPDATES IF NECESSARY

def wget_mcu(extension, update = False):
    nodemcu_ip = load_mcu_ip(load_json_file("config.json"))
    try:
        result = get(nodemcu_ip + extension).content.decode("utf-8").split("\n")
    except:
        return "Got error"
    if update:
        update_pc_log(True, result[1])
    return result[0]

## THESE 2 FUNCTIONS GETS INFO FROM MCU (by previous function) AND DO ACTIONS
## OR MANAGE ANSWERS IF NECESSARY.

def send_status(json_answers):
    mcustatus = wget_mcu("/data")
    if mcustatus == "Got error":
        return json_answers["connection-error"]
    timestring = str(datetime.now())[0:-7].split(" ").append(json_answers["pc-stages"][int(mcustatus[0])])
    return json_answers["pcstatus-answer"][0].format(timestring.append(json_answers["pcstatus-answer"][int(mcustatus[1]) + 1]))

def action_pc(action = "shutdown", op = 3):
    data = wget_mcu("/telegram" + action, True).split("\n")
    if data[0] == "Got error":
        return "connection-error"
    if op != 3:
        program_notification(data[1])
    msg_code = "pc" + action + "-op" + str(op) + "-code" + data[0][0]
    return msg_code

## THIS FUNCTION PUTS PC STATUS ONTO LOGFILE

def update_pc_log(from_bot = False, data = -1):
    loginfo, logfile = get_logs_files("status")
    lines = len(logfile)
    latest = get_latest_line(logfile)
    if data == -1:
        data = wget_mcu("/data")
        if data == "Got error":
            data = "EE"
    result = " >>> PCstatus=" + data[0] + " FANstatus=" + data[1]
    if not(result in latest): #UPDATES LOG FILE IF NECESSARY
        if from_bot:
            result = result + " [Requested by Telegram bot]"
        elif latest[33] == "S": #2020-05-01 12:10:02 >>> PCstatus=S FANstatus=1 CHECKS IF PCSTATUS IS 'S'
            result = result + " [Confirmed shutdown]"
        elif data != "EE":
            program_notification(data)
        result = str(datetime.now())[0:-7] + result
        log_work("status", "status", loginfo, result, lines)

## THIS FUNCTION GETS THE LATEST NON-ERROR LOG LINE

def get_latest_line(logfile):
    i = len(logfile)
    while i > 0:
        i -= 1
        if not " >>> PCstatus=E FANstatus=E" in logfile[i]:
            return logfile[i]
    return logfile[0]

## THIS FUNCTION PUTS EVERY MESSAGE ON THE LOGFILE, INCLUDING DATETIME AND USER_ID

def insert_on_log(date, chat_id, message):
    loginfo, logfile = get_logs_files("msgs")
    lines = len(logfile)
    result ="[" + date + "] ChatID=" + str(chat_id) + " Message: " + message
    log_work("msgs", "messages", loginfo, result, lines)

## THIS TWO NEXT FUNCTIONS PREVENT REPEATING LINES ON THE TWO PREVIOUS FUNCTIONS

def log_work(log_name, log_path, old_log, result, lines):
    if lines < 100:
        with open((get_path() + old_log[log_name + "-actual"]), "a") as filein:
            filein.write("\n" + result)
    else: #IF LOG FILE IS FULL (+100 lines) IT CREATES ANOTHER
        full_log = old_log
        full_log[log_name + "-saved"][old_log[log_name + "-actual"]] = time()
        newfile = "logs/" + log_path + "/" + str(int(time())) + ".log"
        full_log[log_name + "-actual"] = newfile
        dump_json_file("logs_info.json", full_log)
        with open((get_path() + newfile), "w") as filein:
            filein.write(result)

def get_logs_files(type):
    loginfo = load_json_file("logs_info.json")
    with open((get_path() + loginfo[type + "-actual"]), "r") as filein:
        logfile = filein.read().split("\n")
    return [loginfo, logfile]

## THIS FUNCTION PREPARES A NOTIFICATION IN A JSON FILE, THEN TELEGRAMBOT.PY
## WILL SEND THOSE MESSAGES AS THIS FUNCTION CAN'T ACCESS TO BOT VARIABLE

def program_notification(data):
    loginfo = load_json_file("allowed_users.json")
    for admin in loginfo["op-3"].keys():
        loginfo["notify"][admin] = data
    dump_json_file("allowed_users.json", loginfo)

## THIS FUCNTION IS LIKE AN ADVANCED 'IN' CONDITIONAL
## IT RETURNS IF SENTENCE IS IN GROUP OF COMMANDS, EVEN PARTIALLY

def does_it_contain(message, command_code, json_commands):
    keywords = json_commands[command_code]
    for key in keywords:
        if key in message:
            return True
    return False

## THESE CLASS HANDLES ALL USER ACTIONS

class TelegramUser(object):
    """This class does all necessary actions to telegram users."""
    def __init__(self, id):
        super(TelegramUser, self).__init__()
        self.id = id
        userlist = load_json_file("allowed_users.json")
        self.op = 0
        self.status = 0
        for op_level in userlist:
            if str(self.id) in userlist[op_level]:
                self.op = int(op_level[3])
                self.status = userlist[op_level][str(self.id)]
        if self.op == 0:
            userlist["op-1"][self.id] = 0
            dump_json_file("allowed_users.json", userlist)
    def update_op(self, newop):
        userlist = load_json_file("allowed_users.json")
        userlist[("op-" + str(newop))][str(self.id)] = userlist[("op-" + str(self.op))][str(self.id)]
        userlist[("op-" + str(self.op))].pop(str(self.id))
        dump_json_file("allowed_users.json", userlist)
        self.op = newop
    def update_status(self, newstatus):
        userlist = load_json_file("allowed_users.json")
        userlist[("op-" + str(self.op))][str(self.id)] = newstatus
        dump_json_file("allowed_users.json", userlist)
        self.status = newstatus

## THIS FUNCTION RETURNS RANDOM SENTENCES FROM A LIST, FUTURE A.I., MAYBE?

def random_answer(json_answers):
    randoms = json_answers["else-messages"]
    return randoms[randint(0, len(randoms)-1)]
