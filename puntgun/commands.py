"""The implementation of commands"""
from __future__ import annotations

from pathlib import Path

from loguru import logger

from puntgun import runner, util
from puntgun.conf import config, encrypto, example, secret

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


def fire(args: dict[config.CommandArg, str]) -> None:
    logger.info("Run command [fire]")
    config.reload_important_files(args)
    # only config log files, stderr logs... in this command.
    config.config_logging_options()

    try:
        runner.start()
        runner.print_log_file_and_report_file_position()
    except KeyboardInterrupt:
        logger.bind(o=True).info("The tool is stopped by the keyboard.")
        exit(1)


def load_secrets_with_keyboard_interrupt_exit() -> dict[str, str]:
    try:
        return secret.load_or_request_all_secrets(encrypto.load_or_generate_private_key())
    except KeyboardInterrupt:
        logger.bind(o=True).info("The tool is stopped by the keyboard.")
        exit(1)


EXAMPLE_GENERATED = """Example configuration files generated:
settings: {example_settings_file}
plan: {example_plan_file}"""


class Gen:
    @staticmethod
    def secrets(args: dict[config.CommandArg, str]) -> None:
        config.reload_important_files(args)
        load_secrets_with_keyboard_interrupt_exit()

    @staticmethod
    def new_password(args: dict[config.CommandArg, str]) -> None:
        def get_new_password() -> str:
            new_pwd = ""
            two_pwd_are_not_same = True

            while two_pwd_are_not_same:
                print("Now enter a new password.")
                new_pwd = util.get_secret_from_terminal("New Password")
                print("Re-enter the password for confirm.")
                two_pwd_are_not_same = new_pwd != util.get_secret_from_terminal("Repeat Password")
                if two_pwd_are_not_same:
                    print("The two passwords are not same, start from the beginning.")

            return new_pwd

        config.reload_important_files(args)
        pri_key = encrypto.load_or_generate_private_key()

        new_password = get_new_password()
        encrypto.dump_private_key(pri_key, new_password, config.pri_key_file)
        print("Password change succeed, new private key file has been generated.")

    @staticmethod
    def plain_secrets(output_file: str, args: dict[config.CommandArg, str]) -> None:
        config.reload_important_files(args)

        print("Attention! This command will generate an unprotected plaintext secret value file.")
        print("Enter [secrets] to confirm that you are ready to protect it well on your own.")
        if util.get_input_from_terminal("Confirm") != "secrets":
            return

        secrets = load_secrets_with_keyboard_interrupt_exit()

        # this path will only be used here, so we needn't add it to config module.
        output_file_path = Path(output_file)
        util.backup_if_exists(output_file_path)
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.writelines(f"{key}: {value}\n" for key, value in secrets.items())

        print(f"Secrets are dumped: {output_file_path}")

    @staticmethod
    def config(output_path: str) -> None:
        example_settings_file = Path(output_path).joinpath("example-settings.yml")
        util.backup_if_exists(example_settings_file)
        with open(example_settings_file, "w", encoding="utf-8") as f:
            f.write(example.tool_settings)

        example_plan_file = Path(output_path).joinpath("example-plan.yml")
        util.backup_if_exists(example_plan_file)
        with open(example_plan_file, "w", encoding="utf-8") as f:
            f.write(example.plan_config)

        print(
            EXAMPLE_GENERATED.format(example_settings_file=example_settings_file, example_plan_file=example_plan_file)
        )


class Check:
    @staticmethod
    def plan(args: dict[config.CommandArg, str]) -> None:
        config.reload_important_files(args)
        runner.parse_plans_config(runner.get_and_validate_plan_config())
