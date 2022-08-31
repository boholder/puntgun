from unittest import TestCase

from old.test import HuntingPlan


class TestHuntingPlan(TestCase):
    def test_yaml_parser_should_correctly_parses_dict(self):
        yaml_string = """
map:
  list:
    - item1
    - item2
  another: text
        """
        parsed = HuntingPlan.parse_yaml_config(yaml_string)
        self.assertIsInstance(parsed.get("map"), dict)

    def test_yaml_parser_should_correctly_parses_list(self):
        yaml_string = """
          list:
            - item1:
                - inner: text
            - item2: text
            - item3:
                inner_field: text
        """
        parsed = HuntingPlan.parse_yaml_config(yaml_string)
        self.assertIsInstance(parsed.get("list"), list)
