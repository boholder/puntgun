"""
A rule set is an auxiliary type of rule used to organize the execution order,
aggregate the results of a group of rules into a single result.

The rule set itself can be contained inside another rule set,
so you can make complex cascading execution order tree with them.
It's the composite pattern I guess.
"""
from typing import Callable, List, Type

import reactivex as rx
from loguru import logger
from pydantic import BaseModel
from reactivex import Observable
from reactivex import operators as op

from puntgun.client import NeedClientMixin
from puntgun.rules.config_parser import ConfigParser
from puntgun.rules.data import RuleResult, User
from puntgun.rules.user.action_rules import UserActionRule
from puntgun.rules.user.filter_rules import UserFilterRule
from puntgun.rules.user.source_rules import UserSourceRule


class UserSourceRuleResultMergingSet(UserSourceRule):
    """
    * Only be used inside user plan.
    Simply merge user source rule results together into one :class:`Observable`.
    """

    _keyword = "any_of"
    rules: List[UserSourceRule]

    @classmethod
    def parse_from_config(cls, conf: dict) -> "UserSourceRuleResultMergingSet":
        return cls(rules=[ConfigParser.parse(c, UserSourceRule) for c in conf["any_of"]])

    def __call__(self) -> Observable[User]:
        users_observables = [rx.start(r) for r in self.rules]
        return rx.merge(*users_observables).pipe(
            # extract user source rules' results
            op.flat_map(lambda x: x),
            # log for debug
            op.do(rx.Observer(on_next=lambda u: logger.debug("Source user before distinct: {}", u))),
            # remove repeating elements
            op.distinct(),
        )


class UserFilterRuleSet(BaseModel):
    immediate_rules: List[UserFilterRule]
    slow_rules: List[UserFilterRule]

    @staticmethod
    def divide_and_construct(cls: Type["UserFilterRuleSet"], rules: List[UserFilterRule]) -> "UserFilterRuleSet":
        return cls(
            slow_rules=[r for r in rules if isinstance(r, NeedClientMixin)],
            immediate_rules=[r for r in rules if not isinstance(r, NeedClientMixin)],
        )


def execution_wrapper(u: User, rule: UserFilterRule | UserActionRule) -> Callable:
    """
    Because the rx.start() only accept no-param functions as its parameter,
    but user filter rule need a user instance param for judgement.
    """

    def run_the_rule() -> RuleResult:
        return rule(u)

    return run_the_rule


class UserFilterRuleAllOfSet(UserFilterRuleSet, UserFilterRule, NeedClientMixin):
    """
    Run immediate rules first, then slow rules.
    If getting any False result while running, short-circuiting return False
    and discard have-not-finish or have-not-run rules' results.

    It also makes rule set itself becomes time-consuming
    and needed to be treated as a slow filter rule (marked with :class:`NeedClient`).
    """

    _keyword = "all_of"

    @classmethod
    def parse_from_config(cls, conf: dict) -> "UserFilterRuleSet":
        return UserFilterRuleSet.divide_and_construct(
            cls, [ConfigParser.parse(c, UserFilterRule) for c in conf["all_of"]]
        )

    def __call__(self, user: User) -> Observable[RuleResult]:
        # In ideal case, we can find the result without consuming any API resource.
        for r in self.immediate_rules:
            result = r(user)
            if not result:
                return rx.just(result)

        rule_result_observables = [rx.start(execution_wrapper(user, r)) for r in self.slow_rules]
        return rx.merge(*rule_result_observables).pipe(
            # each slow rule returns an observable that contains only one boolean value.
            op.flat_map(lambda x: x),
            # expect first False result or return True finally.
            op.first_or_default(lambda e: bool(e) is False, RuleResult.true(self)),
        )


class UserFilterRuleAnyOfSet(UserFilterRuleSet, UserFilterRule, NeedClientMixin):
    """
    Similar like :class:`UserFilterRuleAllOfSet`,
    but looking for the first True result for short-circuiting.
    """

    _keyword = "any_of"

    @classmethod
    def parse_from_config(cls, conf: dict) -> "UserFilterRuleSet":
        return UserFilterRuleSet.divide_and_construct(
            cls, [ConfigParser.parse(c, UserFilterRule) for c in conf["any_of"]]
        )

    def __call__(self, user: User) -> Observable[RuleResult]:
        """I can endure repeating twice"""
        for r in self.immediate_rules:
            result = r(user)
            if result:
                return rx.just(result)

        rule_result_observables = [rx.start(execution_wrapper(user, r)) for r in self.slow_rules]
        return rx.merge(*rule_result_observables).pipe(
            op.flat_map(lambda x: x), op.first_or_default(lambda e: bool(e) is True, RuleResult.false(self))
        )


class UserActionRuleResultCollectingSet(UserActionRule):
    """
    * Only be used inside user plan.
    Run action rules and collect their results (whether succeeded)
    into one set for latter result aggregating and recording.
    """

    _keyword = "all_of"
    rules: List[UserActionRule]

    @classmethod
    def parse_from_config(cls, conf: dict) -> "UserActionRuleResultCollectingSet":
        return cls(rules=[ConfigParser.parse(c, UserActionRule) for c in conf["all_of"]])

    def __call__(self, user: User) -> Observable[List[RuleResult]]:
        action_results = [rx.start(execution_wrapper(user, r)) for r in self.rules]
        return rx.merge(*action_results).pipe(
            # collect them into one list
            op.buffer_with_count(len(self.rules))
        )
