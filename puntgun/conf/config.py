from dynaconf import Dynaconf
from from_root import from_root

# where to find the config file
config_dir_path = from_root('conf')
config_dir_str: str = str(config_dir_path.absolute())

tool_config_files = [config_dir_str + 'puntgun_settings.yml',
                     config_dir_str + '.secrets.yml']

settings = Dynaconf(
    envvar_prefix="PUNTGUN",
    settings_files=tool_config_files,
)

# settings.configure(settings_files=static_config_files + ['conf/a.yml'])
