from flask import Flask
from functions import load_json_file, dump_json_file

app = Flask(__name__)

def notify(key):
    loginfo = load_json_file("allowed_users.json")
    for admin in loginfo["op-3"].keys():
        loginfo["notify"][admin] = key
    dump_json_file("allowed_users.json", loginfo)

@app.route('/cam0detected')
def not0():
    notify("0")
    return "OK"

@app.route('/cam1detected')
def not1():
    notify("1")
    return "OK"

@app.route('/cam2detected')
def not2():
    notify("2")
    return "OK"

app.run(host="0.0.0.0", port=8889, threaded=True)
