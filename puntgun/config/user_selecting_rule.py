
class UserSelectingRule:
    """
    Model, a mapping of same name configuration option.
    """

    def __init__(self, who, rule_set, let_me_check):
        self.who = who
        self.rule_set = rule_set
        self.let_me_check = let_me_check


class WhoField:
    """
    Represents the "who" field under #{UserSelectingRule}.
    """
    config_keyword = "who-field-generic"


class IdAreWhoField(WhoField):
    """
    "id-are" field
    """
    config_keyword = "id-are"

    def __init__(self, user_ids: list):
        self.user_ids = user_ids

    @staticmethod
    def from_config(value):
        assert isinstance(value, list), r'"id-are" field''s value must be a list'
        return IdAreWhoField(value)
