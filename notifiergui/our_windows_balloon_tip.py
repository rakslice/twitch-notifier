class OurWindowsBalloonTip(object):
    def __init__(self, main_window):
        """:type main_window: MainStatusWindowImpl"""
        self.main_window = main_window

    def balloon_tip(self, title, msg, callback=None):
        self.main_window.set_balloon_click_callback(callback)

        icon = self.main_window.GetIcon()
        self.main_window.toolbar_icon.ShowBalloon(title, msg, 0, icon.GetHandle())
