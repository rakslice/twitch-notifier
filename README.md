# twitch-notifier
A quick python twitch notifier for Windows 10

## Install

First you'll need [Python 2.7](https://www.python.org/downloads/release/python-2711/)

For the version with the status GUI you'll need to install [wxPython 3.0 for Python 2.7](https://wxpython.org/download.php#msw)
(vintage 1990s stylin's!)

Then, to install the other required libraries, run

    >c:\Python27\Scripts\pip.exe install -r requirements.txt

on the included requirements.txt file

**This is primarily for Windows, but on Ubuntu (tested with 16.04.1) you can try:**

NB: No notifications working in Linux yet, just GUI 

	sudo apt install python-pip python-virtualenv python-wxpython python-wxgtk-webview3.0
	virtualenv ~/twitch-notifier-virtualenv
	~/twitch-notifier-virtualenv/bin/pip install -r requirements.txt
	LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libwx_gtk2u_webview-3.0.so ~/twitch-notifier-virtualenv/bin/python notifiergui/notifier_gui_main.py 

## Usage

For notifications and a status GUI, run `notifiergui\notifier_gui_main.py`.

For the old version with just the notificaions, run `twitch_notifier_main.py`.

Both of them use the same command line options (see below).

## Options

    c:\Python27\python.exe twitch_notifier_main.py --username USERNAME [--poll INTERVAL] [--idle INTERVAL] [--all] [--no-unlock-notify] [--auth-oauth TOKEN]

    --user USERNAME  - Twitch user to watch followed users of
    --poll INTERVAL  - Time between polls in seconds; can't go lower than 60
    --idle INTERVAL  - How much time in seconds without activity to go idle
    --all            - Watch all followed streams, not just ones with notifications enabled
    --no-unlock-notify   - Don't notify again on unlock and when we return from idle
    --auth-oauth TOKEN   - OAuth token to use (skips login)
    --no-browser-login   - Don't login -- just use the given token if any, or else the given username and public APIs 
    
## Acknowledgments

Windows 10 notifications for the non-GUI version based on [https://github.com/jithurjacob/Windows-10-Toast-Notifications](https://github.com/jithurjacob/Windows-10-Toast-Notifications),

Twitch API via python-twitch ([https://github.com/ingwinlu/python-twitch](https://github.com/ingwinlu/python-twitch))

GUI version uses [wxWidgets](https://www.wxwidgets.org/) / [wxPython](https://wxpython.org/), grequests, and appdirs
