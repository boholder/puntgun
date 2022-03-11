import yaml
from yaml.parser import ParserError

from puntgun.util import get_input


class HuntingPlan:
    """
    Parse config file into block rules,
    and determine if a block decision should be made
    by given user information.
    """

    def __init__(self):
        config = get_input("Select config file (./config-example.yml)")
        if not config:
            config = "config-example.yml"
        config = self.try_read_config_file(config)
        print(config)

    @staticmethod
    def try_read_config_file(config):
        try:
            config = yaml.safe_load(open(config, encoding='utf-8'))
        except FileNotFoundError as e:
            print("Config file not found, exiting...\n{}".format(e))
            exit(1)
        except IOError as e:
            print("Failed reading config file, exiting...\n{}".format(e))
            exit(1)
        except ParserError as e:
            print("Config parsing error occur, exiting...\n{}".format(e))
            exit(1)
        return config


class Rule:
    """
    Model, block rule.
    """


class Decision:
    """
    Model, context used to passing info between different rule filter chain.
    Including target user's information, and rules the user triggered.
    """


if __name__ == "__main__":
    HuntingPlan()
