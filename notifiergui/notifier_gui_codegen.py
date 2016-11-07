#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
# generated by wxGlade 0.6.3 on Sun Sep 25 13:43:28 2016

import wx

# begin wxGlade: extracode
# end wxGlade



class MainStatusWindow(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: MainStatusWindow.__init__
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.bitmap_channel_logo = wx.StaticBitmap(self, -1, wx.NullBitmap)
        self.label_6 = wx.StaticText(self, -1, "Channel Description:")
        self.label_head_game = wx.StaticText(self, -1, "Game:")
        self.label_head_up = wx.StaticText(self, -1, "Up:")
        self.label_head_started = wx.StaticText(self, -1, "Started:")
        self.label_channel_status = wx.StaticText(self, -1, "")
        self.label_game = wx.StaticText(self, -1, "")
        self.label_uptime = wx.StaticText(self, -1, "")
        self.label_start_time = wx.StaticText(self, -1, "")
        self.label_1 = wx.StaticText(self, -1, "Online")
        self.list_online = wx.ListBox(self, -1, choices=[])
        self.label_2 = wx.StaticText(self, -1, "Offline")
        self.list_offline = wx.ListBox(self, -1, choices=[])
        self.label_3 = wx.StaticText(self, -1, "Log")
        self.list_log = wx.ListBox(self, -1, choices=[])
        self.button_options = wx.Button(self, -1, "&Options")
        self.button_reload_channels = wx.Button(self, -1, "&Reload Channels")
        self.button_quit = wx.Button(self, -1, "&Quit")
        self.label_status = wx.StaticText(self, -1, "Status")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_LISTBOX_DCLICK, self._on_list_online_dclick, self.list_online)
        self.Bind(wx.EVT_LISTBOX, self._on_list_online_gen, self.list_online)
        self.Bind(wx.EVT_LISTBOX_DCLICK, self._on_list_offline_dclick, self.list_offline)
        self.Bind(wx.EVT_LISTBOX, self._on_list_offline_gen, self.list_offline)
        self.Bind(wx.EVT_BUTTON, self._on_options_button_click, self.button_options)
        self.Bind(wx.EVT_BUTTON, self._on_button_reload_channels_click, self.button_reload_channels)
        self.Bind(wx.EVT_BUTTON, self._on_button_quit, self.button_quit)
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: MainStatusWindow.__set_properties
        self.SetTitle("twitch-notifier")
        self.SetSize((788, 793))
        self.SetBackgroundColour(wx.Colour(240, 240, 240))
        self.bitmap_channel_logo.SetMinSize((128,128))
        self.label_6.SetBackgroundColour(wx.Colour(240, 240, 240))
        self.label_head_game.SetBackgroundColour(wx.Colour(240, 240, 240))
        self.label_head_up.SetBackgroundColour(wx.Colour(240, 240, 240))
        self.label_head_started.SetBackgroundColour(wx.Colour(240, 240, 240))
        self.label_channel_status.SetBackgroundColour(wx.Colour(240, 240, 240))
        self.label_game.SetBackgroundColour(wx.Colour(240, 240, 240))
        self.label_uptime.SetBackgroundColour(wx.Colour(240, 240, 240))
        self.label_start_time.SetBackgroundColour(wx.Colour(240, 240, 240))
        self.list_online.SetToolTipString("Double-Click to open stream page")
        self.list_offline.SetToolTipString("Double-Click to open channel page")
        self.button_options.Enable(False)
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: MainStatusWindow.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_6 = wx.BoxSizer(wx.VERTICAL)
        sizer_5 = wx.BoxSizer(wx.VERTICAL)
        sizer_3.Add(self.bitmap_channel_logo, 0, wx.EXPAND, 0)
        sizer_3.Add((10, 1), 0, wx.EXPAND, 0)
        sizer_5.Add(self.label_6, 0, wx.EXPAND, 0)
        sizer_5.Add(self.label_head_game, 0, wx.EXPAND, 0)
        sizer_5.Add(self.label_head_up, 0, wx.EXPAND, 0)
        sizer_5.Add(self.label_head_started, 1, wx.EXPAND, 0)
        sizer_3.Add(sizer_5, 0, wx.EXPAND, 0)
        sizer_3.Add((10, 1), 0, wx.EXPAND, 0)
        sizer_6.Add(self.label_channel_status, 0, wx.EXPAND, 0)
        sizer_6.Add(self.label_game, 0, wx.EXPAND, 0)
        sizer_6.Add(self.label_uptime, 0, wx.EXPAND, 0)
        sizer_6.Add(self.label_start_time, 1, wx.EXPAND, 0)
        sizer_3.Add(sizer_6, 1, wx.EXPAND, 0)
        sizer_1.Add(sizer_3, 0, wx.EXPAND, 0)
        sizer_1.Add(self.label_1, 0, wx.EXPAND, 0)
        sizer_1.Add(self.list_online, 0, wx.EXPAND, 0)
        sizer_1.Add(self.label_2, 0, wx.EXPAND, 0)
        sizer_1.Add(self.list_offline, 1, wx.EXPAND, 0)
        sizer_1.Add(self.label_3, 0, wx.EXPAND, 0)
        sizer_1.Add(self.list_log, 0, wx.EXPAND, 0)
        sizer_2.Add(self.button_options, 0, 0, 0)
        sizer_2.Add(self.button_reload_channels, 0, 0, 0)
        sizer_2.Add((20, 20), 1, wx.EXPAND, 0)
        sizer_2.Add(self.button_quit, 0, 0, 0)
        sizer_1.Add(sizer_2, 0, wx.EXPAND, 0)
        sizer_1.Add(self.label_status, 0, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        self.Layout()
        # end wxGlade

    def _on_button_quit(self, event): # wxGlade: MainStatusWindow.<event_handler>
        print "Event handler `_on_button_quit' not implemented"
        event.Skip()

    def _on_list_online_dclick(self, event): # wxGlade: MainStatusWindow.<event_handler>
        print "Event handler `_on_list_online_dclick' not implemented"
        event.Skip()

    def _on_list_offline_dclick(self, event): # wxGlade: MainStatusWindow.<event_handler>
        print "Event handler `_on_list_offline_dclick' not implemented"
        event.Skip()

    def _on_options_button_click(self, event): # wxGlade: MainStatusWindow.<event_handler>
        print "Event handler `_on_options_button_click' not implemented"
        event.Skip()

    def _on_list_online_gen(self, event): # wxGlade: MainStatusWindow.<event_handler>
        print "Event handler `_on_list_online_gen' not implemented"
        event.Skip()

    def _on_list_offline_gen(self, event): # wxGlade: MainStatusWindow.<event_handler>
        print "Event handler `_on_list_offline_gen' not implemented"
        event.Skip()

    def _on_button_refresh_channels_click(self, event): # wxGlade: MainStatusWindow.<event_handler>
        print "Event handler `_on_button_refresh_channels_click' not implemented"
        event.Skip()

    def _on_button_reload_channels_click(self, event): # wxGlade: MainStatusWindow.<event_handler>
        print "Event handler `_on_button_reload_channels_click' not implemented"
        event.Skip()

# end of class MainStatusWindow


if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame_1 = MainStatusWindow(None, -1, "")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
