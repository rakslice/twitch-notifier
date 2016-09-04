import argparse
import calendar
import os
import time
import webbrowser

# noinspection PyPackageRequirements
import twitch.queries
# noinspection PyPackageRequirements
import twitch.api.v3
# noinspection PyPackageRequirements
import twitch.keys

import windows_10_toast_notifications
import windows_lock_check


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
    parser.add_argument("--debug",
                        dest="debug_output",
                        default=False,
                        action="store_true")
    parser.add_argument("--auth-oauth",
                        dest="authorization_oauth",
                        help="Authorization OAuth header value to send",
                        )
    return parser.parse_args()


def time_desc(s):
    if s <= 120:
        return "%d s" % s
    elif s <= 60 * 60:
        return "%d min" % (s / 60)
    else:
        minutes = s / 60
        return "%d h %02d m" % (minutes / 60, minutes % 60)


STREAM_TYPE_ALL = 'all'
STREAM_TYPE_PLAYLIST = 'playlist'
STREAM_TYPE_LIVE = 'live'


def twitch_streams_followed(stream_type, limit=25, offset=0):
    q = twitch.queries.V3Query('streams/followed')
    q.add_param(twitch.keys.LIMIT, limit, 25)
    q.add_param(twitch.keys.OFFSET, offset, 0)
    q.add_param('stream_type', stream_type)
    return q


def paged_query_iterator(func_to_page, results_list_key, page_size=25, **kwargs):
    cur_offset = 0
    while True:
        result_dict = func_to_page(limit=page_size, offset=cur_offset, **kwargs)
        total = result_dict["_total"]
        results_list_entries = result_dict[results_list_key]
        for entry in results_list_entries:
            yield entry
        if cur_offset + page_size >= total:
            break
        cur_offset += page_size


