"""All the loaded settings and global variables for many modules to use."""
from importlib.metadata import version

from dynaconf import Dynaconf
from from_root import from_root

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
