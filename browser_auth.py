import urllib
import urlparse

# noinspection PyPackageRequirements
import wx
# noinspection PyPackageRequirements
import wx.html2

""" Twitch sign-in in an embedded browser to get Auth code """


CLIENT_ID = "pkvo0qdzjzxeapwpf8bfogx050n4bn8"


class MyBrowser(wx.Dialog):
    def __init__(self, debug, *args, **kwds):
        self._debug = debug
        wx.Dialog.__init__(self, *args, **kwds)
        self.SetTitle("twitch-notifier")
        sizer = wx.BoxSizer(wx.VERTICAL)
        browser = wx.html2.WebView.New(self)
        assert isinstance(browser, wx.html2.WebView)

        self.scheme_callbacks = {}

        self.last_callback_url_and_parsed = None

        self.browser = browser
        self.browser.Bind(wx.html2.EVT_WEBVIEW_NAVIGATING, self._on_navigating)
        self.browser.Bind(wx.html2.EVT_WEBVIEW_NAVIGATED, self._on_navigated)

        sizer.Add(self.browser, 1, wx.EXPAND, 10)
        self.SetSizer(sizer)
        self.SetSize((700, 700))

    def set_scheme_callback(self, scheme, callback):
        """
        Set up a callback to be called when the browser navigates to a given scheme
        :type scheme: str
        :type callback: function(str, urlparse.ParseResult)()
        """
        self.scheme_callbacks[scheme] = callback

    # In some implementations we get EVT_WEBVIEW_NAVIGATING for our placeholder URL, in others EVT_WEBVIEW_NAVIGATED.
    # Our use case is just to intercept whichever happens first -- there's no page to actually load, so we
    # don't care about getting in at a particular time w.r.t. the page load.

    def _on_navigated(self, event):
        url = event.GetURL()
        if self._debug:
            print "NAVIGATED %r" % url
        self._do_handle_event(url)

    def _on_navigating(self, event):
        url = event.GetURL()
        if self._debug:
            print "NAVIGATING %r" % url
        self._do_handle_event(url)

    def _do_handle_event(self, url):
        parsed = urlparse.urlparse(url)
        scheme = parsed.scheme
        callback = self.scheme_callbacks.get(scheme)
        if callback is not None and self.last_callback_url_and_parsed != (url, parsed):
            self.last_callback_url_and_parsed = url, parsed
            callback(url, parsed)


def main():
    do_browser()


def do_browser(token_callback=None, scopes=None, debug=True):
    """
    Do a twitch web-based login in a standalone wx.App and call the given callback function with the token
    :type token_callback: func(str)
    :param scopes: list of oauth scopes that will be used with the authentication token.
    Consult the twitch API documentation to see what scopes are required for different APIs.
    The list of permissions that the user will see on the may vary depending on what scopes you request.
    :type scopes: list of str
    :param debug: bool
    """
    app = wx.App()
    dialog = MyBrowser(debug, None, -1)

    if scopes is None:
        scopes = []

    def o_shi_whaddyup(url, parsed):
        assert isinstance(parsed, urlparse.ParseResult)
        # if url.startswith("http://notifier-main.rakslice.net/"):

        fragment = parsed.fragment
        qs = urlparse.parse_qs(fragment)
        tokens = qs["access_token"]
        assert len(tokens) == 1
        token = tokens[0]

        if debug:
            print "done - we visited"
            print url

        dialog.Close()
        app.ExitMainLoop()

        if token_callback is not None:
            token_callback(token)

    dialog.set_scheme_callback("notifier", o_shi_whaddyup)

    redirect_uri = "notifier://main"

    auth_url = get_auth_url(CLIENT_ID, redirect_uri, scopes)

    dialog.browser.LoadURL(auth_url)
    dialog.Show()
    app.MainLoop()


def get_auth_url(client_id, redirect_uri, scopes, state=None):
    """
    Build the authentication url to direct a user to in a browser for authentication
    :type client_id: str
    :type redirect_uri: str
    :type scopes: list of str
    :type state: str or None

    >>> get_auth_url("123456", "http://localhost", ["notifier"])
    'https://api.twitch.tv/kraken/oauth2/authorize?scope=notifier&redirect_uri=http%3A%2F%2Flocalhost&response_type=code&client_id=123456'
    """

    base_url = "https://api.twitch.tv/kraken/oauth2/authorize"
    params = {"response_type": "token", "client_id": client_id, "redirect_uri": redirect_uri, "scope": " ".join(scopes)}
    if state is not None:
        params["state"] = state
    return base_url + "?" + urllib.urlencode(params)


if __name__ == '__main__':
    main()
