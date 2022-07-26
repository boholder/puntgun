"""All the loaded settings and global variables for many modules to use."""
import sys
from importlib.metadata import version

from dynaconf import Dynaconf
from from_root import from_root
from loguru import logger

# For version based branch logic in report-based "undo" operation.
# (you have different available actions at different version,
# which may require different "undo" process.)
# Works sort of like java's serial version uid.
puntgun_version = version('puntgun')

# where to find the config file:
# .../<project-root>/conf
config_dir_path = from_root('conf')

# the dumped private key is stored in the config directory
pri_key_file_path = config_dir_path.joinpath('.puntgun_rsa4096')

# encrypted secrets are stored into this file
secrets_config_file_path = config_dir_path.joinpath('.secrets.yml')

settings = Dynaconf(
    # environment variables' prefix
    envvar_prefix='BULLET',
    # tool settings on the "global" level
    settings_files=[str(config_dir_path.joinpath('settings.yml')),
                    str(secrets_config_file_path)],
    apply_default_on_none=True
)

# settings.configure(settings_files=static_config_files + ['conf/a.yml'])
# https://www.dynaconf.com/settings_files/#yaml-caveats
# https://loguru.readthedocs.io/en/stable/api/logger.html#loguru._logger.Logger.configure


# report file logger sink,
# we're borrowing function of loguru logging library for writing an execution report file.
# See puntgun.record.Recorder for more info.
#
# Add this sink only when not in unit testing,
# or it will generate the file every time tests running, sort of annoying.
if "pytest" not in sys.modules:
    logger.add('record.json',
               filter=lambda record: 'r' in record['extra'],
               # only write the plain message content
               format='{message}')

# TODO 配置文件后面加后缀
# TODO 定义配置优先级（配置文件路径的指定）
# https://pydantic-docs.helpmanual.io/usage/settings/#changing-priority
