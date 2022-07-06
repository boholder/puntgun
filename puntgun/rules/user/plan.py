from typing import Optional, ClassVar, List

from reactivex import operators as op

from rules import FromConfig, ConfigParser, validate_required_fields_exist
from rules.user.action_rules import UserActionRule
from rules.user.filter_rules import UserFilterRule
from rules.user.rule_sets import UserSourceRuleAnyOfSet, UserFilterRuleAnyOfSet
from rules.user.source_rules import UserSourceRule


class UserPlan(FromConfig):
    """
    Represent a user_plan, user processing pipeline.
    """

    _keyword: ClassVar[str] = 'user_plan'
    name: str
    sources: UserSourceRuleAnyOfSet
    # TODO filter还没写完，要做到有默认的lambda。
    filters: Optional[UserFilterRuleAnyOfSet]
    actions: List[UserActionRule]

    @classmethod
    def parse_from_config(cls, conf: dict):
        # we won't directly extract values from configuration and assign them to fields,
        # so custom validation is needed.
        validate_required_fields_exist(cls._keyword, conf, ['from', 'do'])

        return cls(name=conf['user_plan'],
                   # wrap source rules with any_of rule set
                   sources=ConfigParser.parse({'any_of': conf['from']}, UserSourceRule),
                   # wrap with any_of
                   filters=ConfigParser.parse({'any_of': conf['that']}, UserFilterRule),
                   actions=[ConfigParser.parse(c, UserActionRule) for c in conf['do']])

    def __call__(self):
        # TODO 还没实现运行呢

        self.sources().pipe(op.filter(self.filters))
