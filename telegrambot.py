#!/usr/bin/env python
# -*- coding: utf-8 -*-

from time import strftime, localtime, sleep
from datetime import datetime
import telepot
from telepot.loop import MessageLoop
from functions import insert_on_log, TelegramUser, does_it_contain, send_status, load_json_file, dump_json_file, send_status, action_pc, random_answer, save_last_img, take_snapshot, get_path, get_notification_status, set_notification_status

from playback import PlayListHandler

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
    global json_commands
    chat_id = msg["chat"]["id"]
    message = msg["text"].replace("\n", " |n ")
    date = strftime("%Y-%m-%d %H:%M:%S", localtime(msg["date"]))
    insert_on_log(date, chat_id, message)
    user = TelegramUser(str(chat_id))
    if user.status == "0": #IF NOT AWAITING FOR PASSWORD
        if user.op == "0": #NEW USER
            bot.sendMessage(chat_id, json_answers["first-time-msg"])
            bot.sendMessage(chat_id, json_answers["hello-op1"])
        elif does_it_contain(message, "hello-cmds", json_commands):
            bot.sendMessage(chat_id, json_answers["hello-op" + user.op])
        elif does_it_contain(message, "help-cmds", json_commands):
            bot.sendMessage(chat_id, json_answers["help-msg"])
        elif does_it_contain(message, "login-cmds", json_commands):
            bot.sendMessage(chat_id, json_answers["login-op" + user.op])
            if user.op == "1":
                user.update_status("1")
        elif does_it_contain(message, "logout-cmds", json_commands):
            bot.sendMessage(chat_id, json_answers["logout-op" + user.op])
            if user.op == "2":
                user.update_op("1")
        elif does_it_contain(message, "pcstatus-cmds", json_commands):
            bot.sendMessage(chat_id, json_answers["pcstatus-op" + user.op + "-received"])
            if user.op != "1":
                bot.sendMessage(chat_id, send_status(json_answers))
            else:
                user.update_status("2")
        elif does_it_contain(message, "pcstart-cmds", json_commands) and user.op != "1":
            bot.sendMessage(chat_id, json_answers["pcstart-op" + user.op + "-received"])
            if user.op == "3":
                bot.sendMessage(chat_id, json_answers[action_pc("start", user.op)])
            else:
                user.update_status("2")
        elif does_it_contain(message, "pcshutdown-cmds", json_commands) and user.op == "3":
            bot.sendMessage(chat_id, json_answers["pcshutdown-op3-received"])
            bot.sendMessage(chat_id, json_answers[action_pc()])
        elif does_it_contain(message, "camera-entry-cmds", json_commands) and user.op != "1":
            bot.sendMessage(chat_id, json_answers["camera-response"])
            try:
                take_snapshot(bot, chat_id, 0)
            except:
                bot.sendMessage(chat_id, json_answers["camera-error"])
        elif does_it_contain(message, "camera-rout1-cmds", json_commands) and user.op != "1":
            bot.sendMessage(chat_id, json_answers["camera-response"])
            try:
                take_snapshot(bot, chat_id, 1)
            except:
                bot.sendMessage(chat_id, json_answers["camera-error"])
        elif does_it_contain(message, "camera-rout2-cmds", json_commands) and user.op != "1":
            bot.sendMessage(chat_id, json_answers["camera-response"])
            try:
                take_snapshot(bot, chat_id, 2)
            except:
                bot.sendMessage(chat_id, json_answers["camera-error"])
        elif does_it_contain(message, "camera-last-img-cmds", json_commands) and user.op != "1":
            bot.sendMessage(chat_id, json_answers["camera-last-img-response"])
            try:
                take_snapshot(bot, chat_id, -1)
            except:
                bot.sendMessage(chat_id, json_answers["camera-error"])
        elif does_it_contain(message, "save-last-img-cmds", json_commands) and user.op != "1":
            try:
                save_last_img(date.replace(" ", "_"))
            except:
                bot.sendMessage(chat_id, json_answers["camera-error"])
            else:
                bot.sendMessage(chat_id, json_answers["save-photo"])

        # Playlist stuff
        elif does_it_contain(message, "playlist-list-cmds", json_commands):
            bot.sendMessage(chat_id, json_answers["playlist-list-header"].format(
                "".join([ json_answers["playlist-list-line"].format(
                    "ON" if ans[1] else "OFF", ans[0], json_answers["playlist-list-playing"] if ans[2] else ""
                ) for ans in ph.get_playlists_info()])
            ), parse_mode="Markdown")
            
        elif does_it_contain(message, "playlist-get-info-cmds", json_commands):
            pl_id = message.split()[-1]
            if not ph.id_exists(pl_id):
                bot.sendMessage(chat_id, json_answers["playlist-info-fail"])
            else:
                pl_info = ph.get_info_of(pl_id)
                bot.sendMessage(chat_id, json_answers["playlist-info-msg"].format(
                    *pl_info
                ), parse_mode="Markdown")

        elif does_it_contain(message, "playlist-new-cmds", json_commands) and user.op == "3":
            if len(message.split()) != 8:
                bot.sendMessage(chat_id, json_answers["playlist-created-fail"])
            else:
                pl_id, pl_folder, pl_date1, pl_date2, pl_duration, pl_repeat = message.split()[2:]
                try:
                    pl_year, pl_month, pl_day = [int(x) for x in pl_date1.split("/")]
                    pl_hour, pl_min, pl_sec = [int(x) for x in pl_date2.split(":")]
                    pl_start = datetime(pl_year, pl_month, pl_day, pl_hour, pl_min, pl_sec).timestamp()

                    pl_end = pl_start + (float(pl_duration)*3600)
                    pl_repeat = float(pl_repeat)*3600

                    assert not ph.id_exists(pl_id)
                except:
                    bot.sendMessage(chat_id, json_answers["playlist-created-fail"])
                else:
                    ph.new_playlist(pl_id, pl_folder, pl_start, pl_end, pl_repeat)
                    bot.sendMessage(chat_id, json_answers["playlist-created-success"])

        elif does_it_contain(message, "playlist-edit-cmds", json_commands) and user.op == "3":
            if len(message.split()) != 8:
                bot.sendMessage(chat_id, json_answers["playlist-edited-fail"])
            else:
                pl_id, pl_folder, pl_date1, pl_date2, pl_duration, pl_repeat = message.split()[2:]
                try:
                    pl_year, pl_month, pl_day = [int(x) for x in pl_date1.split("/")]
                    pl_hour, pl_min, pl_sec = [int(x) for x in pl_date2.split(":")]
                    pl_start = datetime(pl_year, pl_month, pl_day, pl_hour, pl_min, pl_sec).timestamp()

                    pl_end = pl_start + (float(pl_duration)*3600)
                    pl_repeat = float(pl_repeat)*3600

                    assert ph.id_exists(pl_id)
                except:
                    bot.sendMessage(chat_id, json_answers["playlist-edited-fail"])
                else:
                    ph.edit_playlist(pl_id, pl_folder, pl_start, pl_end, pl_repeat)
                    bot.sendMessage(chat_id, json_answers["playlist-edited-success"])

        elif does_it_contain(message, "playlist-delete-cmds", json_commands) and user.op == "3":
            if not ph.id_exists(message.split()[-1]):
                bot.sendMessage(chat_id, json_answers["playlist-deleted-fail"])
            else:
                pl_id = message.split()[-1]
                ph.delete_playlist(pl_id)
                bot.sendMessage(chat_id, json_answers["playlist-deleted-success"])

        elif does_it_contain(message, "playlist-enable-cmds", json_commands) and user.op == "3":
            if not ph.id_exists(message.split()[-1]):
                bot.sendMessage(chat_id, json_answers["playlist-enable-disable-fail"])
            else:
                pl_id = message.split()[-1]
                ph.change_status_playlist(pl_id, enabled=True)
                bot.sendMessage(chat_id, json_answers["playlist-enable-success"])

        elif does_it_contain(message, "playlist-disable-cmds", json_commands) and user.op == "3":
            if not ph.id_exists(message.split()[-1]):
                bot.sendMessage(chat_id, json_answers["playlist-enable-disable-fail"])
            else:
                pl_id = message.split()[-1]
                ph.change_status_playlist(pl_id, enabled=False)
                bot.sendMessage(chat_id, json_answers["playlist-disable-success"])

        elif does_it_contain(message, "playlist-shuffle-cmds", json_commands) and user.op == "3":
            if not ph.id_exists(message.split()[-1]):
                bot.sendMessage(chat_id, json_answers["playlist-shuffle-fail"])
            else:
                pl_id = message.split()[-1]
                ph.shuffle_playlist(pl_id)
                bot.sendMessage(chat_id, json_answers["playlist-shuffle-success"])

        # Notification stuff
        elif does_it_contain(message, "notifications-status", json_commands) and user.op == "3":
            if get_notification_status():
                bot.sendMessage(chat_id, json_answers["notifications-enabled"])
            else:
                bot.sendMessage(chat_id, json_answers["notifications-disabled"])

        elif does_it_contain(message, "notifications-enable", json_commands) and user.op == "3":
            set_notification_status(True)
            bot.sendMessage(chat_id, json_answers["notifications-enabled"])

        elif does_it_contain(message, "notifications-disable", json_commands) and user.op == "3":
            set_notification_status(False)
            bot.sendMessage(chat_id, json_answers["notifications-disabled"])


        else:
            bot.sendMessage(chat_id, random_answer(json_answers))
    else:
        if does_it_contain(message, "login-pwds", json_commands) and user.status == "1":
            user.update_op("2")
            bot.sendMessage(chat_id, json_answers["login-op1-pwd-done"])
        elif does_it_contain(message, "pcstatus-pwds", json_commands) and user.op == "1" and user.status == "2":
            bot.sendMessage(chat_id, json_answers["pcstatus-op1-pwd-done"])
            bot.sendMessage(chat_id, send_status(json_answers))
        elif does_it_contain(message, "pcstart-pwds", json_commands) and user.op == "2" and user.status == "2":
            bot.sendMessage(chat_id, json_answers["pcstart-op2-pwd-done"])
            bot.sendMessage(chat_id, json_answers[action_pc("start", user.op)])
        else:
            bot.sendMessage(chat_id, json_answers["pwd-failed"])
        user.update_status("0")

