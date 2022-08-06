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


report_file = naming_log_file('report.json')

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


def reload_config_files_base_on_cmd_args(**kwargs):
    # Ugly. But don't know how to improve it.
    global config_path
    global plan_file
    global settings_file
    global pri_key_file
    global secrets_file
    global report_file

    # after changing config_path, other paths need to be re-computed to propagate change
    if kwargs.get('config_path'):
        config_path = Path(kwargs.get('config_path'))
    if kwargs.get('plan_file'):
        plan_file = Path(kwargs.get('plan_file'))
    if kwargs.get('settings_file'):
        settings_file = Path(kwargs.get('settings_file'))
    if kwargs.get('private_key_file'):
        pri_key_file = Path(kwargs.get('private_key_file'))
    if kwargs.get('secrets_file'):
        secrets_file = Path(kwargs.get('secrets_file'))
    if kwargs.get('report_file'):
        report_file = Path(kwargs.get('report_file'))

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

    # report file
    # we're borrowing function of loguru library for writing execution report files.
    # use 'r' field to mark these logs.
    # See puntgun.record.Recorder for more info.
    logger.add(report_file,
               filter=lambda record: 'r' in record['extra'],
               # only write the plain message content
               format='{message}')

    # logs that we want user see will show in stdout
    logger.add(sys.stdout,
               filter=lambda record: 'o' in record['extra'],
               format=logger_format)

    # technical diagnostic logs go to stderr
    logger.add(sys.stderr,
               filter=lambda record: 'r' not in record['extra'] and 'o' not in record['extra'],
               format=logger_format)

    # log file, saves all but record logs
    logger.add(naming_log_file('running.log'),
               filter=lambda record: 'r' not in record['extra'],
               format=logger_format,
               # https://loguru.readthedocs.io/en/stable/api/logger.html#file
               rotation=settings.get('log_rotation', '100 MB'))


# Configurate logging options only when not in unit testing,
# or it will generate files every time tests running, sort of annoying.
if "pytest" not in sys.modules:
    config_logging_options()
