import argparse
import calendar
import json
import os
import shelve
import time
import traceback
import webbrowser

import datetime
# noinspection PyPackageRequirements
import appdirs
import twitch.queries
# noinspection PyPackageRequirements
import twitch.api.v3
# noinspection PyPackageRequirements
import twitch.keys

import browser_auth
try:
    import windows_10_toast_notifications
    import windows_lock_check
except ImportError:
    windows_10_toast_notifications = None
    windows_lock_check = None

script_path = os.path.dirname(os.path.abspath(__file__))
assets_path = os.path.join(script_path, "assets")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user",
                        dest="username")
    parser.add_argument("--no-browser-auth",
                        help="don't authenticate through twitch website login if token not supplied",
                        dest="browser_auth",
                        default=True,
                        action="store_false")
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
    parser.add_argument("--ui",
                        help="Use the wxpython UI")
    parser.add_argument("--no-popups",
                        dest="popups",
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


def convert_iso_time(iso_time):
    start_time = calendar.timegm(time.strptime(iso_time, "%Y-%m-%dT%H:%M:%SZ"))
    return start_time


class TwitchNotifierMain(object):
    def __init__(self, options):
        self.options = options
        self._auth_oauth = None
        self.windows_balloon_tip_obj = None
        """:type: windows_10_toast_notifications.WindowsBalloonTip"""
        self.use_fast_query = False

        self.need_channels_refresh = True

        self.cache_dir = appdirs.user_cache_dir("twitch-notifier", "rakslice")
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        self.cache_shelf_filename = os.path.join(self.cache_dir, "url_cached.dat")
        self.cache_shelf = shelve.open(self.cache_shelf_filename)

        self.saved_config_filename = os.path.join(self.cache_dir, "config.json")

        self.saved_config = None
        self._load_saved_config()

    def shutdown(self):
        self.cache_shelf.close()

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
        created_at = stream["created_at"]
        start_time = convert_iso_time(created_at)
        elapsed_s = time.time() - start_time

        stream_browser_link = stream["channel"]["url"]
        game = stream["game"]

        if game is None:
            show_info = ""
        else:
            show_info = u"with %s " % stream["game"]

        message = u"%s is now live %s(up %s)" % (channel_name, show_info, time_desc(elapsed_s))

        def callback():
            print "notification for %s clicked" % channel_name
            webbrowser.open(stream_browser_link)

        self.log("Showing message: '%s'" % message.encode("utf-8"))

        if self.options.popups:
            self.windows_balloon_tip_obj.balloon_tip("twitch-notifier", message,
                                                     callback=callback)

    def _auth_complete_callback(self, token, used_cached_auth=False):
        assert token is not None

        if not used_cached_auth:
            self.saved_config["oauth_token"] = (token, time.time())
            self._write_saved_config()

        self._auth_oauth = token
        # get us a username

        self.main_loop_post_auth()

    def main_loop_auth(self):
        return self.main_loop_post_auth()

    def need_browser_auth(self):
        return self.options.browser_auth and self._auth_oauth is None

    def do_browser_auth(self):
        oauth_token = None
        if "oauth_token" in self.saved_config:
            oauth_token, oauth_token_timestamp = self.saved_config["oauth_token"]
            token_age = time.time() - oauth_token_timestamp
            if token_age > 60 * 60 * 24 * 30:
                oauth_token = None

        if oauth_token is not None:
            self._auth_complete_callback(oauth_token, used_cached_auth=True)
        else:
            browser_auth.do_browser(self._auth_complete_callback, debug=self.options.debug_output)

    def main_loop(self):
        options = self.options

        if options.authorization_oauth is not None:
            self._auth_oauth = options.authorization_oauth
        elif self.need_browser_auth():
            self.do_browser_auth()
        else:
            assert options.username is not None, "You need to set a username (--user)"
        self.main_loop_post_auth()

    def main_loop_post_auth(self):
        for sleep_time, sleep_reason in self.main_loop_yielder():
            time.sleep(sleep_time)

    def _channels_reload_complete(self):
        pass

    def main_loop_yielder(self):
        options = self.options

        channels_followed = set()
        channel_info = {}
        last_streams = {}

        channels_followed_names = []

        self._init_notifier()

        # loop

        try:
            # Poll for twitch
            while True:
                try:
                    if self.need_channels_refresh:
                        self.need_channels_refresh = False
                        channels_followed.clear()
                        channel_info.clear()
                        last_streams.clear()
                        channels_followed_names[:] = []

                        # first time querying

                        if self._auth_oauth is not None:
                            authorization = "OAuth %s" % self._auth_oauth
                            # noinspection PyProtectedMember
                            twitch.queries._v3_headers["Authorization"] = authorization
                            self.use_fast_query = True

                            if options.username is None:
                                root_response = twitch.api.v3.root()
                                options.username = root_response["token"]["user_name"]

                        notifications_disabled_for = []

                        for follow in paged_query_iterator(twitch.api.v3.follows.by_user, name=options.username, results_list_key='follows'):
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

                        self.init_channel_display(followed_channel_entries)

                        print "Watching: %s" % ", ".join([self.channel_display_name(x) for x in followed_channel_entries])
                        if len(notifications_disabled_for) > 0:
                            print "Notifications disabled for: %s" % ", ".join(sorted(notifications_disabled_for))

                        self._channels_reload_complete()

                    if windows_lock_check is None:
                        locked = False
                        idle = False
                    else:
                        locked = windows_lock_check.check_if_locked()
                        idle = windows_lock_check.check_if_idle(threshold_s=options.idle)
                    self.log("locked: %s idle: %s" % (locked, idle))
                    if locked or idle:
                        self.log("Locked, waiting for unlock")
                        while windows_lock_check.check_if_locked() or windows_lock_check.check_if_idle(threshold_s=options.idle):
                            yield 5, "waiting for unlock"
                        if options.unlock_notify:
                            self.log("Clearing last streams to renotify")
                            last_streams = {}

                    self.log("Checking for follow stream changes")

                    if self.use_fast_query:
                        self.assume_all_streams_offline()
                        channel_stream_iterator = self.get_streams_channels_following(channel_info.viewkeys())
                    else:
                        channel_stream_iterator = self.get_streams_channels_iterating(channel_info, channels_followed)

                    for channel_id, channel, stream in channel_stream_iterator:
                        channel_name = channel["display_name"]

                        stream_we_consider_online = stream is not None and not stream["is_playlist"]

                        self.stream_state_change(channel_id, stream_we_consider_online, stream)

                        if stream_we_consider_online:
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

                    self.done_state_changes()
                except Exception, e:
                    traceback.print_exc()
                    self.log(repr(e))

                self.log("Waiting %s s for next poll" % options.poll)
                sleep_until_next_poll_s = max(options.poll, 60)
                yield sleep_until_next_poll_s, "waiting until another poll is allowed"
        except (KeyboardInterrupt, Exception):
            self._notifier_fini()
            raise

    def log(self, msg):
        if self.options.debug_output:
            print "%s TwitchNotifierMain: %s" % (datetime.datetime.now(), msg)

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

    @staticmethod
    def channel_display_name(x):
        return "%(display_name)s (%(_id)s)" % x

    def init_channel_display(self, followed_channel_entries):
        pass

    def stream_state_change(self, channel_id, stream_we_consider_online, stream):
        pass

    def assume_all_streams_offline(self):
        pass

    def done_state_changes(self):
        pass

    def _load_saved_config(self):
        filename = self.saved_config_filename
        if os.path.exists(filename):
            try:
                with open(filename, "r") as handle:
                    self.saved_config = json.load(handle)
            except Exception, e:
                self.log("Error loading config: %r" % e)
                self.saved_config = {}
        else:
            self.saved_config = {}

    def _write_saved_config(self):
        with open(self.saved_config_filename, "w") as handle:
            json.dump(self.saved_config, handle)


def main():
    options = parse_args()

    twitch_notifier_main = TwitchNotifierMain(options)

    twitch_notifier_main.main_loop()


if __name__ == "__main__":
    main()
