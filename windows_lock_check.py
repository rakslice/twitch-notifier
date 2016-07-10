
import time
import ctypes

# From: http://timgolden.me.uk/python/win32_how_do_i/see_if_my_workstation_is_locked.html
import win32api

user32 = ctypes.windll.User32
OpenDesktop = user32.OpenDesktopA
CloseDesktop = user32.CloseDesktop
SwitchDesktop = user32.SwitchDesktop
DESKTOP_SWITCHDESKTOP = 0x0100


def check_if_locked():
    h_desktop = OpenDesktop("default", 0, False, DESKTOP_SWITCHDESKTOP)
    result = SwitchDesktop(h_desktop)
    # if h_desktop:
    #     CloseDesktop(h_desktop)
    if result:
        return False
    else:
        return True


def get_idle_time():
    return (win32api.GetTickCount() - win32api.GetLastInputInfo()) / 1000


def check_if_idle(threshold_s=60):
    # From: https://stackoverflow.com/questions/911856/detecting-idle-time-using-python
    idle_time = get_idle_time()
    return idle_time >= threshold_s


if __name__ == "__main__":
    while True:
        print "%s: locked: %s idle: %s" % (time.strftime("%Y/%m/%d %H:%M:%S", time.localtime(time.time())), check_if_locked(),
                                           get_idle_time())
        time.sleep(2)
