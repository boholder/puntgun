import fire

from conf import config

banner = r"""
     ____              _      ____
,___|____\____________|_|____/____|____________________
|___|_|_)_|_|_|_|_'__\|___|_|_|___|_|_|_|_'__\__[____]  ""-,___..--=====
    |  __/| |_| | | | | |_  | |_| | |_| | | | |   \\_____/   ""        |
    |_|    \__,_|_| |_|\__|  \____|\__,_|_| |_|      [ ))"---------..__|
puntgun - a configurable automation command line tool for Twitter
"""


class Command(object):
    @staticmethod
    def fire(config_path='', plan_file='', settings_file='', private_key_file='', secrets_file='',
             report_file=''):
        """Run a plan configuration.

        :param config_path: Path of various configuration files the tool needs.
        :param plan_file: Plan configuration file you'd like to execute.
        :param settings_file: Global tool settings that will apply to every execution.
        :param private_key_file: Tool generated password protected private key.
        :param secrets_file: Tool generated cipher text or user writen plain text file contains secrets.
        :param report_file: Expect path of the tool generated execution report.
        """
        config.reload_config_files_base_on_cmd_args(config_path, plan_file, settings_file,
                                                    private_key_file, secrets_file, report_file)


if __name__ == '__main__':
    # expose subcommands
    fire.Fire(Command)
