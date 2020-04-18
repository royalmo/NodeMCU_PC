# NodeMCU_PC
Start, stop, plug and unplug your computer from a Telegram Bot!
With this code and the good components you can fully control your computer status from whatever you want.

## What do I need?
If you want to copy my design, you will need the following components:
* A computer to be controlled. It sounds obvious, but I put it to prevent useless issues! ;)
* A NodeMCU module, mainly the v1.0. The ESP8266 itself should also work, but I haven't tested it.
* A Raspberry Pi, with internet connection.
* A relay. In my case, i used an old non-working programmable plug, that just had a working relay inside, it was just the programmable part that was dead. Depending on your relay you may have to change some of the configurations.
* Some electronic components. To connect up the relay, or the PC buttons i used diodes, resistors and optocouplers (see wiring). You could replace the optocouplers for some transistors, it's up to you!
* Aaaaaaaaaaaand a Telegram account, sounds also obvious!

## How to install it?
You first need to make all the connections on the ESP8266 board, and copy the code with the arduino IDE and the ESP8266 library. Remember to change the network settings!

Then, just go to the Raspberry Board (with Raspbian and internet access) and download the whole repository. Remember to change the bot token and put yours in the python file, and the ip adress that you inserted on the NodeMCU board!
Then, install the libraries:
```
pip install telepot
```
Add the following command at the bottom of the file `/etc/rc.local` , before the `fi` command:
```
python /the/path/of/the/NodeMCU_PC/telegrambot.py &
```
That way, the bot will always be active when the raspberry is on. Now you just have to restart the raspberry in order to apply changes.

## How do I use it?
Just need to acces your telegram bot, with the codes that you introduced in you python file. If they are the same as mines, its just commands like /start, /status, and so on. If you don't have a Fan switch plugged into the NodeMCU you should remove that part of the code.

Have fun shutting down the computer when your little brother is playing skywars! And you can access that configuration from anywhere in the world! Amazing!
