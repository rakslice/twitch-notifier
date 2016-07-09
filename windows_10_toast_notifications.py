from win32gui import *
import win32con
# import time

"""
Show toast notification messages in Windows 10
Based on https://github.com/jithurjacob/Windows-10-Toast-Notifications/blob/master/main.py
"""


# Example
# w = WindowsBalloonTip()

# w.balloon_tip('Example one', 'Python is awsm')
# w.balloon_tip('Example two', 'Once you start coding in Python you will hate other languages')

# Class

OUR_NOTIFICATION_WM = win32con.WM_USER + 20

DEBUG = False


class WindowsBalloonTip:
    def __init__(self, window_title="Taskbar", debug_output=False):
        self.debug_output = debug_output

        message_map = {win32con.WM_DESTROY: self.on_destroy,
                       OUR_NOTIFICATION_WM: self.on_notification_message,
                       }

        # Register the window class.
        wc = WNDCLASS()
        self.hinst = wc.hInstance = GetModuleHandle(None)
        wc.lpszClassName = 'PythonTaskbar'
        wc.lpfnWndProc = message_map  # could also specify a wndproc.
        self.classAtom = RegisterClass(wc)
        self.last_callback = None
        self.hwnd = None

        self.window_title = window_title

        self.init_window(window_title)

    # noinspection PyUnusedLocal,PyMethodMayBeStatic
    def on_destroy(self, hwnd, msg, wparam, lparam):
        nid = (hwnd, 0)
        Shell_NotifyIcon(NIM_DELETE, nid)
        PostQuitMessage(0)

    # noinspection PyUnusedLocal
    def on_notification_message(self, hwnd, msg, wparam, lparam):
        if DEBUG:
            print "shell notify event %r %r" % (wparam, lparam)
        if lparam == 1029:
            if DEBUG:
                print "clicked"
            if self.last_callback is not None:
                self.last_callback()
                self.last_callback = None
            PostQuitMessage(0)
        elif lparam == 1028:
            PostQuitMessage(0)

    def init_window(self, window_title):
        assert window_title is not None

        # assert self.hwnd is None, "already initialized"

        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        hwnd = CreateWindow(self.classAtom, window_title, style, 0, 0, win32con.CW_USEDEFAULT, win32con.CW_USEDEFAULT, 0, 0, self.hinst, None)
        UpdateWindow(hwnd)

        self.hwnd = hwnd
        # self.nid = nid
        # self.hicon = hicon

    def log(self, msg):
        if self.debug_output:
            print msg

    def balloon_tip(self, title, msg, callback=None):
        self.last_callback = callback

        # self.init_window(self.window_title)

        hwnd = self.hwnd
        # nid = self.nid
        # hicon = self.hicon
        self.log("hwnd: %r" % hwnd)

        hicon = LoadIcon(0, win32con.IDI_APPLICATION)
        assert hicon
        self.log(hicon)

        flags = NIF_ICON | NIF_MESSAGE | NIF_TIP | NIF_INFO
        # flags = NIF_ICON | NIF_MESSAGE | NIF_TIP
        # nid = (hwnd, 0, flags, OUR_NOTIFICATION_WM, hicon, self.window_title)
        nid = (hwnd, 0, flags, OUR_NOTIFICATION_WM, hicon, self.window_title, msg, 200, title, NIIF_INFO)

        self.log(nid)

        self.log("NIM_ADD")
        Shell_NotifyIcon(NIM_ADD, nid)
        # Shell_NotifyIcon(NIM_MODIFY, (hwnd, 0, NIF_INFO, OUR_NOTIFICATION_WM, hicon, 'Balloon Tooltip', msg, 200, title, NIIF_INFO))

        self.log("PumpMessages()")
        PumpMessages()  # Handle window messages in main loop until something calls PostQuitMessage

        self.log("NIM_DELETE")
        Shell_NotifyIcon(NIM_DELETE, nid)
