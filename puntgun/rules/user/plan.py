from typing import ClassVar, List

import reactivex as rx
from pydantic import BaseModel
from reactivex import operators as op

from recorder import Recordable, Record
from rules import validate_required_fields_exist, Plan, RuleResult
from rules.config_parser import ConfigParser
from rules.user import User
from rules.user.action_rules import UserActionRule
from rules.user.filter_rules import UserFilterRule
from rules.user.rule_sets import UserSourceRuleResultMergingSet, UserFilterRuleAnyOfSet, \
    UserActionRuleResultCollectingSet
from rules.user.source_rules import UserSourceRule


class UserPlanResult(BaseModel, Recordable):
    """TODO"""
    user: User
    filtering_result: RuleResult
    action_results: List[RuleResult]

    def to_record(self) -> Record:
        pass

    @staticmethod
    def parse_from_record(record: Record):
        pass


class UserPlan(Plan):
    """
    Represent a user_plan, user processing pipeline.
    """

    _keyword: ClassVar[str] = 'user_plan'
    name: str
    sources: UserSourceRuleResultMergingSet
    filters: UserFilterRuleAnyOfSet
    actions: UserActionRuleResultCollectingSet

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
            conf['that'] = [{'placeholder_user_filter_rule': {}}]

        return cls(name=conf['user_plan'],  # using the keyword field for naming this plan
                   # wrap rules with their rule set
                   # for giving them a default running order
                   sources=ConfigParser.parse({'any_of': conf['from']}, UserSourceRule),
                   filters=ConfigParser.parse({'any_of': conf['that']}, UserFilterRule),
                   actions=ConfigParser.parse({'all_of': conf['do']}, UserActionRule))

    def __call__(self):
        """
        Run this plan, return users that triggered filter rules and action rules execution results.
        result explanation: (<user instance>, <filtering result>, <action results>)
        :return: rx.Observable(Tuple[ Tuple[User, RuleResult], List[RuleResult] ])
        """
        users_need_to_be_performed_with_filtering_result = self._filtering().pipe(
            # take users that triggered filter rules
            op.filter(lambda z: bool(z[1]) is True)
        )

        action_results = users_need_to_be_performed_with_filtering_result.pipe(
            # extract user instance from tuple
            op.map(lambda z: z[0]),
            # apply actions on users
            op.map(self.actions),
            # flat_map() is needed
            op.flat_map(lambda x: x),
        )

        return rx.zip(users_need_to_be_performed_with_filtering_result, action_results).pipe(
            # put three values under one tuple, no nested
            op.map(lambda zipped: (zipped[0][0], zipped[0][1], zipped[1]))
        )

    def _filtering(self):
        """
        Pass source users to filter chain and combine filtering result with origin user instance.
        result explanation: (<user instance>, <filtering result>)
        :return: rx.Observable(Tuple[User, RuleResult])
        """

        users = self.sources()
        # flat_map() is needed because calling UserFilterRuleAnyOfSet will return Observable[RuleResult]
        filter_results = users.pipe(op.map(self.filters), op.flat_map(lambda x: x))
        return rx.zip(users, filter_results)
