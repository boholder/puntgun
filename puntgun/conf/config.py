"""All the loaded settings and global variables for many modules to use."""
from dynaconf import Dynaconf
from from_root import from_root

# where to find the config file:
# .../project-root/conf
config_dir_path = from_root('conf')
config_dir_str: str = str(config_dir_path.absolute())

# the dumped private key is stored in the config directory
pri_key_file_path = config_dir_path.joinpath('.puntgun_rsa4096')
pri_key_file_str = str(pri_key_file_path.absolute())

# encrypted secrets are stored into this file
secrets_config_file_path = config_dir_path.joinpath('.secrets.yml')

# tool settings on the "global" level
tool_config_files = [str(config_dir_path.joinpath('settings.yml').absolute()),
                     str(secrets_config_file_path.absolute())]

# environment variables' prefix
environment_variables_prefix = 'BULLET'

settings = Dynaconf(
    envvar_prefix=environment_variables_prefix,
    settings_files=tool_config_files,
    apply_default_on_none=True
)

# settings.configure(settings_files=static_config_files + ['conf/a.yml'])
# https://www.dynaconf.com/settings_files/#yaml-caveats
# https://loguru.readthedocs.io/en/stable/api/logger.html#loguru._logger.Logger.configure

# try:
#     print(settings.get('name'))
# except Exception as e:
#     print(e)
