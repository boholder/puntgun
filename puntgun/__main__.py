import fire
from from_root import from_here

import runner
from conf import config
from conf.encrypto import load_or_generate_private_key
from conf.secret import load_or_request_all_secrets

banner = r"""
     ____              _      ____
,___|____\____________|_|____/____|____________________
|___|_|_)_|_|_|_|_'__\|___|_|_|___|_|_|_|_'__\__[____]  ""-,___..--=====
    |  __/| |_| | | | | |_  | |_| | |_| | | | |   \\_____/   ""        |
    |_|    \__,_|_| |_|\__|  \____|\__,_|_| |_|      [ ))"---------..__|
puntgun - a configurable automation command line tool for Twitter
"""


class Gen(object):
    """Generate various files from the tool."""

    @staticmethod
    def secrets(secrets_file=str(config.secrets_file), output_file=str(from_here())):
        """Extract secrets from secrets file and save them in plaintext format."""
        config.reload_config_files_base_on_cmd_args(secrets_file=secrets_file)
        secrets = load_or_request_all_secrets(load_or_generate_private_key())
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(f'{key}: {value}\n' for key, value in secrets.items())

    @staticmethod
    def example_config():
        """Generate example configuration files."""
        # https://stackoverflow.com/questions/53454049/how-to-include-a-text-file-in-a-python-installed-package
        print('config')


class Command(object):

    def __init__(self):
        self.gen = Gen()

    @staticmethod
    def fire(config_path=str(config.config_path),
             plan_file=str(config.plan_file),
             settings_file=str(config.settings_file),
             private_key_file=str(config.pri_key_file),
             secrets_file=str(config.secrets_file),
             report_file=str(config.report_file)):
        """
        Run a plan configuration.

        :param config_path: Path of various configuration files the tool needs.
        :param plan_file: Plan configuration file you'd like to execute.
        :param settings_file: Global tool settings that will apply to every execution.
        :param private_key_file: Tool generated password protected private key.
        :param secrets_file: Tool generated cipher text or user writen plain text file contains secrets.
        :param report_file: Expect path of the tool generated execution report.
        """
        config.reload_config_files_base_on_cmd_args(config_path=config_path,
                                                    plan_file=plan_file,
                                                    settings_file=settings_file,
                                                    private_key_file=private_key_file,
                                                    secrets_file=secrets_file,
                                                    report_file=report_file)
        runner.start()


if __name__ == '__main__':
    print(banner)
    fire.Fire(Command)
