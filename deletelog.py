#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import remove
from pathlib import Path
from json import loads, dumps
from time import time

"""
This file will delete old logs that have more than 30 days since they have been saved.
This script will run every day at 5am.
"""

def remove_old():
    directory_path = str(Path(__file__).parent.absolute()) + "/"
    with open((directory_path +"logs_info.json"), "r") as filein:
        loginfo = loads(filein.read())
    result = {"msgs-actual": loginfo["msgs-actual"], "status-actual" : loginfo["status-actual"], "msgs-saved" : {}, "status-saved" : {}}
    result = check_age(result, "msgs", "logs/messages/", loginfo)
    result = check_age(result, "status", "logs/status/", loginfo)
    fout = open((directory_path +"logs_info.json"), "w")
    fout.write(dumps(result))
    fout.close()

def check_age(result, log_name, log_path, loginfo):
    directory_path = str(Path(__file__).parent.absolute()) + "/"
    for filename, saved in loginfo[log_name + "-saved"].items():
        if (saved + 2592000) < time():
            remove((directory_path + log_path + filename))
        else:
            result[log_name + "-saved"][filename] = saved
    return result

if __name__ == "__main__":
    remove_old()
