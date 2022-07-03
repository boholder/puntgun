from typing import Optional, ClassVar

from rules import FromConfig, ConfigParser
from rules.user.action_rules import UserActionRule
from rules.user.filter_rules import UserFilterRule
from rules.user.source_rules import UserSourceRule


class UserPlan(FromConfig):
    """
    Represent a user_plan, user processing pipeline.
    """

    _keyword: ClassVar[str] = 'user_plan'
    name: str
    sources: [UserSourceRule]
    filters: Optional[UserFilterRule]
    actions: [UserActionRule]

    @classmethod
    def parse_from_config(cls, conf: dict):
        return cls(name=conf['user_plan'],
                   sources=[ConfigParser.parse(c, UserSourceRule) for c in conf['from']],
                   filters=[ConfigParser.parse(c, UserFilterRule) for c in conf['that']],
                   actions=[ConfigParser.parse(c, UserActionRule) for c in conf['do']])
