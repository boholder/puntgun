"""All the loaded settings and global variables for many modules to use."""
import sys
from datetime import datetime
from importlib.metadata import version

from dynaconf import Dynaconf
from from_root import from_root
from loguru import logger

# For version based branch logic in report-based "undo" operation.
# (you have different available actions at different version,
# which may require different "undo" process.)
# Works sort of like java's serial version uid.
puntgun_version = version('puntgun')

# TODO 这两个global配置文件应该变到用户目录下(的 .puntgun 目录)
# Path.home()
# sys.__stdin__.isatty()
config_dir_path = from_root('conf')

# the dumped private key is stored in the config directory
pri_key_file_path = config_dir_path.joinpath('.puntgun_rsa4096')

# encrypted secrets are stored into this file
secrets_config_file_path = config_dir_path.joinpath('.secrets.yml')

config_files = [config_dir_path.joinpath('settings.yml'),
                secrets_config_file_path]

settings = Dynaconf(
    # environment variables' prefix
    envvar_prefix='BULLET',
    settings_files=config_files,
    apply_default_on_none=True
)


def load_plan_configuration_file(path):
    # Dynaconf works in a layered override mode based on the above order,
    # the precedence will be based on the loading order.
    # *manually tested and searched: https://dynaconf.readthedocs.io/en/docs_223/guides/usage.html
    settings.configure(settings_files=[path] + config_files)


def log_file_naming(suffix: str):
    # loguru will follow given path to create log files.
    # so the log files will be generated under same directory with plan configuration file.
    # TODO 加上plan config路径
    plan_config_file = config_dir_path.joinpath('puntgun')
    time = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"{plan_config_file}_{time}_{suffix}"


# Configurate logging options only when not in unit testing,
# or it will generate files every time tests running, sort of annoying.
if "pytest" not in sys.modules:
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
    logger.add(log_file_naming('_running.log'),
               filter=lambda record: 'r' not in record['extra'],
               format=logger_format,
               rotation=settings.get('log_rotation', '100 MB'))

    # report file
    # we're borrowing function of loguru library for writing execution report files.
    # See puntgun.record.Recorder for more info.
    logger.add(log_file_naming('_report.json'),
               filter=lambda record: 'r' in record['extra'],
               # only write the plain message content
               format='{message}')
