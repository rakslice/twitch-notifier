# twitch-notifier
A quick python twitch notifier for Windows 10

## Install

First you'll need [Python 2.7](https://www.python.org/downloads/release/python-2711/)

Then, to install the required libraries, run

    >c:\Python27\Scripts\pip.exe install -r requirements.txt

on the included requirements.txt file

## Usage

Run `twitch_notifier_main.py` and pass it at least the username to watch the follows of.

Use `notifiergui\notifier_gui_main.py` instead for a wxPython-based GUI (requires that you also install [wxPython 3.0 for Python 2.7](https://wxpython.org/download.php#msw), uses the same options)

## Options

    c:\Python27\python.exe twitch_notifier_main.py --username USERNAME [--poll INTERVAL] [--idle INTERVAL] [--all] [--no-unlock-notify] [--auth-oauth TOKEN]

    --user USERNAME  - Twitch user to watch followed users of
    --poll INTERVAL  - Time between polls in seconds; can't go lower than 60
    --idle INTERVAL  - How much time in seconds without activity to go idle
    --all            - Watch all followed streams, not just ones with notifications enabled
    --no-unlock-notify   - Don't notify again on unlock and when we return from idle
    --auth-oauth TOKEN   - OAuth token to pass

## Acknowledgments

Windows 10 notifications based on [https://github.com/jithurjacob/Windows-10-Toast-Notifications](https://github.com/jithurjacob/Windows-10-Toast-Notifications),

Twitch API via python-twitch ([https://github.com/ingwinlu/python-twitch](https://github.com/ingwinlu/python-twitch))