from typing import ClassVar, List

import reactivex as rx
from loguru import logger
from reactivex import Observable
from reactivex import operators as op

from puntgun import rules
from puntgun.record import Record, Recordable
from puntgun.rules import Plan, RuleResult
from puntgun.rules.config_parser import ConfigParser
from puntgun.rules.user import User
from puntgun.rules.user.action_rules import UserActionRule
from puntgun.rules.user.filter_rules import UserFilterRule
from puntgun.rules.user.rule_sets import (
    UserActionRuleResultCollectingSet,
    UserFilterRuleAnyOfSet,
    UserSourceRuleResultMergingSet,
)
from puntgun.rules.user.source_rules import UserSourceRule


class UserPlanResult(Recordable):
    plan_id: int
    user: User
    filtering_result: RuleResult
    action_results: List[RuleResult]

    def __init__(self, plan_id: int, user: User, filtering_result: RuleResult, action_results: List[RuleResult]):
        self.plan_id = plan_id
        self.user = user
        self.filtering_result = filtering_result
        self.action_results = action_results

    def to_record(self) -> Record:
        # Only the user id, action rules keywords and results ("done" field) are critical for "undo" operations,
        # other information for letting user know what happened.
        #
        # Thanks to the pydantic library, the "str(r.rule)" will output every field's value of the rule,
        # along with rule's keyword, user can figure out what this rule's meaning is.
        return Record(
            type="user_plan_result",
            data={
                "plan_id": self.plan_id,
                "user": {"id": self.user.id, "username": self.user.username},
                "decisive_filter_rule": {
                    "keyword": self.filtering_result.rule.keyword(),
                    "value": str(self.filtering_result.rule),
                },
                "action_rule_results": [
                    {"keyword": r.rule.keyword(), "value": str(r.rule), "done": r.result} for r in self.action_results
                ],
            },
        )

    @staticmethod
    def parse_from_record(record: Record):
        user: dict = record.data.get("user", {})
        action_rule_results: list = record.data.get("action_rule_results", [])
        return UserPlanResult(
            plan_id=record.data.get("plan_id", 0),
            user=User(id=user.get("id"), username=user.get("username")),
            # we don't need this (while parsing from record for "undo" operations)
            filtering_result=RuleResult.true(None),
            action_results=[
                RuleResult(rule=ConfigParser.parse({r.get("keyword"): {}}, UserActionRule), result=r.get("done"))
                for r in action_rule_results
            ],
        )


class UserPlan(Plan):
    """
    Represent a user_plan, user processing pipeline.
    """

    _keyword: ClassVar[str] = "user_plan"
    sources: UserSourceRuleResultMergingSet
    filters: UserFilterRuleAnyOfSet
    actions: UserActionRuleResultCollectingSet

    class DefaultAllTriggerUserFilterRule(UserFilterRule):
        def __call__(self, user: User):
            return True

    @classmethod
    def parse_from_config(cls, conf: dict):
        # we won't directly extract values from configuration and assign them to fields,
        # so custom validation is needed
        # as we can't use pydantic library's validating function on fields.
        rules.validate_required_fields_exist(cls._keyword, conf, ["from", "do"])

        # need at least one default filter rule to keep plan execution functionally
        if "that" not in conf:
            conf["that"] = [{"placeholder_user_filter_rule": {}}]

        return cls(
            name=conf["user_plan"],  # using the keyword field for naming this plan
            # wrap rules with their rule set
            # for giving them a default running order
            sources=ConfigParser.parse({"any_of": conf["from"]}, UserSourceRule),
            filters=ConfigParser.parse({"any_of": conf["that"]}, UserFilterRule),
            actions=ConfigParser.parse({"all_of": conf["do"]}, UserActionRule),
        )

    def __call__(self) -> Observable[UserPlanResult]:
        """
        Run this plan, return users that triggered filter rules and action rules execution results.
        result explanation: (<user instance>, <filtering result>, <action results>)
        :return: rx.Observable(Tuple[ Tuple[User, RuleResult], List[RuleResult] ])
        """
        # take users that triggered filter rules
        target_users = self._filtering().pipe(op.filter(lambda z: bool(z[1]) is True))

        action_results = target_users.pipe(
            # log for debug
            op.do(
                rx.Observer(
                    on_next=lambda z: logger.debug("Plan[id={}]: User triggered filter rules: {}", self.id, z[0])
                )
            ),
            # extract user instance from tuple
            op.map(lambda z: z[0]),
            # apply actions on target users
            op.map(self.actions),
            # flat_map() is needed
            op.flat_map(lambda x: x),
            op.share(),
        )

        return rx.zip(target_users, action_results).pipe(
            # Convert results into a DTO instance
            op.map(
                lambda zipped: UserPlanResult(
                    plan_id=self.id, user=zipped[0][0], filtering_result=zipped[0][1], action_results=zipped[1]
                )
            )
        )

    def _filtering(self):
        """
        Pass source users to filter chain and combine filtering result with origin user instance.
        result explanation: (<user instance>, <filtering result>)
        :return: rx.Observable(Tuple[User, RuleResult])
        """
        users = self.sources().pipe(
            # log for debug
            op.do(rx.Observer(on_next=lambda u: logger.debug("Plan[id={}]: Distinct source user: {}", self.id, u))),
            # prevent repeat querying client to unnecessarily consuming additional API resource
            # https://stackoverflow.com/a/68482112/11397457
            op.share(),
        )
        filter_results = users.pipe(
            # execute filter rules on users
            op.map(self.filters),
            # flat_map() is needed because calling UserFilterRuleAnyOfSet will return Observable[RuleResult]
            op.flat_map(lambda x: x),
            op.share(),
        )
        return rx.zip(users, filter_results)
