class OurWindowsBalloonTip(object):
    def __init__(self, main_window):
        """:type main_window: notifier_gui.notifier_gui_main.MainStatusWindowImpl"""
        self.main_window = main_window

    def balloon_tip(self, title, msg, callback=None):
        main_window = self.main_window

        main_window.enqueue_notification(title, msg, callback)
