from dynaconf import Dynaconf
from from_root import from_here


def print_loaded_settings_file():
    settings = Dynaconf(
        settings_files=[from_here().joinpath('settings.yml')],
        apply_default_on_none=True
    )
    print(settings.get('s'))
