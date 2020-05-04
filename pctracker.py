#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functions import update_pc_log

'''
This file will check every five minutes if PC state has changed. If so, logs will be written down.
'''

if __name__ == '__main__':
    update_pc_log()
