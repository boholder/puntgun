from typing import ClassVar, List

import reactivex as rx
from reactivex import operators as op

from rules import validate_required_fields_exist, Plan
from rules.config_parser import ConfigParser
from rules.user import User
from rules.user.action_rules import UserActionRule
from rules.user.filter_rules import UserFilterRule
from rules.user.rule_sets import UserSourceRuleAnyOfSet, UserFilterRuleAnyOfSet
from rules.user.source_rules import UserSourceRule


class UserPlan(Plan):
    """
    Represent a user_plan, user processing pipeline.
    """

    _keyword: ClassVar[str] = 'user_plan'
    name: str
    sources: UserSourceRuleAnyOfSet
    filters: UserFilterRuleAnyOfSet
    actions: List[UserActionRule]

    class DefaultAllTriggerUserFilterRule(UserFilterRule):
        def __call__(self, user: User):
            return True

    @classmethod
    def parse_from_config(cls, conf: dict):
        # we won't directly extract values from configuration and assign them to fields,
        # so custom validation is needed.
        validate_required_fields_exist(cls._keyword, conf, ['from', 'do'])

        # need at least one default filter rule to keep plan execution functionally
        if 'that' not in conf:
            conf['that'] = [cls.DefaultAllTriggerUserFilterRule()]

        return cls(name=conf['user_plan'],  # using the keyword field for naming this plan
                   # wrap source rules and filter rules with their rule set
                   # for giving them a default running order
                   sources=ConfigParser.parse({'any_of': conf['from']}, UserSourceRule),
                   filters=ConfigParser.parse({'any_of': conf['that']}, UserFilterRule),
                   actions=[ConfigParser.parse(c, UserActionRule) for c in conf['do']])

    def __call__(self):
        # TODO action 想要的是每个action各衍生一个消费流去消费user
        self.filtering()

    def filtering(self):
        """
        Pass source users to filter chain and combine filter result with origin user instance.
        """
        users = self.sources()
        filter_results = users.pipe(op.filter(self.filters), op.flat_map(lambda x: x))
        return rx.zip(self.sources(), filter_results)
