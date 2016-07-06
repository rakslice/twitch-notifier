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
    def __init__(self):
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

    def balloon_tip(self, title, msg, callback=None):
        self.last_callback = callback

        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        hwnd = CreateWindow(self.classAtom, "Taskbar", style, 0, 0, win32con.CW_USEDEFAULT, win32con.CW_USEDEFAULT, 0, 0, self.hinst, None)
        UpdateWindow(hwnd)

        hicon = LoadIcon(0, win32con.IDI_APPLICATION)

        flags = NIF_ICON | NIF_MESSAGE | NIF_TIP
        nid = (hwnd, 0, flags, OUR_NOTIFICATION_WM, hicon, 'Tooltip')
        Shell_NotifyIcon(NIM_ADD, nid)
        Shell_NotifyIcon(NIM_MODIFY, (hwnd, 0, NIF_INFO, OUR_NOTIFICATION_WM, hicon, 'Balloon Tooltip', msg, 200, title, NIIF_INFO))

        PumpMessages()  # Handle window messages in main loop until something calls PostQuitMessage
