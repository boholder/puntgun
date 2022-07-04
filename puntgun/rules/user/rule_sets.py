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
import reactivex as rx
from reactivex import operators as op, Observable

from client import NeedClient
from rules import FromConfig, ConfigParser
from rules.user import User
from rules.user.filter_rules import UserFilterRule
from rules.user.source_rules import UserSourceRule


class UserSourceRuleAnyOfSet(FromConfig, UserSourceRule):
    _keyword = 'any_of'
    rules: [UserSourceRule]

    @classmethod
    def parse_from_config(cls, conf: dict):
        return cls(rules=[ConfigParser.parse(c, UserSourceRule) for c in conf['any_of']])

    def __call__(self) -> Observable[User]:
        # simply merge results together, and remove repeating elements
        return rx.merge(self.rules).pipe(op.distinct())


class UserFilterRuleAllOfSet(FromConfig, UserFilterRule, NeedClient):
    """
    Run immediate rules first, then slow rules.
    If getting any False result while running, short-circuiting return False
    and discard have-not-finish or have-not-run rules' results.

    It also makes rule set itself becomes time-consuming
    and needed to be treated in async way (marked with :class:`NeedClient`).
    """

    _keyword = 'all_of'
    immediate_rules: [UserFilterRule]
    slow_rules: [UserFilterRule]

    @classmethod
    def parse_from_config(cls, conf: dict):
        rules = [ConfigParser.parse(c, UserFilterRule) for c in conf['all_of']]
        # Filter rules that need to communicate with Twitter Server via API
        # will take some time to run judgement and can't return immediately.
        #
        # In some case we can come up a result without knowing all the results,
        # similar to short-circuiting evaluation in logical expressions.
        # So it's good to divide these two types and process them independently.
        return cls(slow_rules=[r for r in rules if isinstance(r, NeedClient)],
                   immediate_rules=[r for r in rules if not isinstance(r, NeedClient)])

    def __call__(self, user: User):
        # In ideal case, we can find the result without consuming any API resource.
        for r in self.immediate_rules:
            if not r(user):
                return rx.just(False)

        return rx.of(self.slow_rules(user)).pipe(
            # each slow rule returns an observable contains only one boolean value.
            op.flat_map(lambda x: x),
            # expect first False result or return True finally.
            op.first_or_default(lambda e: e is False, True)
        )


class UserFilterRuleAnyOfSet(FromConfig, UserFilterRule, NeedClient):
    """
    Similar like :class:`UserFilterRuleAllOfSet`,
    but looking for the first True result for short-circuiting.
    """
    _keyword = 'any_of'
    immediate_rules: [UserFilterRule]
    slow_rules: [UserFilterRule]

    @classmethod
    def parse_from_config(cls, conf: dict):
        rules = [ConfigParser.parse(c, UserFilterRule) for c in conf['any_of']]
        return cls(slow_rules=[r for r in rules if isinstance(r, NeedClient)],
                   immediate_rules=[r for r in rules if not isinstance(r, NeedClient)])

    def __call__(self, user: User):
        for r in self.immediate_rules:
            if r(user):
                return rx.just(True)

        return rx.of(self.slow_rules(user)).pipe(
            op.flat_map(lambda x: x),
            op.first_or_default(lambda e: e is True, False)
        )
