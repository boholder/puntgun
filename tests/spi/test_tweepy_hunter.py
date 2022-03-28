import unittest
from unittest import TestCase

import reactivex as rx

from puntgun.spi.twitter_client.tweepy_hunter import TweepyHunter


class TestTweepyHunter(TestCase):
    """
    Mainly testing tweepy apis' result for development.
    """

    @unittest.skip("test for development")
    def test_get_user(self):
        def consume(response):
            print(response)

        client = TweepyHunter.singleton()
        client \
            .observe(username=rx.just("TwitterDev")) \
            .subscribe(on_next=consume,
                       on_error=lambda e: print(e))

    # TODO 用Mock把tweepy mock了，测Hunter的功能。
