"""
A rule set is an auxiliary type of rule used to organize the execution order
by aggregating the results of a group of rules into a single result.
The rule set itself can be contained inside another rule set,
so you can make complex cascading execution order tree with them.
It's the composite pattern I guess.

Currently, there are two logical rule sets:
all_of(AND), any_of(OR)

Different rule type has different type of result to aggregating,
so they get different implements:

1. source rule: any_of
(And it's its default (and only) execution order - combine results together into one set.)

2. filter rule: all_of, any_of
(There will be more rule set for filter rule type.)

Action rule type doesn't have any rule set because
it's the latest execution step and there's no need for aggregating action results.
"""
from typing import List

import reactivex as rx
from pydantic import BaseModel
from reactivex import operators as op, Observable

from client import NeedClient
from rules import ConfigParser
from rules.user import User
from rules.user.filter_rules import UserFilterRule
from rules.user.source_rules import UserSourceRule


class UserSourceRuleAnyOfSet(UserSourceRule):
    _keyword = 'any_of'
    rules: List[UserSourceRule]

    @classmethod
    def parse_from_config(cls, conf: dict):
        return cls(rules=[ConfigParser.parse(c, UserSourceRule) for c in conf['any_of']])

    def __call__(self) -> Observable[User]:
        # simply merge results together
        return rx.merge(*[rx.start(r) for r in self.rules]).pipe(
            # extract user source rules' results
            op.flat_map(lambda x: x),
            # remove repeating elements
            op.distinct()
        )


class UserFilterRuleSet(BaseModel):
    immediate_rules: List[UserFilterRule]
    slow_rules: List[UserFilterRule]

    @staticmethod
    def construct(cls, rules: [UserFilterRule]):
        return cls(slow_rules=[r for r in rules if isinstance(r, NeedClient)],
                   immediate_rules=[r for r in rules if not isinstance(r, NeedClient)])

    @staticmethod
    def execution_wrapper(u: User, rule: UserFilterRule):
        """
        Because the rx.start() only accept no-param functions as its parameter,
        but user filter rule need a user instance param for judgement.
        """

        def run_the_rule():
            return rule(u)

        return run_the_rule


class UserFilterRuleAllOfSet(UserFilterRuleSet, UserFilterRule, NeedClient):
    """
    Run immediate rules first, then slow rules.
    If getting any False result while running, short-circuiting return False
    and discard have-not-finish or have-not-run rules' results.

    It also makes rule set itself becomes time-consuming
    and needed to be treated as a slow filter rule (marked with :class:`NeedClient`).
    """

    _keyword = 'all_of'

    @classmethod
    def parse_from_config(cls, conf: dict):
        return UserFilterRuleSet.construct(cls, [ConfigParser.parse(c, UserFilterRule) for c in conf['all_of']])

    def __call__(self, user: User):
        # In ideal case, we can find the result without consuming any API resource.
        for r in self.immediate_rules:
            if not r(user):
                return rx.just(False)

        return rx.merge(*[rx.start(self.execution_wrapper(user, r)) for r in self.slow_rules]).pipe(
            # each slow rule returns an observable that contains only one boolean value.
            op.flat_map(lambda x: x),
            # expect first False result or return True finally.
            op.first_or_default(lambda e: e is False, True)
        )


class UserFilterRuleAnyOfSet(UserFilterRuleSet, UserFilterRule, NeedClient):
    """
    Similar like :class:`UserFilterRuleAllOfSet`,
    but looking for the first True result for short-circuiting.
    """
    _keyword = 'any_of'

    @classmethod
    def parse_from_config(cls, conf: dict):
        return UserFilterRuleSet.construct(cls, [ConfigParser.parse(c, UserFilterRule) for c in conf['any_of']])

    def __call__(self, user: User):
        """I can endure repeating twice"""
        for r in self.immediate_rules:
            if r(user):
                return rx.just(True)

        return rx.merge(*[rx.start(self.execution_wrapper(user, r)) for r in self.slow_rules]).pipe(
            op.flat_map(lambda x: x), op.first_or_default(lambda e: e is True, False)
        )
