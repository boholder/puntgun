from dynaconf import Dynaconf

import conf.config


def print_loaded_settings_file():
    settings = Dynaconf(
        settings_files=[conf.config.config_path.joinpath('settings.yml')],
        apply_default_on_none=True
    )
    print(settings.get('s'))
