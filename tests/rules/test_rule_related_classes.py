from typing import Optional

from rules import Rule, ConfigParser


class TestRuleType:
    pass


class TestRule(Rule, TestRuleType):
    keyword: Optional[str] = 'f'
    f: str


class TestConfigParserWithRuleBaseClass:

    def test_config_parsing_success(self):
        obj = ConfigParser.parse({'f': 'text'}, TestRuleType)
        assert obj.f == 'text'
