import argparse
import calendar
import os
import time
import webbrowser

# noinspection PyPackageRequirements
import twitch.queries
# noinspection PyPackageRequirements
import twitch.api.v3

import windows_10_toast_notifications
from tests.one_offs import windows_lock_check

DEBUG_OUTPUT = False


script_path = os.path.dirname(os.path.abspath(__file__))
assets_path = os.path.join(script_path, "assets")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user",
                        required=True,
                        dest="username")
    parser.add_argument("--poll",
                        help="poll interval",
                        type=int,
                        default=60
                        )
    parser.add_argument("--all",
                        help="Watch all followed streams, not just ones with notifications enabled",
                        default=False,
                        action="store_true")
    parser.add_argument("--idle",
                        help="idle time threshold to consider locked (seconds)",
                        type=int,
                        default=300)
    parser.add_argument("--no-unlock-notify",
                        dest="unlock_notify",
                        help="Don't notify again on unlock",
                        default=True,
                        action="store_false")
    return parser.parse_args()


def time_desc(s):
    if s <= 120:
        return "%d s" % s
    elif s <= 60 * 60:
        return "%d min" % (s / 60)
    else:
        minutes = s / 60
        return "%d h %02d m" % (minutes / 60, minutes % 60)


def main():
    options = parse_args()

    username = options.username

    result = twitch.api.v3.follows.by_user(username)

    channels_followed = set()
    channel_info = {}
    last_streams = {}

    channels_followed_names = []

    for follow in result["follows"]:
        channel = follow["channel"]
        channel_id = channel["_id"]
        channel_name = channel["display_name"]

        notifications_enabled = follow["notifications"]
        if options.all or notifications_enabled:

            channels_followed.add(channel_id)
            channels_followed_names.append(channel_name)
            channel_info[channel_id] = channel

    print "Watching: %s" % ", ".join(sorted(channels_followed_names))

    windows_balloon_tip_obj = windows_10_toast_notifications.WindowsBalloonTip(window_title="twitch-notifier",
                                                                               icon_filename=os.path.join(assets_path, "icon.ico")
                                                                               )
    try:
        # Poll for twitch
        while True:
            locked = windows_lock_check.check_if_locked()
            idle = windows_lock_check.check_if_idle(threshold_s=options.idle)
            if DEBUG_OUTPUT:
                print "locked: %s idle: %s" % (locked, idle)
            if locked or idle:
                print "Locked, waiting for unlock"
                while windows_lock_check.check_if_locked() or windows_lock_check.check_if_idle(threshold_s=options.idle):
                    time.sleep(5)
                if options.unlock_notify:
                    if DEBUG_OUTPUT:
                        print "Clearing last streams to renotify"
                    last_streams = {}

            if DEBUG_OUTPUT:
                print "Checking for follow stream changes"
            for channel_id in channels_followed:

                channel_name = channel_info[channel_id]["display_name"]
                response = twitch.api.v3.streams.by_channel(channel_name)

                stream = response["stream"]

                if stream is not None and not stream["is_playlist"]:
                    stream_id = stream["_id"]
                    if last_streams.get(channel_id) != stream_id:
                        start_time = calendar.timegm(time.strptime(stream["created_at"], "%Y-%m-%dT%H:%M:%SZ"))
                        elapsed_s = time.time() - start_time

                        game = stream["game"]
                        stream_browser_link = stream["channel"]["url"]

                        message = u"%s is now live with %s (up %s)" % (channel_name, game, time_desc(elapsed_s))

                        def callback():
                            print "notification for %s clicked" % channel_name
                            webbrowser.open(stream_browser_link)

                        windows_balloon_tip_obj.balloon_tip("twitch-notifier", message.encode("utf-8"),
                                                            callback=callback)

                    last_streams[channel_id] = stream_id
                else:
                    last_streams[channel_id] = None

            if DEBUG_OUTPUT:
                print "Waiting %s s for next poll" % options.poll
            time.sleep(max(options.poll, 60))
    except (KeyboardInterrupt, Exception):
        windows_balloon_tip_obj.close()
        raise


if __name__ == "__main__":
    main()
