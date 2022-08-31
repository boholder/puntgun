"""
Some user filter rules have simular functions and contain same delegating agents inside them,
"follower rule" and "following rule" for example.
Most functions of these rules are tested when testing delegating agents,
so only basic "parsing" logic will be tested in this test module.
"""
import datetime
from typing import List

import pytest
from dynaconf import Dynaconf

from puntgun.rules.config_parser import ConfigParser
from puntgun.rules.user import User
from puntgun.rules.user.filter_rules import UserFilterRule, TextMatchUserFilterRule


def test_follower_user_filter_rule():
    r = ConfigParser.parse({"follower": {"less_than": 20, "more_than": 10}}, UserFilterRule)
    assert r(User(followers_count=15))
    assert not r(User(followers_count=0))
    assert not r(User(followers_count=30))


def test_follower_less_than_filter_rule():
    r = ConfigParser.parse({"follower_less_than": 10}, UserFilterRule)
    assert r(User(followers_count=5))
    assert not r(User(followers_count=20))


def test_following_user_filter_rule():
    r = ConfigParser.parse({"following": {"less_than": 20, "more_than": 10}}, UserFilterRule)
    assert r(User(following_count=15))
    assert not r(User(following_count=0))
    assert not r(User(following_count=30))


def test_following_more_than_filter_rule():
    r = ConfigParser.parse({"following_more_than": 10}, UserFilterRule)
    assert r(User(following_count=20))
    assert not r(User(following_count=5))


def test_created_filter_rule():
    time = datetime.datetime.utcnow()
    timedelta = datetime.timedelta(hours=1)
    # -1 <-> 1
    r = ConfigParser.parse({"created": {"after": time - timedelta, "before": time + timedelta}}, UserFilterRule)
    # 0, pass
    assert r(User(created_at=time))
    # 2, -2, fail
    assert not r(User(created_at=time + timedelta * 2))
    assert not r(User(created_at=time - timedelta * 2))


def test_created_after_filter_rule():
    time = datetime.datetime.utcnow()
    r = ConfigParser.parse({"created_after": time}, UserFilterRule)
    assert r(User(created_at=time + datetime.timedelta(hours=1)))
    assert not r(User(created_at=time - datetime.timedelta(hours=1)))


def test_created_within_days_filter_rule():
    time = datetime.datetime.utcnow()
    r = ConfigParser.parse({"created_within_days": 1}, UserFilterRule)
    assert r(User(created_at=time))
    assert not r(User(created_at=time - datetime.timedelta(days=2)))


class TestTextMatchUserFilterRule:
    """
    Start from letting dynaconf load the config file,
    to check character escaping concern of regex.
    """

    @pytest.fixture
    def config_plan_file_with(self, tmp_path):
        def wrapper(content: str):
            file = tmp_path.joinpath("f.yml")
            with open(file, "w", encoding="utf-8") as f:
                f.write(content)
            return Dynaconf(settings_files=[file])

        return wrapper

    @pytest.fixture
    def run_assert(self, config_plan_file_with):
        def wrapper(regex: str, text: str, expect: bool):
            def user_texts(_texts: List[str]):
                words = [t if t else "" for t in _texts[0:3]]
                return User(name=words[0], description=words[1], pinned_tweet_text=words[2])

            # let the regex goes through dynaconf
            _regex = config_plan_file_with(f"re: {regex}").get("re")
            rule = TextMatchUserFilterRule.parse_from_config({"profile_text_matches": _regex})

            # rotate valid text to different position to represent different rules text
            texts = [text, "", ""]
            for _ in range(3):
                texts = texts[1:] + [texts[0]]
                assert rule(user_texts(texts)) == expect

        return wrapper

    def test_match_without_escaping_concern(self, run_assert):
        run_assert("a", "abc", True)
        run_assert("abc", "def", False)

        run_assert("你好", "你好", True)
        run_assert("Здравствуйте", "Здравствуйте", True)

    def test_yaml_escaping(self, run_assert):
        # escaping ":" and "-"

        # no escaping will cause error
        with pytest.raises(Exception):
            run_assert("- a: b", "- a: b", True)

        # escape with quote
        run_assert("'- a: b'", "- a: b", True)
        run_assert('"- a: b"', "- a: b", True)

        # escaping quote symbol itself (using another quote symbol)
        run_assert("'\"'", '"', True)
        run_assert('"\'"', "'", True)

    def test_python_backslash_escaping(self, run_assert):
        # backslash as part of "\d"
        run_assert(r"\d+", "123", True)

        # literal backslash without quote
        run_assert(r"^a\\b$", r"a\b", True)
        # literal backslash with quote
        run_assert(r"'^a\\b$'", r"a\b", True)
        # don't know why we need double amount of backslash when using double quote
        run_assert(r'"^a\\\\b$"', r"a\b", True)


def test_following_count_ratio_filter_rule():
    r = ConfigParser.parse({"following_count_ratio": {"less_than": 2, "more_than": 1}}, UserFilterRule)
    assert r(User(followers_count=3, following_count=2))
    assert not r(User(followers_count=4, following_count=2))
    assert not r(User(followers_count=1, following_count=2))


def test_following_count_ratio_less_than_filter_rule():
    r = ConfigParser.parse({"following_count_ratio_less_than": 1}, UserFilterRule)
    assert r(User(followers_count=1, following_count=2))
    assert not r(User(followers_count=3, following_count=2))


def test_tweet_count_filter_rule():
    r = ConfigParser.parse({"tweet_count": {"less_than": 20, "more_than": 10}}, UserFilterRule)
    assert r(User(tweet_count=15))
    assert not r(User(tweet_count=0))
    assert not r(User(tweet_count=30))


def test_tweet_count_less_than_filter_rule():
    r = ConfigParser.parse({"tweet_count_less_than": 10}, UserFilterRule)
    assert r(User(tweet_count=5))
    assert not r(User(tweet_count=20))