def send_notifications():
    global bot
    global json_answers
    jsonfile = load_json_file("allowed_users.json")
    if get_notification_status():
        for user, notification in jsonfile["notify"].items():
            if len(notification) > 1:
                bot.sendMessage(user, json_answers["notification_pc"].format(json_answers["pc-stages"][int(notification[0])], notification[1]))
            elif notification in ["0", "1", "2"]:
                bot.sendMessage(user, json_answers["notification_cam"].format(json_answers["cams"][int(notification)]))
                take_snapshot(bot, user, int(notification))
    jsonfile["notify"] = {}
    dump_json_file("allowed_users.json", jsonfile)

## SATRTUP FUNCTION (well, better call it code than function)
if __name__ == "__main__":
    config_log = load_json_file("config.json")
    bot = telepot.Bot(config_log["telegram-token"])

    json_file = load_json_file("lang-" + config_log["main-language"] + ".json")
    json_answers = json_file["answers"]
    json_commands = json_file["commands"]

    ph = PlayListHandler( get_path() + "playlists.json" )
    ph.main_folder = config_log["music-folder"] + "/"

    #STARTS BOT, AND INFINITE LOOP TO KEEP IT RUNNING
    MessageLoop(bot, handle).run_as_thread()

    while True:
        for _ in range(10):
            sleep(1)
            ph.update()

        send_notifications()
        ph.save_playlists()
