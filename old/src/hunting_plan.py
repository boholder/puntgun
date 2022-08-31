from typing import IO, Union

import yaml

import util


class HuntingPlan(object):
    """
    Parse configuration file content into rules, and hold them.
    """

    logger = util.get_logger(__qualname__)

    def __init__(self):
        self.raw_config = HuntingPlan.parse_yaml_config(self.read_config_file())

    @classmethod
    def parse_yaml_config(cls, config_file: Union[IO, str]) -> dict:
        try:
            return yaml.safe_load(config_file)
        except yaml.YAMLError as e:
            HuntingPlan.logger.error(f"Config parsing error occur, exiting...\n{e}")
            exit(1)

    @classmethod
    def read_config_file(cls) -> IO:
        file_name = util.get_input_from_terminal("Select file_name file (./option.yml)")
        if not file_name:
            file_name = "option.yml"

        try:
            return open(file_name, encoding="utf-8")
        except FileNotFoundError as e:
            HuntingPlan.logger.error("Config file not found, exiting...\n{}".format(e))
            exit(1)
        except IOError as e:
            HuntingPlan.logger.error("Failed reading file_name file, exiting...\n{}".format(e))
            exit(1)


if __name__ == "__main__":
    HuntingPlan()
