"""
A rule set is an auxiliary type of rule used to organize the execution order,
aggregate the results of a group of rules into a single result.

The rule set itself can be contained inside another rule set,
so you can make complex cascading execution order tree with them.
It's the composite pattern I guess.
"""
from typing import List

import reactivex as rx
from pydantic import BaseModel
from reactivex import operators as op, Observable

from client import NeedClient
from rules import RuleResult
from rules.config_parser import ConfigParser
from rules.user import User
from rules.user.action_rules import UserActionRule
from rules.user.filter_rules import UserFilterRule
from rules.user.source_rules import UserSourceRule


class UserSourceRuleResultMergingSet(UserSourceRule):
    """
    * Only be used inside user plan.
    Simply merge user source rule results together into one :class:`Observable`.
    """
    _keyword = 'any_of'
    rules: List[UserSourceRule]

    @classmethod
    def parse_from_config(cls, conf: dict):
        return cls(rules=[ConfigParser.parse(c, UserSourceRule) for c in conf['any_of']])

    def __call__(self) -> Observable[User]:
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
    def divide_and_construct(cls, rules: [UserFilterRule]):
        return cls(slow_rules=[r for r in rules if isinstance(r, NeedClient)],
                   immediate_rules=[r for r in rules if not isinstance(r, NeedClient)])


def execution_wrapper(u: User, rule: UserFilterRule | UserActionRule):
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
        return UserFilterRuleSet.divide_and_construct(
            cls, [ConfigParser.parse(c, UserFilterRule) for c in conf['all_of']])

    def __call__(self, user: User) -> Observable[RuleResult]:
        # In ideal case, we can find the result without consuming any API resource.
        for r in self.immediate_rules:
            result = r(user)
            if not result:
                return rx.just(result)

        return rx.merge(*[rx.start(execution_wrapper(user, r)) for r in self.slow_rules]).pipe(
            # each slow rule returns an observable that contains only one boolean value.
            op.flat_map(lambda x: x),
            # expect first False result or return True finally.
            op.first_or_default(lambda e: bool(e) is False, RuleResult.true(self))
        )


class UserFilterRuleAnyOfSet(UserFilterRuleSet, UserFilterRule, NeedClient):
    """
    Similar like :class:`UserFilterRuleAllOfSet`,
    but looking for the first True result for short-circuiting.
    """
    _keyword = 'any_of'

    @classmethod
    def parse_from_config(cls, conf: dict):
        return UserFilterRuleSet.divide_and_construct(
            cls, [ConfigParser.parse(c, UserFilterRule) for c in conf['any_of']])

    def __call__(self, user: User) -> Observable[RuleResult]:
        """I can endure repeating twice"""
        for r in self.immediate_rules:
            result = r(user)
            if result:
                return rx.just(result)

        return rx.merge(*[rx.start(execution_wrapper(user, r)) for r in self.slow_rules]).pipe(
            op.flat_map(lambda x: x),
            op.first_or_default(lambda e: bool(e) is True, RuleResult.false(self))
        )


class UserActionRuleResultCollectingSet(UserActionRule):
    """
    * Only be used inside user plan.
    Run action rules and collect their results (whether succeeded)
    into one set for latter result aggregating and recording.
    """
    _keyword = 'all_of'
    rules: List[UserActionRule]

    @classmethod
    def parse_from_config(cls, conf: dict):
        return cls(rules=[ConfigParser.parse(c, UserSourceRule) for c in conf['all_of']])

    def __call__(self, user: User) -> Observable[List[RuleResult]]:
        # TODO untested
        return rx.merge(*[rx.start(execution_wrapper(user, r)) for r in self.rules]).pipe(
            op.flat_map(lambda x: x),
            # collect them into one list
            op.buffer_with_count(len(self.rules))
        )
