from win32gui import *
import win32con

NIIF_USER = 0x4

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
    def __init__(self, window_title="Taskbar", debug_output=False, icon_filename=None):
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
        self.hicon = None

        self.basic_flags = None

        self.nid = None
        self.hiding_nid = None

        self.window_title = window_title
        self.message_icon_flags = None

        self.init_window(window_title, icon_filename=icon_filename)

    # noinspection PyUnusedLocal,PyMethodMayBeStatic
    def on_destroy(self, hwnd, msg, wparam, lparam):
        # nid = (hwnd, 0)
        # Shell_NotifyIcon(NIM_DELETE, nid)
        self._pqm("on_destroy")

    def _pqm(self, source):
        self.log("%s before PQM sleep(1)" % source)
        # rubber band
        self.log("%s PostQuitMessage(0)" % source)
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
            self._pqm("1029")
        elif lparam == 1028:
            self._pqm("1028")

    def init_window(self, window_title, icon_filename=None):
        assert window_title is not None

        assert self.hwnd is None, "already initialized"

        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        hwnd = CreateWindow(self.classAtom, window_title, style, 0, 0, win32con.CW_USEDEFAULT, win32con.CW_USEDEFAULT, 0, 0, self.hinst, None)
        UpdateWindow(hwnd)

        if icon_filename is not None:
            # from https://stackoverflow.com/questions/13187453/load-window-icon-dynamically
            hicon = LoadImage(  # returns a HANDLE so we have to cast to HICON
                None,             # hInstance must be NULL when loading from a file
                icon_filename,   # the icon file name
                win32con.IMAGE_ICON,       # specifies that the file is an icon
                0,                # width of the image (we'll specify default later on)
                0,                # height of the image
                win32con.LR_LOADFROMFILE |  # we want to load a file (as opposed to a resource)
                win32con.LR_DEFAULTSIZE |   # default metrics based on the type (IMAGE_ICON, 32x32)
                win32con.LR_SHARED         # let the system release the handle when it's no longer used
            )
        else:
            hicon = LoadIcon(0, win32con.IDI_APPLICATION)

        assert hicon
        self.log(hicon)

        # Let's choose appropriate dwInfoFlags for when we're showing the message to determine the icon that will appear in the notification box
        if icon_filename is not None:
            # also use the custom icon for the message
            self.message_icon_flags = NIIF_USER
        else:
            # info icon
            self.message_icon_flags = NIIF_INFO

        self.basic_flags = NIF_ICON | NIF_MESSAGE | NIF_TIP
        nid = (hwnd, 0, self.basic_flags, OUR_NOTIFICATION_WM, hicon, self.window_title)
        """ NOTIFYICONDATA structure: https://msdn.microsoft.com/en-us/library/windows/desktop/bb773352(v=vs.85).aspx """

        self.log("NIM_ADD")
        Shell_NotifyIcon(NIM_ADD, nid)

        self.hwnd = hwnd
        self.hicon = hicon

        self.nid = nid
        self.hiding_nid = nid

    def log(self, msg):
        if self.debug_output:
            print msg

    def balloon_tip(self, title, msg, callback=None):
        self.last_callback = callback

        hwnd = self.hwnd
        hicon = self.hicon
        self.log("hwnd: %r" % hwnd)

        assert self.message_icon_flags is not None
        # NOTIFYICONDATA structure: https://msdn.microsoft.com/en-us/library/windows/desktop/bb773352(v=vs.85).aspx
        new_nid = (hwnd, 0, NIF_INFO, OUR_NOTIFICATION_WM, hicon, 'Balloon Tooltip', msg, 200, title, self.message_icon_flags)
        Shell_NotifyIcon(NIM_MODIFY, new_nid)

        self.log("PumpMessages()")
        PumpMessages()  # Handle window messages in main loop until something calls PostQuitMessage

    def close(self):
        nid = self.nid

        self.log("NIM_DELETE")
        Shell_NotifyIcon(NIM_DELETE, nid)
