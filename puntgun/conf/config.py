"""
All the loaded settings and global variables for many modules to use.

IMPROVE: Any proper way to unit test this module?
I feel it is too implement-coupling to be valuable enough writing test cases.
"""
import enum
import os
import sys
from datetime import datetime
from importlib import metadata
from pathlib import Path

# import dynaconf before loguru because loguru also uses dynaconf
# https://github.com/Delgan/loguru/issues/138#issuecomment-610476814
from dynaconf import Dynaconf
from loguru import logger

# I treat this tool as a... shortly running executable tool, not consistent running service,
# so it didn't need a fixed directory to store configuration files, executable, logs or so,
# just like other tools, use a configuration directory under the home directory.
config_path = Path.home().joinpath(".puntgun")

plan_file = config_path.joinpath("plan.yml")
settings_file = config_path.joinpath("settings.yml")
pri_key_file = config_path.joinpath(".puntgun_rsa4096")
secrets_file = config_path.joinpath(".secrets.yml")

# == log file and report file's path ==
# as: YYYYmmddHHMMSS
report_path = config_path.joinpath("reports")
log_path = config_path.joinpath("logs")

# a/b/c/plan.yml -> 'plan'
plan_file_name = os.path.basename(plan_file).split(".")[0]
log_time = datetime.now().strftime("%Y%m%d%H%M%S")

report_file = report_path.joinpath(f"{plan_file_name}_{log_time}_report.json")
log_file = log_path.joinpath(f"{plan_file_name}_{log_time}.log")

# generate required directories
if not config_path.exists():
    os.makedirs(config_path)
if not log_path.exists():
    os.makedirs(log_path)
if not report_path.exists():
    os.makedirs(report_path)

tool_version = metadata.version("puntgun")


def load_settings() -> Dynaconf:
    return Dynaconf(
        # environment variables' prefix
        envvar_prefix="BULLET",
        # Dynaconf works in a layered override mode based on the above order,
        # the precedence will be based on the loading order.
        # manually tested and searched:
        # https://dynaconf.readthedocs.io/en/docs_223/guides/usage.html
        settings_files=[plan_file, settings_file, secrets_file],
        apply_default_on_none=True,
    )


# Load configuration files with default config paths
settings = load_settings()


class CommandArg(enum.Enum):
    """How arguments are named in commands."""

    CONFIG_PATH = str(config_path)
    PLAN_FILE = str(plan_file)
    SETTINGS_FILE = str(settings_file)
    PRIVATE_KEY_FILE = str(pri_key_file)
    SECRETS_FILE = str(secrets_file)
    REPORT_FILE = str(report_file)

    def to_arg_str(self) -> str:
        return self.name.lower().replace("_", "-")

    def to_arg(self) -> str:
        return "--" + self.to_arg_str()

    @staticmethod
    def from_arg_str(arg: str) -> "CommandArg":
        return CommandArg[arg.upper().replace("-", "_")]

    @staticmethod
    def arg_dict_to_enum_dict(**kwargs: str) -> dict["CommandArg", str]:
        return {CommandArg.from_arg_str(k): v for k, v in kwargs.items()}


def reload_important_files(args: dict[CommandArg, str]) -> None:
    """
    Change file paths base on command arguments passed by user,
    and reload configuration from new files.
    """

    # IMPROVE: Ugly. But don't know how to improve it.
    global config_path
    global plan_file
    global settings_file
    global pri_key_file
    global secrets_file
    global report_file

    # after changing the config_path, other paths need to be re-computed to propagate change
    # it's how arguments paired with configurations.
    if a := args.get(CommandArg.CONFIG_PATH):
        config_path = Path(a)
    if a := args.get(CommandArg.PLAN_FILE):
        plan_file = Path(a)
    if a := args.get(CommandArg.SETTINGS_FILE):
        settings_file = Path(a)
    if a := args.get(CommandArg.PRIVATE_KEY_FILE):
        pri_key_file = Path(a)
    if a := args.get(CommandArg.SECRETS_FILE):
        secrets_file = Path(a)
    if a := args.get(CommandArg.REPORT_FILE):
        report_file = Path(a)

    # reload configuration files
    global settings
    settings = load_settings()


# source: https://github.com/Delgan/loguru/issues/586#issuecomment-1030819250
logger_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <5}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

# https://loguru.readthedocs.io/en/stable/api/logger.html#levels
log_level = settings.get("log_level", "INFO").upper()


def config_logging_options() -> None:
    # technical diagnostic logs go to stderr
    logger.add(
        sys.stderr,
        filter=lambda record: "r" not in record["extra"] and "o" not in record["extra"],
        format=logger_format,
        level=log_level,
    )

    # Only configurate log file and report file when running file command and isn't in unit testing.
    # loguru will follow given path to create log files.
    if "pytest" not in sys.modules:
        # report file
        # we're borrowing function of loguru library for writing execution report files.
        # use 'r' field to mark these logs.
        # See puntgun.record.Recorder for more info.
        logger.add(
            report_file,
            filter=lambda record: "r" in record["extra"],
            # only write the plain message content
            format="{message}",
            level=log_level,
        )

        # log file, saves all but record logs
        logger.add(
            log_file,
            filter=lambda record: "r" not in record["extra"],
            format=logger_format,
            # https://loguru.readthedocs.io/en/stable/api/logger.html#file
            rotation=settings.get("log_rotation", "100 MB"),
            level=log_level,
        )


# remove default logging sink (stderr)
logger.remove()
# reconfig logging options,
# logs that we want user see will show in stdout
logger.add(sys.stdout, filter=lambda record: "o" in record["extra"], format=logger_format, level=log_level)
