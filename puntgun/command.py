"""The implementation of commands"""
from pathlib import Path

from loguru import logger

from puntgun import runner
from puntgun import util
from puntgun.conf import config, example
from puntgun.conf import encrypto, secret

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


def fire(plan, report, settings, config_path, secrets, private_key):
    logger.info("Run command [fire]")
    config.reload_important_files(config_path=config_path,
                                  plan_file=plan,
                                  settings_file=settings,
                                  pri_key_file=private_key,
                                  secrets_file=secrets,
                                  report_file=report)
    # only config log files, stderr logs... in this command.
    config.config_logging_options()

    try:
        runner.start()
    except KeyboardInterrupt:
        logger.bind(o=True).info("The tool is stopped by the keyboard.")
        exit(1)


def load_secrets_with_keyboard_interrupt_exit():
    try:
        return secret.load_or_request_all_secrets(encrypto.load_or_generate_private_key())
    except KeyboardInterrupt:
        logger.bind(o=True).info("The tool is stopped by the keyboard.")
        exit(1)


EXAMPLE_GENERATED = """Example configuration files generated:
settings: {example_settings_file}
plan: {example_plan_file}"""


class Gen(object):
    @staticmethod
    def secrets(private_key_file, secrets_file):
        config.reload_important_files(secrets_file=secrets_file, pri_key_file=private_key_file)
        load_secrets_with_keyboard_interrupt_exit()

    @staticmethod
    def plain_secrets(output_file, private_key_file, secrets_file):
        config.reload_important_files(secrets_file=secrets_file, pri_key_file=private_key_file)
        secrets = load_secrets_with_keyboard_interrupt_exit()

        # this path will only be used here, so we needn't add it to config module.
        output_file = Path(output_file)
        util.backup_if_exists(output_file)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(f'{key}: {value}\n' for key, value in secrets.items())

        print(f"Secrets are dumped: {output_file}")

    @staticmethod
    def config(output_path):
        example_settings_file = Path(output_path).joinpath('example-settings.yml')
        util.backup_if_exists(example_settings_file)
        with open(example_settings_file, 'w', encoding='utf-8') as f:
            f.write(example.tool_settings)

        example_plan_file = Path(output_path).joinpath('example-plan.yml')
        util.backup_if_exists(example_plan_file)
        with open(example_plan_file, 'w', encoding='utf-8') as f:
            f.write(example.plan_config)

        print(EXAMPLE_GENERATED.format(example_settings_file=example_settings_file,
                                       example_plan_file=example_plan_file))


class Check(object):
    @staticmethod
    def plan(plan_file):
        config.reload_important_files(plan_file=plan_file)
        runner.parse_plans_config(runner.get_and_validate_plan_config())
