import argparse
import pprint
import urllib
from HTMLParser import HTMLParser

# noinspection PyPackageRequirements
import time
import twitch.queries
# noinspection PyPackageRequirements
import twitch.api.v3

import browser_auth
from twitch_notifier_main import paged_query_iterator, convert_iso_time


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ref",
                        help="Some kind of reference to a time",
                        required=True,
                        )
    parser.add_argument("--channel",
                        help="The twitch channel to look up VODs in",
                        )
    return parser.parse_args()


class TweetTimeParser(HTMLParser):
    def __init__(self):
        self.tweet_time = None
        self.twitter_timeline_link = None
        HTMLParser.__init__(self)

    @staticmethod
    def get_classes(attrs):
        if "class" not in attrs:
            return []
        else:
            return attrs["class"].split()

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "span":
            attrs_dict = dict(attrs)
            if "js-short-timestamp" in self.get_classes(attrs_dict):
                self.tweet_time = int(attrs_dict["data-time"])
        if tag.lower() == "a":
            attrs_dict = dict(attrs)
            if "twitter-timeline-link" in self.get_classes(attrs_dict):
                self.twitter_timeline_link = attrs_dict["data-expanded-url"]


def url_contents(url):
    handle = urllib.urlopen(url)
    try:
        return handle.read()
    finally:
        handle.close()


def get_time_from_tweet(tweet_url):
    content = url_contents(tweet_url)
    parser = TweetTimeParser()
    content = content.decode("utf-8")
    parser.feed(content)
    timeline_link = parser.twitter_timeline_link
    if timeline_link is not None:
        timeline_link = timeline_link.lower()
    return parser.tweet_time, timeline_link


def epoch_to_local_pretty(t):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t))


def main_authed(token, options):
    print "**********************************************************"
    print ""
    authorization = "OAuth %s" % token
    # noinspection PyProtectedMember
    twitch.queries._v3_headers["Authorization"] = authorization
    channel_name = options.channel

    ref = options.ref
    ref_epoch = None
    if ref.startswith("https://twitter.com/"):
        print "The ref seems like it might be a tweet"
        tweet_time, timeline_link = get_time_from_tweet(ref)
        ref_epoch = tweet_time
        print "Referred to time is %s" % epoch_to_local_pretty(tweet_time)

        if timeline_link is not None:
            print "Tweet has timeline link to %s" % timeline_link
            twitch_pref = "http://twitch.tv/"
            if channel_name is None and timeline_link is not None and timeline_link.startswith(twitch_pref):
                channel_name = timeline_link[len(twitch_pref):].split("/", 1)[0]
                print "Using channel name %s" % channel_name
    else:
        ref_epoch = convert_iso_time(ref)

    assert ref_epoch is not None, "could not find ref time"
    assert channel_name is not None, "could not find a twitch channel reference; pass --channel channelname to specify"

    pp = pprint.PrettyPrinter(indent=2)

    results = paged_query_iterator(twitch.api.v3.videos.by_channel, name=channel_name, results_list_key="videos",
                                   broadcasts="true")
    for video in results:

        start_time = convert_iso_time(video["recorded_at"])
        end_time = start_time + video["length"]
        print "Video %r from %s to %s" % (video["title"], epoch_to_local_pretty(start_time), epoch_to_local_pretty(end_time))

        if start_time <= ref_epoch <= end_time:
            print "^^^^ ref in this video"

            url = video["url"]

            seconds_from_start = ref_epoch - start_time
            min_from_start = seconds_from_start / 60

            url_with_time = url + "?t=%sm%ss" % (min_from_start, seconds_from_start % 60)

            print "time link: %s" % url_with_time
            # pp.pprint(video)
            break
    else:
        print "Ref time was not in a video"


def main():
    options = parse_args()

    # authenticate
    print "*********** Opening browser popup for auth ***************"
    browser_auth.do_browser(lambda token: main_authed(token, options))


if __name__ == "__main__":
    main()
