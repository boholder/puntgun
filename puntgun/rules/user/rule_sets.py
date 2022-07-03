"""
A rule set is an auxiliary type of rule used to organize the execution order
by aggregating the results of a group of rules into a single result.
The rule set itself can be contained inside another rule set,
so you can make complex cascading execution order tree with them.
It's the composite pattern I guess.

Currently, there are two logical rule sets:
all-of(AND), any-of(OR)

Source rule type and filter rule type gets different implements of these two rule sets
(because different rule type has different type of result to aggregating).
Action rule type doesn't have any rule set because it's the latest execution step.
"""
from rules import FromConfig
from rules.user.source_rules import UserSourceRule


class UserSourceRuleAllOfSet(FromConfig, UserSourceRule):
    _keyword = 'all_of'
    rules: [UserSourceRule]

    @classmethod
    def parse_from_config(cls, conf: dict):
        return cls(rules=conf['all_of'])

    def __call__(self):
        return


class UserSourceRuleAnyOfSet(FromConfig, UserSourceRule):
    _keyword = 'any_of'
    rules: [UserSourceRule]

    @classmethod
    def parse_from_config(cls, conf: dict):
        return cls(rules=conf['any_of'])


class UserFilterRuleAllOfSet(FromConfig, UserSourceRule):
    _keyword = 'all_of'
    rules: [UserSourceRule]

    @classmethod
    def parse_from_config(cls, conf: dict):
        return cls(rules=conf['all_of'])


class UserFilterRuleAnyOfSet(FromConfig, UserSourceRule):
    _keyword = 'any_of'
    rules: [UserSourceRule]

    @classmethod
    def parse_from_config(cls, conf: dict):
        return cls(rules=conf['any_of'])
