import runner
from conf import config
from conf.encrypto import load_or_generate_private_key
from conf.secret import load_or_request_all_secrets


class Gen(object):
    """Generate various files from the tool."""

    @staticmethod
    def secrets(secrets_file=str(config.secrets_file),
                output_file=str(config.secrets_plaintext_file)):
        """Extract secrets from secrets file and save them in plaintext format."""
        config.reload_config_files(secrets_file=secrets_file,
                                   secrets_plaintext_file=output_file)
        secrets = load_or_request_all_secrets(load_or_generate_private_key())
        with open(config.secrets_plaintext_file, 'w', encoding='utf-8') as f:
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
        config.reload_config_files(config_path=config_path,
                                   plan_file=plan_file,
                                   settings_file=settings_file,
                                   pri_key_file=private_key_file,
                                   secrets_file=secrets_file,
                                   report_file=report_file)
        runner.start()