class TwitchNotifierMain(object):
    def __init__(self, options):
        self.options = options
        self.windows_balloon_tip_obj = None
        """:type: windows_10_toast_notifications.WindowsBalloonTip"""
        self.use_fast_query = False

    def _init_notifier(self):
        options = self.options
        windows_balloon_tip_obj = windows_10_toast_notifications.WindowsBalloonTip(window_title="twitch-notifier",
                                                                                   icon_filename=os.path.join(assets_path, "icon.ico"),
                                                                                   debug_output=options.debug_output
                                                                                   )
        self.windows_balloon_tip_obj = windows_balloon_tip_obj

    def _notifier_fini(self):
        self.windows_balloon_tip_obj.close()

    def notify_for_stream(self, channel_name, stream):
        start_time = calendar.timegm(time.strptime(stream["created_at"], "%Y-%m-%dT%H:%M:%SZ"))
        elapsed_s = time.time() - start_time

        game = stream["game"]
        stream_browser_link = stream["channel"]["url"]

        if game is None:
            show_info = ""
        else:
            show_info = u"with %s" % stream["game"]

        message = u"%s is now live %s(up %s)" % (channel_name, show_info, time_desc(elapsed_s))

        def callback():
            print "notification for %s clicked" % channel_name
            webbrowser.open(stream_browser_link)

        self.log("Showing message: '%s'" % message.encode("utf-8"))

        self.windows_balloon_tip_obj.balloon_tip("twitch-notifier", message,
                                                 callback=callback)

    def main_loop(self):
        options = self.options
        username = options.username

        self._init_notifier()

        channels_followed = set()
        channel_info = {}
        last_streams = {}

        channels_followed_names = []

        # first time querying

        if options.authorization_oauth is not None:
            authorization = "OAuth %s" % options.authorization_oauth
            # noinspection PyProtectedMember
            twitch.queries._v3_headers["Authorization"] = authorization
            self.use_fast_query = True

        notifications_disabled_for = []

        for follow in paged_query_iterator(twitch.api.v3.follows.by_user, name=username, results_list_key='follows'):
            channel = follow["channel"]
            channel_id = channel["_id"]
            channel_name = channel["display_name"]

            notifications_enabled = follow["notifications"]
            if options.all or notifications_enabled:

                channels_followed.add(channel_id)
                channels_followed_names.append(channel_name)
                channel_info[channel_id] = channel

            else:

                notifications_disabled_for.append(channel_name)

        followed_channel_entries = []

        for channel_id in channels_followed:
            followed_channel_entries.append(channel_info[channel_id])

        followed_channel_entries.sort(key=lambda ch: ch["display_name"])

        print "Watching: %s" % ", ".join(["%(display_name)s (%(_id)s)" % x for x in followed_channel_entries])
        if len(notifications_disabled_for) > 0:
            print "Notifications disabled for: %s" % ", ".join(sorted(notifications_disabled_for))

        # loop

        try:
            # Poll for twitch
            while True:
                locked = windows_lock_check.check_if_locked()
                idle = windows_lock_check.check_if_idle(threshold_s=options.idle)
                self.log("locked: %s idle: %s" % (locked, idle))
                if locked or idle:
                    self.log("Locked, waiting for unlock")
                    while windows_lock_check.check_if_locked() or windows_lock_check.check_if_idle(threshold_s=options.idle):
                        time.sleep(5)
                    if options.unlock_notify:
                        self.log("Clearing last streams to renotify")
                        last_streams = {}

                self.log("Checking for follow stream changes")

                if self.use_fast_query:
                    channel_stream_iterator = self.get_streams_channels_following(channel_info.viewkeys())
                else:
                    channel_stream_iterator = self.get_streams_channels_iterating(channel_info, channels_followed)

                for channel_id, channel, stream in channel_stream_iterator:
                    channel_name = channel["display_name"]
                    if stream is not None and not stream["is_playlist"]:
                        stream_id = stream["_id"]
                        if last_streams.get(channel_id) != stream_id:
                            self.notify_for_stream(channel_name, stream)

                        last_streams[channel_id] = stream_id
                    else:
                        if stream is None:
                            self.log("channel_id %r had stream None" % channel_id)
                        else:
                            self.log("channel_id %r is_playlist %r" % (channel_id, stream["is_playlist"]))
                        last_streams[channel_id] = None

                self.log("Waiting %s s for next poll" % options.poll)
                time.sleep(max(options.poll, 60))
        except (KeyboardInterrupt, Exception):
            self._notifier_fini()
            raise

    def log(self, msg):
        if self.options.debug_output:
            print "TwitchNotifierMain: %s" % msg

    def get_streams_channels_iterating(self, channel_info, channels_followed):
        """
        Get streams by iterating through the channels we're following. More queries but requires no special auth (as of 2016-07-09)
        :param channels_followed: list of ids of channels we're following
        :param channel_info: dict of channel_id -> previously loaded channel dict
        :return: generator that yields (channel_id, channel, stream) for each stream
        """
        for channel_id in channels_followed:
            original_channel = channel_info[channel_id]
            channel_name = original_channel["display_name"]

            self.log("twitch.api.v3.streams.by_channel(%r)" % channel_name)
            response = twitch.api.v3.streams.by_channel(channel_name)

            stream = response["stream"]
            if stream is not None:
                updated_channel = stream['channel']
            else:
                updated_channel = original_channel
            yield channel_id, updated_channel, stream

    def get_streams_channels_following(self, followed_channels):
        """
        Get live streams for followed channels. Efficient because it's a single query but requires auth
        :param followed_channels: set of ids of channels that we've followed
        :return: generator that yields (channel_id, channel, stream) for each stream
        """

        self.log("twitch streams/followed(live)")
        query = twitch_streams_followed(STREAM_TYPE_LIVE)
        response = query.execute()
        for stream in response['streams']:
            channel = stream['channel']

            channel_id = channel['_id']
            if channel_id not in followed_channels:
                # skip channels that are here because they're being hosted by another channel
                self.log("skipping channel_id %r because it's not a followed channel" % channel_id)
                continue
            yield channel_id, channel, stream


def main():
    options = parse_args()

    twitch_notifier_main = TwitchNotifierMain(options)

    twitch_notifier_main.main_loop()


if __name__ == "__main__":
    main()
