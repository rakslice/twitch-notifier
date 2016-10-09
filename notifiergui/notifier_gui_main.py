import os
import sys
import cStringIO
import time

# noinspection PyPackageRequirements
import wx

from notifiergui.our_twitch_notifier_main import OurTwitchNotifierMain

cur = os.path.abspath(".")
if cur not in sys.path:
    sys.path.append(cur)


# These have to go after the path correction
from notifiergui.notifier_gui_codegen import MainStatusWindow
from twitch_notifier_main import parse_args, time_desc, convert_iso_time

script_path = os.path.dirname(os.path.abspath(__file__))
assets_path = os.path.join(script_path, "..", "assets")


def show_image_in_wx_image(control, image_data):
    """
    Using image data in a byte string, show it in a control
    :type control: wx.StaticBitmap
    :type image_data: str
    """
    # fixed height control expected
    height = control.GetMinHeight()
    width = control.GetMinWidth()
    sbuf = cStringIO.StringIO(image_data)
    image = wx.ImageFromStream(sbuf)
    if width and height:
        image = image.Scale(width, height)
    bitmap = image.ConvertToBitmap()
    control.SetBitmap(bitmap)


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

        self.base_logo_bitmap = self.bitmap_channel_logo.GetBitmap()

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

    def clear_info(self):
        # self.label_debug.SetLabel(u"")
        self.clear_stream_info()

    def set_stream_info(self, stream):
        for label in [self.label_head_game, self.label_head_started, self.label_head_up]:
            label.Show()
            label.Refresh()
        game = stream["game"]
        if game:
            self.label_game.SetLabel(game)
        else:
            self.label_game.SetLabel(u"")
        created_at = stream["created_at"]
        self.label_start_time.SetLabel(created_at)
        start_time = convert_iso_time(created_at)
        elapsed_s = time.time() - start_time
        self.label_uptime.SetLabel(time_desc(elapsed_s))
        # self.label_stream_desc.SetLabel(u" ".join(parts))

    def clear_stream_info(self):
        # self.label_stream_desc.SetLabel(u"")
        for label in [self.label_game, self.label_uptime, self.label_start_time]:
            label.SetLabel(u"")
        for label in [self.label_head_game, self.label_head_started, self.label_head_up]:
            label.Hide()

    def show_info(self, channel, stream):
        # d = "channel:\n%s\nstream:\n%s" % (pretty_json(channel), pretty_json(stream))
        # self.label_debug.SetLabel(d.replace("\n", "\r\n"))

        if channel is None:
            self.label_channel_status.SetLabel(u"")
        else:
            self.label_channel_status.SetLabel(channel["status"])

        if stream is not None:
            self.set_stream_info(stream)

        else:
            self.clear_stream_info()

        self.main_obj.cancel_delayed_url_loads_for_context("channel")

        self.bitmap_channel_logo.SetBitmap(self.base_logo_bitmap)
        # self.bitmap_channel_logo.ClearBackground()

        logo_url = channel.get("logo")
        if logo_url:
            # noinspection PyUnusedLocal
            def _on_logo_load(rs, **kwargs):
                """:type rs: requests.Response"""
                if not rs.status_code == 200:
                    self.main_obj.log("Got HTTP error %d %s retrieving %s" % (rs.status_code, rs.reason, logo_url))
                    return
                self.main_obj.log("Logo loaded")
                content_type = rs.headers["Content-type"]
                # TODO verify content type
                data = rs.content
                show_image_in_wx_image(self.bitmap_channel_logo, data)

            self.main_obj.log("Showing logo %s" % logo_url)
            self.main_obj.do_delayed_url_load("channel", logo_url, _on_logo_load)

    def _on_list_online_gen(self, event):
        idx = event.GetInt()
        if idx >= 0:
            self.list_offline.DeselectAll()  # deselect other list
            channel, stream = self.main_obj.get_channel_and_stream_for_list_entry(True, idx)
            self.show_info(channel, stream)
        else:
            self.clear_info()

    def _on_list_offline_gen(self, event):
        idx = event.GetInt()
        if idx >= 0:
            self.list_online.DeselectAll()  # deselect other list
            channel, stream = self.main_obj.get_channel_and_stream_for_list_entry(False, idx)
            self.show_info(channel, stream)
        else:
            self.clear_info()

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


def main():
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame_1 = MainStatusWindowImpl(None, -1, "")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()


if __name__ == "__main__":
    main()
