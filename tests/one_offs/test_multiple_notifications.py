import sys

import time

import windows_10_toast_notifications


def main():
    notifier = windows_10_toast_notifications.WindowsBalloonTip(debug_output=True)

    pause()

    for i in xrange(3):
        text = "this is notification %s" % i
        title = "test multiple notifications %s" % i
        notifier.balloon_tip(title, text)
        time.sleep(0.1)

    pause()

    notifier.close()


def pause(msg="pause, press return"):
    print msg
    sys.stdin.readline()


if __name__ == "__main__":
    main()
