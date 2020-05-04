#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import remove
from time import time
from functions import load_json_file, dump_json_file, get_path

"""
This file will delete old logs that have more than 30 days since they have been saved.
This script will run every day at 5am.
"""

def remove_old():
    loginfo = load_json_file("logs_info.json")
    result = {"msgs-actual": loginfo["msgs-actual"], "status-actual" : loginfo["status-actual"], "msgs-saved" : {}, "status-saved" : {}}
    result = check_age(result, "msgs", "logs/messages/", loginfo)
    result = check_age(result, "status", "logs/status/", loginfo)
    dump_json_file("logs_info.json", result)

## THIS FUNCTION CLEANS THE LOGS, IT'S THE CORE OF THIS FILE.

def check_age(result, log_name, log_path, loginfo):
    directory_path = get_path()
    for filename, saved in loginfo[log_name + "-saved"].items():
        if (saved + 2592000) < time():
            remove((directory_path + log_path + filename))
        else:
            result[log_name + "-saved"][filename] = saved
    return result

if __name__ == "__main__":
    remove_old()
