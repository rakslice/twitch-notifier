# noinspection PyPackageRequirements
import os
import webbrowser

# noinspection PyPackageRequirements
import sys
import wx


cur = os.path.abspath(".")
if cur not in sys.path:
    sys.path.append(cur)


from notifiergui.notifier_gui_codegen import MainStatusWindow
from twitch_notifier_main import TwitchNotifierMain, parse_args


script_path = os.path.dirname(os.path.abspath(__file__))
assets_path = os.path.join(script_path, "..", "assets")


class OurTwitchNotifierMain(TwitchNotifierMain):
    def __init__(self, options, window_impl):
        """:type window_impl: MainStatusWindowImpl"""
        self.window_impl = window_impl
        super(OurTwitchNotifierMain, self).__init__(options)
        self.main_loop_iter = None
        self.followed_channel_entries = None
        self.channel_status_by_id = {}
        self.stream_by_channel_id = {}

    def main_loop_main_window_timer(self):
        self.main_loop_iter = iter(self.main_loop_yielder())
        self.set_next_time()

    def _init_notifier(self):
        self.windows_balloon_tip_obj = OurWindowsBalloonTip(self.window_impl)

    def _notifier_fini(self):
        pass

    def set_next_time(self):
        time_s, wait_reason = self.main_loop_iter.next()
        self.window_impl.set_timer_with_callback(time_s, self.set_next_time)

    def log(self, msg):
        self.window_impl.list_log.Append(msg)

    def init_channel_display(self, followed_channel_entries):
        super(OurTwitchNotifierMain, self).init_channel_display(followed_channel_entries)

        self.followed_channel_entries = followed_channel_entries
        self.reset_lists()

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

    def open_site_for_list_entry(self, is_online, index):
        stream = None
        channel = None
        for channel_id, cur_status in self.channel_status_by_id.iteritems():
            if cur_status["idx"] == index and cur_status["online"] == is_online:
                if channel_id in self.stream_by_channel_id:
                    stream = self.stream_by_channel_id[channel_id]
                channel = self._channel_for_id(channel_id)
                if channel is None:
                    self.log("Channel entry not found for id %r" % channel_id)
                    return
                break

        if stream is not None:
            url = stream["channel"]["url"]
        elif channel is not None:
            url = channel["url"]
        else:
            self.log("Channel is none somehow")
            return

        webbrowser.open(url)


class MainStatusWindowImpl(MainStatusWindow):
    def __init__(self, *args, **kwargs):
        super(MainStatusWindowImpl, self).__init__(*args, **kwargs)
        self.timer = None
        self.balloon_click_callback = None

        self.toolbar_icon = wx.TaskBarIcon()
        the_icon = wx.EmptyIcon()
        the_icon.CopyFromBitmap(wx.Bitmap(os.path.join(assets_path, "icon.ico"), wx.BITMAP_TYPE_ANY))

        self.toolbar_icon.SetIcon(the_icon)

        self.toolbar_icon.Bind(wx.EVT_TASKBAR_LEFT_DCLICK, self._on_toolbar_icon_left_dclick)
        self.toolbar_icon.Bind(wx.EVT_TASKBAR_BALLOON_CLICK, self._on_toolbar_balloon_click)
        self.Bind(wx.EVT_CLOSE, self._on_close)

        options = parse_args()
        self.main_obj = OurTwitchNotifierMain(options, self)
        self.main_obj.main_loop_main_window_timer()

    # noinspection PyUnusedLocal
    def _on_toolbar_balloon_click(self, event):
        if self.balloon_click_callback is not None:
            self.balloon_click_callback()

    # noinspection PyUnusedLocal
    def _on_toolbar_icon_left_dclick(self, event):
        self.Show()

    # noinspection PyUnusedLocal
    def _on_close(self, event):
        self.Hide()

    def _on_list_online_dclick(self, event):
        self.main_obj.open_site_for_list_entry(True, event.GetInt())

    def _on_list_offline_dclick(self, event):
        self.main_obj.open_site_for_list_entry(False, event.GetInt())

    def _on_button_quit(self, event):
        self.toolbar_icon.RemoveIcon()
        self.toolbar_icon.Destroy()
        self.toolbar_icon = None
        self.Destroy()

    def set_timer_with_callback(self, time_s, callback, timer_id=100):
        assert self.timer is None

        # noinspection PyUnusedLocal
        def internal_callback(event):
            print "timer hit"
            self.timer.Stop()
            self.timer = None
            callback()

        print "setting up timer for %d s" % time_s
        self.timer = wx.Timer(self, timer_id)
        wx.EVT_TIMER(self, timer_id, internal_callback)
        self.timer.Start(time_s * 1000)

    def set_balloon_click_callback(self, callback):
        self.balloon_click_callback = callback


class OurWindowsBalloonTip(object):
    def __init__(self, main_window):
        """:type main_window: MainStatusWindowImpl"""
        self.main_window = main_window

    def balloon_tip(self, title, msg, callback=None):
        self.main_window.set_balloon_click_callback(callback)

        icon = self.main_window.GetIcon()
        self.main_window.toolbar_icon.ShowBalloon(title, msg, 0, icon.GetHandle())


def main():
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame_1 = MainStatusWindowImpl(None, -1, "")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()


if __name__ == "__main__":
    main()
