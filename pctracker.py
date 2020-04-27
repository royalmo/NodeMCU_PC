#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functions import update_pc_log, wget_mcu, load_configs, log_work, get_logs_files
from pathlib import Path
from json import loads, dumps

'''
This file will check every five minutes if PC state has changed. If so, logs will be written down.
'''

if __name__ == '__main__':
    update_pc_log(False)
