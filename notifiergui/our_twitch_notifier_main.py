import functools
import os
import shelve
import traceback
import webbrowser
import time

import datetime

import appdirs
import grequests

import requests

from notifiergui.our_windows_balloon_tip import OurWindowsBalloonTip
from twitch_notifier_main import TwitchNotifierMain


class FakeResponse(object):
    def __init__(self):
        self.content = None
        self.headers = None
        self.status_code = None
        self.reason = None


class OurTwitchNotifierMain(TwitchNotifierMain):
    def __init__(self, options, window_impl):
        """:type window_impl: MainStatusWindowImpl"""
        self.window_impl = window_impl
        super(OurTwitchNotifierMain, self).__init__(options)
        self.main_loop_iter = None
        self.followed_channel_entries = None
        self.channel_status_by_id = {}
        """:type: dict[str, dict[str, any]]"""
        self.stream_by_channel_id = {}
        self.previously_online_streams = set()

        self.delayed_url_request_ids_by_context = {}
        """:type: dict[str, list[int]]"""

        self.next_request_id = 0
        self.delayed_url_requests_by_id = {}
        """:type: dict[int, grequests.AsyncRequest]"""

        self.cache_dir = appdirs.user_cache_dir("twitch-notifier", "rakslice")
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        self.cache_shelf_filename = os.path.join(self.cache_dir, "url_cached.dat")
        self.cache_shelf = shelve.open(self.cache_shelf_filename)

    def cancel_delayed_url_loads_for_context(self, ctx):
        l = self.delayed_url_request_ids_by_context.pop(ctx, None)
        if l is not None:
            for request_id in l:
                self.cancel_delayed_url_load(request_id)

    def cancel_delayed_url_load(self, request_id):
        request = self.delayed_url_requests_by_id.pop(request_id)
        if request is not None:
            # FIXME verify that the scope of this isn't too large
            request.session.close()
            # FIXME verify that there is no further cleanup to do so we can do future requests

    def _on_delayed_url_load(self, request_id, ctx, callback, response, **kwargs):
        """
        :type request_id: int
        :type ctx: str
        :type response: requests.Response
        """
        try:
            self.delayed_url_requests_by_id.pop(request_id, None)
            l = self.delayed_url_request_ids_by_context.get(ctx, None)
            if l is not None:
                try:
                    l.remove(request_id)
                except ValueError:
                    pass
            callback(response, **kwargs)
            if response.status_code == 200:
                data = response.content
                max_age = response.headers.get("max-age")
                url = response.url
                cache_entry = {"timestamp": time.time(),
                               "max_age": max_age,
                               "data": data,
                               "headers": response.headers}
                url_str = url.encode("utf-8")
                self.cache_shelf[url_str] = cache_entry
                self.cache_shelf.sync()
        except Exception, e:
            traceback.print_exc()
            self.log("Exception %r" % e)

    def do_delayed_url_load(self, ctx, url, callback):
        # look for a cache entry
        url_str = url.encode("utf-8")
        cache_entry = self.cache_shelf.get(url_str)
        if cache_entry is not None:
            age = time.time() - cache_entry["timestamp"]
            max_age = cache_entry.get("max_age", 86400)
            if max_age and age > max_age:
                cache_entry = None

        if cache_entry is not None:
            self.log(u"Using cache url %s" % url)
            response = FakeResponse()
            response.content = cache_entry["data"]
            response.headers = cache_entry["headers"]
            response.status_code = 200
            response.reason = "OK"
            callback(response)
            return

        self.log(u"Loading url %s" % url)

        request_id = self.next_request_id
        self.next_request_id += 1

        wrapped_callback = functools.partial(self._on_delayed_url_load, request_id, ctx, callback)

        request = grequests.AsyncRequest("GET", url, hooks={"response": wrapped_callback})
        self.delayed_url_requests_by_id[request_id] = request
        self.delayed_url_request_ids_by_context.setdefault(ctx, []).append(request_id)

        request.send()

        return request

    def main_loop_main_window_timer(self):
        if self.need_browser_auth():
            self.do_browser_auth()
        else:
            self.main_loop_main_window_timer_with_auth()

    def main_loop_main_window_timer_with_auth(self):
        self.main_loop_iter = iter(self.main_loop_yielder())
        self.set_next_time()

    def main_loop_post_auth(self):
        self.main_loop_main_window_timer_with_auth()

    def _init_notifier(self):
        self.windows_balloon_tip_obj = OurWindowsBalloonTip(self.window_impl)

    def _notifier_fini(self):
        pass

    def set_next_time(self):
        time_s, wait_reason = self.main_loop_iter.next()
        self.window_impl.set_timer_with_callback(time_s, self.set_next_time)

    def log(self, msg):
        line_item = u"%s: %s" % (datetime.datetime.now(), msg)
        self.window_impl.list_log.Append(line_item)

    def init_channel_display(self, followed_channel_entries):
        super(OurTwitchNotifierMain, self).init_channel_display(followed_channel_entries)

        self.followed_channel_entries = followed_channel_entries
        self.reset_lists()

    def assume_all_streams_offline(self):
        self.previously_online_streams.clear()
        for channel_id, channel_status in self.channel_status_by_id.iteritems():
            if channel_status["online"]:
                self.previously_online_streams.add(channel_id)

    def reset_lists(self):
        self.window_impl.list_offline.Clear()
        self.channel_status_by_id.clear()
        for i, channel in enumerate(self.followed_channel_entries):
            self.window_impl.list_offline.Append(self.channel_display_name(channel))
            channel_id = channel["_id"]
            self.channel_status_by_id[channel_id] = {"online": False, "idx": i}

    def _list_for_is_online(self, is_online):
        """:rtype: ListBox"""
        if is_online:
            return self.window_impl.list_online
        else:
            return self.window_impl.list_offline

    def _channel_for_id(self, channel_id):
        for channel in self.followed_channel_entries:
            if channel["_id"] == channel_id:
                return channel

    def stream_state_change(self, channel_id, new_online, stream):

        if channel_id in self.previously_online_streams:
            self.previously_online_streams.remove(channel_id)

        self.stream_by_channel_id[channel_id] = stream

        channel_obj = self._channel_for_id(channel_id)
        if channel_obj is None:
            return

        channel_status = self.channel_status_by_id[channel_id]
        old_online = channel_status["online"]
        if old_online != new_online:
            old_index = channel_status["idx"]
            out_of_list = self._list_for_is_online(old_online)
            out_of_list.Delete(old_index)

            into_list = self._list_for_is_online(new_online)
            new_index = into_list.GetCount()
            into_list.Append(self.channel_display_name(channel_obj))

            # update the later indexes
            for cur_status in self.channel_status_by_id.values():
                if cur_status["online"] == old_online and cur_status["idx"] > old_index:
                    cur_status["idx"] -= 1
                elif cur_status["online"] == new_online and cur_status["idx"] >= new_index:
                    cur_status["idx"] += 1

            channel_status["online"] = new_online
            channel_status["idx"] = new_index

    def done_state_changes(self):
        streams_that_went_offline = list(self.previously_online_streams)
        for channel_id in streams_that_went_offline:
            self.stream_state_change(channel_id, new_online=False, stream=None)
        self.previously_online_streams.clear()

    def _get_channel_id_for_list_entry(self, is_online, index):
        for channel_id, cur_status in self.channel_status_by_id.iteritems():
            if cur_status["idx"] == index and cur_status["online"] == is_online:
                return channel_id
        return None

    def get_channel_and_stream_for_list_entry(self, is_online, index):
        stream = None
        channel = None

        channel_id = self._get_channel_id_for_list_entry(is_online, index)
        if channel_id is not None:
            if channel_id in self.stream_by_channel_id:
                stream = self.stream_by_channel_id[channel_id]
            channel = self._channel_for_id(channel_id)
            if channel is None:
                self.log("Channel entry not found for id %r" % channel_id)

        return channel, stream

    def open_site_for_list_entry(self, is_online, index):
        channel, stream = self.get_channel_and_stream_for_list_entry(is_online, index)

        if stream is not None:
            url = stream["channel"]["url"]
        elif channel is not None:
            url = channel["url"]
        else:
            self.log("Channel is none somehow")
            return

        webbrowser.open(url)
