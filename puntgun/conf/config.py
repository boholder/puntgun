"""
All the loaded settings and global variables for many modules to use.
No unit tests guard (too implement-coupling to be valuable enough writing test cases), stay sharp.
"""
import sys
from datetime import datetime
from pathlib import Path

from dynaconf import Dynaconf
from loguru import logger

config_path = Path.home().joinpath('.puntgun')
plan_file = config_path.joinpath('plan.yml')
settings_file = config_path.joinpath('settings.yml')
pri_key_file = config_path.joinpath('.puntgun_rsa4096')
secrets_file = config_path.joinpath('.secrets.yml')


def naming_log_file(suffix: str):
    # YYYYMMDDHHMMSS
    time = datetime.now().strftime('%Y%m%d%H%M%S')
    # loguru will follow given path to create log files.
    # so the log files will be generated under same directory with plan configuration file.
    return f"{plan_file}_{time}_{suffix}"


report_file = naming_log_file('_report.json')

# Dynaconf works in a layered override mode based on the above order,
# the precedence will be based on the loading order.
# *manually tested and searched: https://dynaconf.readthedocs.io/en/docs_223/guides/usage.html
config_files_order = [plan_file, settings_file, secrets_file]

# load configuration files
settings = Dynaconf(
    # environment variables' prefix
    envvar_prefix='BULLET',
    settings_files=config_files_order,
    apply_default_on_none=True
)


def reload_config_files_base_on_cmd_args(_config_path, _plan_file, _settings_file,
                                         _private_key_file, _secrets_file, _report_file):
    # Ugly. But don't know how to improve it.
    global config_path
    global plan_file
    global settings_file
    global pri_key_file
    global secrets_file
    global report_file

    # after changing config_path, other paths need to be re-computed to propagate change
    config_path = Path(_config_path) if _config_path else Path.home().joinpath('.puntgun')
    plan_file = _plan_file if _plan_file else config_path.joinpath('plan.yml')
    settings_file = _settings_file if _settings_file else config_path.joinpath('settings.yml')
    pri_key_file = _private_key_file if _private_key_file else config_path.joinpath('.puntgun_rsa4096')
    secrets_file = _secrets_file if secrets_file else config_path.joinpath('.secrets.yml')
    report_file = _report_file if _report_file else naming_log_file('_report.json')

    # reload configuration files
    settings.configure(settings_files=config_files_order)


def config_logging_options():
    """
    Logs about current executing process to stdout will go with print(), not so much lines.
    """

    # remove default logging sink (stderr)
    logger.remove()

    # source: https://github.com/Delgan/loguru/issues/586#issuecomment-1030819250
    logger_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <5}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # console log
    logger.add(sys.stderr,
               filter=lambda record: 'r' not in record['extra'],
               format=logger_format)

    # log file
    logger.add(naming_log_file('_running.log'),
               filter=lambda record: 'r' not in record['extra'],
               format=logger_format,
               rotation=settings.get('log_rotation', '100 MB'))

    # report file
    # we're borrowing function of loguru library for writing execution report files.
    # See puntgun.record.Recorder for more info.
    logger.add(report_file,
               filter=lambda record: 'r' in record['extra'],
               # only write the plain message content
               format='{message}')


# Configurate logging options only when not in unit testing,
# or it will generate files every time tests running, sort of annoying.
if "pytest" not in sys.modules:
    config_logging_options()
